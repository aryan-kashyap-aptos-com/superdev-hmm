#!/usr/bin/env python3
"""OMS Engine — shared Toro / IIS operations console."""

from __future__ import annotations

import base64
import json
import os
import queue
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
import tkinter as tk
from typing import Any, Callable

from cloudwatch_logs import list_shoplogic_api_log_groups, preload_log_groups_background, tail_log_group
from display_utils import (
    format_file_size,
    format_remote_timestamp,
    format_service_status,
    format_start_type,
    iis_row_tag,
    status_tag,
)
from env_detection import classify_iis_site, classify_toro_service, detection_rules_markdown
from inventory_io import INVENTORY_PATH, load_inventory, refresh_from_aws
from path_candidates import content_server_path_from_unc, shoplogic_path_candidates
from sftp_client import SftpSession, resolve_credentials
from sftp_paths import sftp_path_for_iis_site
from ssm_runner import (
    PS_HOST_META,
    PS_LIST_IIS,
    PS_LIST_OMS_SERVICES,
    ps_app_pool_state,
    ps_file_length,
    ps_iis_recycle_pool,
    ps_iis_site_action,
    ps_list_directory,
    ps_read_file_base64,
    ps_read_file_chunk_base64,
    ps_tail_text_file,
    ps_service_action,
    ps_service_status,
    ps_tail_shoplogic_debug_bases,
    ps_tail_toro_logs,
    ps_website_state,
    run_powershell,
    ssm_failed_message,
    ssm_ping_status,
)
from theme import DARK, LIGHT, Palette
from ui_helpers import ToolTip, show_error_dialog


def ensure_ssm_ok(result: dict[str, str]) -> None:
    if result.get("status") != "Success":
        raise RuntimeError(ssm_failed_message(result))

SSM_CHUNK_BYTES = 1_048_576
SSM_INLINE_MAX = 8_388_608
DIR_CACHE_TTL_SECONDS = 45


def _parse_list_directory_payload(raw: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    text = (raw or "").strip()
    if not text:
        return {}, []
    data = json.loads(text)
    if isinstance(data, dict) and "Items" in data:
        items = data.get("Items") or []
        if isinstance(items, dict):
            items = [items]
        return dict(data.get("Server") or {}), list(items)
    rows = _parse_json_rows(text)
    return {}, rows


def _parse_json_rows(raw: str) -> list[dict[str, Any]]:
    text = (raw or "").strip()
    if not text:
        return []
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


class OmsEngineApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("OMS Engine")
        self.geometry("1280x820")
        self.minsize(1024, 680)

        self._palette: Palette = DARK
        self._dark = True
        self._work_q: queue.Queue[tuple[Callable[..., None], tuple]] = queue.Queue()
        self._executor = ThreadPoolExecutor(max_workers=6)
        self._region, self._stacks = load_inventory()
        self._stack_var = tk.StringVar()
        self._toro_filter = tk.StringVar()
        self._iis_filter = tk.StringVar()
        self._iis_seg = tk.StringVar(value="all")
        self._live_sync = tk.BooleanVar(value=False)
        self._host_ssm: dict[str, str] = {}
        self._host_serial: dict[str, str] = {}
        self._iis_sites: list[dict[str, Any]] = []
        self._iis_pools: dict[str, str] = {}
        self._toro_rows: list[dict[str, Any]] = []
        self._cw_groups: list[str] = []
        self._file_path = tk.StringVar(value=r"D:\content\dev")
        self._file_host_role = tk.StringVar(value="content")
        self._live_after_id: str | None = None
        self._host_cards: list[tk.Frame] = []
        self._sftp = SftpSession("")
        self._sftp_path = tk.StringVar(value="/dev")
        self._sftp_cred_user: str | None = None
        self._sftp_cred_pass: str | None = None
        self._xfer_visible = False
        self._busy_jobs = 0
        self._dir_cache: dict[tuple[str, str], tuple[float, dict[str, Any], list[dict[str, Any]]]] = {}

        self._setup_styles()
        self._build_ui()
        self._apply_theme()
        if self._stacks:
            self._stack_var.set(self._stacks[0].label)
        self.after(100, self._refresh_all)
        self._cw_group_var.set("Loading CloudWatch groups...")
        preload_log_groups_background(self._on_cw_groups_preloaded)
        self.bind("<r>", lambda e: self._refresh_all())
        self.bind("<R>", lambda e: self._refresh_all())

    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        self._apply_theme()

    def _apply_theme(self) -> None:
        p = self._palette
        self.configure(bg=p.bg)
        style = ttk.Style()
        style.configure(".", background=p.bg, foreground=p.ink, font=(p.ui, 10))
        style.configure("TFrame", background=p.bg)
        style.configure("Panel.TFrame", background=p.panel)
        style.configure("TLabel", background=p.bg, foreground=p.ink)
        style.configure("Panel.TLabel", background=p.panel, foreground=p.ink)
        style.configure("Muted.TLabel", background=p.bg, foreground=p.ink_muted, font=(p.ui, 9))
        style.configure("SideMuted.TLabel", background=p.panel, foreground=p.ink_muted, font=(p.mono, 9))
        style.configure("TButton", padding=(10, 7))
        style.configure("Accent.TButton", background=p.teal, foreground="#062421")
        style.map("Accent.TButton", background=[("active", p.teal)])
        style.configure("TNotebook", background=p.bg, borderwidth=0, tabmargins=(4, 4, 0, 0))
        style.configure(
            "TNotebook.Tab",
            padding=(16, 10),
            font=(p.ui, 10, "bold"),
            background=p.sub,
            foreground=p.ink_muted,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", p.panel), ("active", p.hover)],
            foreground=[("selected", p.ink), ("active", p.ink)],
        )
        style.configure("Treeview", background=p.panel, fieldbackground=p.panel, foreground=p.ink, rowheight=32, borderwidth=0)
        style.configure("Treeview.Heading", font=(p.ui, 9, "bold"), foreground=p.ink_muted, background=p.sub, relief=tk.FLAT)
        style.map("Treeview.Heading", background=[("active", p.hover)])
        style.configure("TLabelframe", background=p.bg)
        style.configure("TLabelframe.Label", background=p.bg, foreground=p.ink_muted, font=(p.ui, 9, "bold"))
        style.configure("TEntry", fieldbackground=p.sub, foreground=p.ink, insertcolor=p.ink)
        style.configure("TCombobox", fieldbackground=p.sub, background=p.panel, foreground=p.ink, arrowsize=14)
        style.map("TCombobox", fieldbackground=[("readonly", p.sub)])
        style.configure("TRadiobutton", background=p.bg, foreground=p.ink)
        style.configure("Horizontal.TProgressbar", troughcolor=p.line, background=p.teal)

        for tree in (
            getattr(self, "_toro_tree", None),
            getattr(self, "_iis_tree", None),
            getattr(self, "_file_tree", None),
            getattr(self, "_sftp_tree", None),
        ):
            if tree is None:
                continue
            tree.tag_configure("Running", foreground=p.green)
            tree.tag_configure("Stopped", foreground=p.red)
            tree.tag_configure("Pending", foreground=p.amber)
            tree.tag_configure("IISStarted", foreground=p.green)
            tree.tag_configure("IISStopped", foreground=p.red)
            tree.tag_configure("IISPending", foreground=p.amber)
            tree.tag_configure("IISNeutral", foreground=p.ink_muted)
            tree.tag_configure("transition", background=p.amber_soft)
            tree.tag_configure("stripe", background=p.sub)

        if hasattr(self, "_title_bar"):
            self._title_bar.configure(bg=p.navy)
        if hasattr(self, "_brand_label"):
            self._brand_label.configure(bg=p.navy, fg="#ffffff")
        if hasattr(self, "_brand_sub"):
            self._brand_sub.configure(bg=p.navy, fg="#9fb0c8")
        if hasattr(self, "_side"):
            self._side.configure(bg=p.panel)
        if hasattr(self, "_summary_card"):
            self._summary_card.configure(bg=p.sub, highlightbackground=p.line)
        for lbl in (getattr(self, "_sum_svc", None), getattr(self, "_sum_iis", None), getattr(self, "_sum_env", None)):
            if lbl is not None:
                lbl.configure(bg=p.sub, fg=p.ink)
        if hasattr(self, "_file_server_label"):
            self._file_server_label.configure(bg=p.panel, fg=p.ink_muted)
        if hasattr(self, "_activity"):
            self._activity.configure(bg=p.sub, fg=p.ink, insertbackground=p.ink, relief=tk.FLAT, padx=8, pady=6)
            self._activity.tag_configure("ok", foreground=p.green)
            self._activity.tag_configure("err", foreground=p.red)
            self._activity.tag_configure("run", foreground=p.amber)
            self._activity.tag_configure("inf", foreground=p.blue)
            self._activity.tag_configure("ts", foreground=p.ink_muted)

    def _toggle_theme(self) -> None:
        self._dark = not self._dark
        self._palette = DARK if self._dark else LIGHT
        self._apply_theme()

    def _title_btn(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        accent: bool = False,
        toggle: bool = False,
    ) -> tk.Widget:
        p = self._palette
        if toggle:
            return tk.Checkbutton(
                parent,
                text=text,
                variable=self._live_sync,
                command=command,
                bg=p.navy,
                fg="#c9d4e4",
                selectcolor=p.navy_2,
                activebackground=p.navy_2,
                activeforeground="#ffffff",
                font=(p.ui, 9),
                indicatoron=False,
                padx=10,
                pady=5,
                relief=tk.FLAT,
                borderwidth=0,
                highlightthickness=0,
            )
        bg = p.teal if accent else p.navy_2
        fg = "#062421" if accent else "#e6ecf5"
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=p.teal if accent else "#1a2a42",
            activeforeground=fg,
            relief=tk.FLAT,
            font=(p.ui, 9, "bold" if accent else "normal"),
            padx=12,
            pady=5,
            cursor="hand2",
            borderwidth=0,
            highlightthickness=0,
        )

    def _toggle_live_sync(self) -> None:
        self._on_live_toggle()

    def _current_stack(self):
        label = self._stack_var.get()
        for s in self._stacks:
            if s.label == label:
                return s
        return self._stacks[0] if self._stacks else None

    def _select_notebook_tab(self, prefix: str) -> None:
        for i, tab_id in enumerate(self._notebook.tabs()):
            if self._notebook.tab(tab_id, "text").startswith(prefix):
                self._notebook.select(i)
                return

    def _build_ui(self) -> None:
        p = self._palette
        self._title_bar = tk.Frame(self, bg=p.navy, height=52)
        self._title_bar.pack(fill=tk.X)
        self._title_bar.pack_propagate(False)

        brand = tk.Frame(self._title_bar, bg=p.navy)
        brand.pack(side=tk.LEFT, padx=(14, 16))
        self._brand_label = tk.Label(brand, text="OMS Engine", bg=p.navy, fg="#fff", font=(p.ui, 14, "bold"))
        self._brand_label.pack(anchor=tk.W)
        self._brand_sub = tk.Label(brand, text="SHARED OPERATIONS", bg=p.navy, fg="#9fb0c8", font=(p.ui, 8))
        self._brand_sub.pack(anchor=tk.W)

        stack_frame = tk.Frame(self._title_bar, bg=p.navy_2, highlightbackground="#2a3b57", highlightthickness=1)
        stack_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=10)
        tk.Label(stack_frame, text="STACK", bg=p.navy_2, fg="#9fb0c8", font=(p.ui, 8, "bold")).pack(side=tk.LEFT, padx=(10, 6))
        stack_combo = ttk.Combobox(
            stack_frame,
            textvariable=self._stack_var,
            values=[s.label for s in self._stacks],
            state="readonly",
            width=52,
        )
        stack_combo.pack(side=tk.LEFT, padx=(0, 10), pady=6)
        stack_combo.bind("<<ComboboxSelected>>", lambda _: self._refresh_all())
        self._hosts_pill = tk.Label(stack_frame, text="— hosts", bg=p.navy_2, fg=p.teal, font=(p.mono, 9))
        self._hosts_pill.pack(side=tk.LEFT, padx=8)

        tb_right = tk.Frame(self._title_bar, bg=p.navy)
        tb_right.pack(side=tk.RIGHT, padx=12)
        self._live_btn = self._title_btn(tb_right, "Live sync", self._toggle_live_sync, toggle=True)
        self._live_btn.pack(side=tk.LEFT, padx=4)
        self._title_btn(tb_right, "Theme", self._toggle_theme).pack(side=tk.LEFT, padx=3)
        self._title_btn(tb_right, "Detection", self._show_detection_rules).pack(side=tk.LEFT, padx=3)
        self._title_btn(tb_right, "Refresh", self._refresh_all, accent=True).pack(side=tk.LEFT, padx=3)
        self._title_btn(tb_right, "EC2 IDs", self._refresh_inventory).pack(side=tk.LEFT, padx=3)

        self._body_paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self._body_paned.pack(fill=tk.BOTH, expand=True)

        self._side = tk.Frame(self._body_paned, bg=p.panel, width=280)
        self._body_paned.add(self._side, weight=0)
        tk.Label(self._side, text="HOSTS", bg=p.panel, fg=p.ink_muted, font=(p.ui, 9, "bold")).pack(
            anchor=tk.W, padx=14, pady=(14, 6)
        )
        self._host_list = tk.Frame(self._side, bg=p.panel)
        self._host_list.pack(fill=tk.X)

        self._summary_card = tk.Frame(self._side, bg=p.sub, highlightbackground=p.line, highlightthickness=1)
        self._summary_card.pack(fill=tk.X, padx=12, pady=12)
        tk.Label(
            self._summary_card, text="STACK HEALTH", bg=p.sub, fg=p.ink_muted, font=(p.ui, 8, "bold")
        ).pack(anchor=tk.W, padx=12, pady=(10, 6))
        self._sum_svc = tk.Label(self._summary_card, text="Services —", bg=p.sub, fg=p.ink, font=(p.ui, 10))
        self._sum_svc.pack(anchor=tk.W, padx=12, pady=2)
        self._sum_iis = tk.Label(self._summary_card, text="IIS sites —", bg=p.sub, fg=p.ink, font=(p.ui, 10))
        self._sum_iis.pack(anchor=tk.W, padx=12, pady=2)
        self._sum_env = tk.Label(self._summary_card, text="Environments —", bg=p.sub, fg=p.ink, font=(p.ui, 10))
        self._sum_env.pack(anchor=tk.W, padx=12, pady=2)
        self._health_bar = tk.Canvas(self._summary_card, height=8, bg=p.line, highlightthickness=0)
        self._health_bar.pack(fill=tk.X, padx=12, pady=(8, 12))
        self._last_refresh = tk.Label(
            self._side, text="Not refreshed yet", bg=p.panel, fg=p.ink_muted, font=(p.mono, 8), wraplength=220
        )
        self._last_refresh.pack(side=tk.BOTTOM, anchor=tk.W, padx=14, pady=12)

        main = ttk.Frame(self._body_paned, style="Panel.TFrame")
        self._body_paned.add(main, weight=1)
        self.after(200, lambda: self._body_paned.sashpos(0, 280))

        notebook = ttk.Notebook(main)
        notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self._notebook = notebook

        toro_tab = ttk.Frame(notebook, padding=(12, 8))
        notebook.add(toro_tab, text="Toronado")
        self._build_toro_tab(toro_tab)

        iis_tab = ttk.Frame(notebook, padding=(12, 8))
        notebook.add(iis_tab, text="Site Manager (IIS)")
        self._build_iis_tab(iis_tab)

        logs_tab = ttk.Frame(notebook, padding=(12, 8))
        notebook.add(logs_tab, text="Logs")
        self._build_logs_tab(logs_tab)

        files_tab = ttk.Frame(notebook, padding=(12, 8))
        notebook.add(files_tab, text="Files")
        self._build_files_tab(files_tab)

        sftp_tab = ttk.Frame(notebook, padding=(12, 8))
        notebook.add(sftp_tab, text="SFTP")
        self._build_sftp_tab(sftp_tab)

        dock = ttk.Frame(self, padding=(0, 0))
        dock.pack(fill=tk.X)
        act_frame = ttk.LabelFrame(dock, text="Activity stream", padding=8)
        act_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        self._activity = tk.Text(act_frame, height=4, wrap=tk.WORD, font=(p.mono, 9), relief=tk.FLAT)
        self._activity.pack(fill=tk.X)

        self._status = ttk.Label(self, text=f"Region {self._region} · {INVENTORY_PATH.name}", anchor=tk.W, padding=(12, 4))
        self._status.pack(fill=tk.X)
        self._build_transfer_bar()

    def _build_toro_tab(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Filter").pack(side=tk.LEFT)
        ent = ttk.Entry(row, textvariable=self._toro_filter, width=40)
        ent.pack(side=tk.LEFT, padx=8)
        ent.bind("<KeyRelease>", lambda _: self._render_toro_tree())
        for label, action in [("Start", "start"), ("Stop", "stop"), ("Restart", "restart")]:
            ttk.Button(row, text=label, command=lambda a=action: self._service_action(a)).pack(side=tk.RIGHT, padx=3)

        cols = ("name", "environment", "status", "start_type")
        self._toro_tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        self._toro_tree.heading("name", text="Service")
        self._toro_tree.heading("environment", text="Environment")
        self._toro_tree.heading("status", text="Status")
        self._toro_tree.heading("start_type", text="Startup")
        self._toro_tree.column("name", width=420)
        self._toro_tree.column("environment", width=180)
        self._toro_tree.column("status", width=120)
        self._toro_tree.column("start_type", width=100)
        self._toro_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

    def _build_iis_tab(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Filter sites").pack(side=tk.LEFT)
        ent = ttk.Entry(row, textvariable=self._iis_filter, width=36)
        ent.pack(side=tk.LEFT, padx=8)
        ent.bind("<KeyRelease>", lambda _: self._render_iis_tree())
        seg = ttk.Frame(row)
        seg.pack(side=tk.LEFT, padx=12)
        for val, label in [("all", "All"), ("started", "Started"), ("stopped", "Stopped"), ("oms", "OMS only")]:
            ttk.Radiobutton(seg, text=label, value=val, variable=self._iis_seg, command=self._render_iis_tree).pack(
                side=tk.LEFT, padx=4
            )
        for label, action in [
            ("Recycle pool", None),
            ("Start", "start"),
            ("Stop", "stop"),
            ("Restart", "restart"),
        ]:
            cmd = self._iis_recycle_pool if action is None else (lambda a=action: self._iis_site(a))
            ttk.Button(row, text=label, command=cmd).pack(side=tk.RIGHT, padx=3)

        iis_cols = ("site", "environment", "site_state", "app_pool", "pool_state", "physical_path")
        self._iis_tree = ttk.Treeview(parent, columns=iis_cols, show="headings", height=18)
        labels = ("Site", "Environment", "Site", "App pool", "Pool", "Physical path")
        for col, text in zip(iis_cols, labels):
            self._iis_tree.heading(col, text=text)
        self._iis_tree.column("site", width=180)
        self._iis_tree.column("environment", width=140)
        self._iis_tree.column("site_state", width=90)
        self._iis_tree.column("app_pool", width=160)
        self._iis_tree.column("pool_state", width=80)
        self._iis_tree.column("physical_path", width=320)
        self._iis_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

    def _build_logs_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="Tail opens in a separate window so Toro / IIS tables keep the screen.",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(0, 10))

        sm_row = ttk.LabelFrame(parent, text="Site Manager — ShopLogic", padding=10)
        sm_row.pack(fill=tk.X, pady=(0, 8))
        self._log_site_var = tk.StringVar()
        r1 = ttk.Frame(sm_row)
        r1.pack(fill=tk.X)
        ttk.Label(r1, text="IIS site").pack(side=tk.LEFT)
        self._log_site_combo = ttk.Combobox(r1, textvariable=self._log_site_var, width=52, state="readonly")
        self._log_site_combo.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        ttk.Button(r1, text="Tail ShopLogic log", command=self._tail_sm_log).pack(side=tk.RIGHT)

        toro_row = ttk.LabelFrame(parent, text="Toronado", padding=10)
        toro_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(toro_row, text="Uses the service selected on the Toronado tab.", style="Muted.TLabel").pack(
            anchor=tk.W, pady=(0, 6)
        )
        ttk.Button(toro_row, text="Tail latest .log", command=self._tail_toro_log).pack(anchor=tk.W)

        api_row = ttk.LabelFrame(parent, text="API — CloudWatch", padding=10)
        api_row.pack(fill=tk.X)
        self._cw_group_var = tk.StringVar()
        r3 = ttk.Frame(api_row)
        r3.pack(fill=tk.X)
        ttk.Button(r3, text="Refresh groups", command=self._refresh_cw_groups).pack(side=tk.LEFT)
        self._cw_combo = ttk.Combobox(r3, textvariable=self._cw_group_var, width=58, state="readonly")
        self._cw_combo.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        ttk.Button(r3, text="Tail events", command=self._tail_cw_log).pack(side=tk.RIGHT)

    def _build_files_tab(self, parent: ttk.Frame) -> None:
        p = self._palette
        ttk.Label(
            parent,
            text="Browse site files on the content or Site Manager host. Double-click folders; double-click files to preview.",
            style="Muted.TLabel",
            wraplength=900,
        ).pack(anchor=tk.W)
        self._file_server_label = tk.Label(
            parent,
            text="Server time: — (open a folder to load)",
            bg=p.panel,
            fg=p.ink_muted,
            font=(p.mono, 9),
            anchor=tk.W,
        )
        self._file_server_label.pack(fill=tk.X, pady=(6, 0))

        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X, pady=8)
        ttk.Label(bar, text="Host").pack(side=tk.LEFT)
        host_cb = ttk.Combobox(
            bar,
            textvariable=self._file_host_role,
            values=("content", "sitemanager", "toronado"),
            state="readonly",
            width=14,
        )
        host_cb.pack(side=tk.LEFT, padx=6)
        host_cb.bind("<<ComboboxSelected>>", lambda _: self._dir_cache.clear())
        ttk.Label(bar, text="Path").pack(side=tk.LEFT, padx=(12, 0))
        ttk.Entry(bar, textvariable=self._file_path, width=64).pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        ttk.Button(bar, text="Open", command=lambda: self._file_list_dir(force=True)).pack(side=tk.LEFT, padx=3)
        ttk.Button(bar, text="Up", command=self._file_go_up).pack(side=tk.LEFT, padx=3)
        ttk.Button(bar, text="Site path", command=self._file_use_site_path).pack(side=tk.LEFT, padx=3)
        ttk.Button(bar, text="View / tail", command=self._file_view).pack(side=tk.RIGHT, padx=3)
        ttk.Button(bar, text="Open on PC", command=self._file_open_locally).pack(side=tk.RIGHT, padx=3)
        ttk.Button(bar, text="Download", command=self._file_download).pack(side=tk.RIGHT, padx=3)

        fcols = ("name", "kind", "size", "modified", "nbytes")
        self._file_tree = ttk.Treeview(parent, columns=fcols, show="headings", height=20)
        self._file_tree.heading("name", text="Name")
        self._file_tree.heading("kind", text="Type")
        self._file_tree.heading("size", text="Size")
        self._file_tree.heading("modified", text="Modified (server)")
        self._file_tree.heading("nbytes", text="")
        self._file_tree.column("name", width=340)
        self._file_tree.column("kind", width=72)
        self._file_tree.column("size", width=88)
        self._file_tree.column("modified", width=140)
        self._file_tree.column("nbytes", width=0, stretch=False)
        self._file_tree.pack(fill=tk.BOTH, expand=True)
        self._file_tree.bind("<Double-1>", self._file_on_double_click)
        self._file_last_listed_path: str | None = None

    def _build_sftp_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="SFTP mirror for large archives (ShopLogic / task logs). Credentials from .env or Connect.",
            style="Muted.TLabel",
            wraplength=900,
        ).pack(anchor=tk.W)
        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X, pady=8)
        self._sftp_status = ttk.Label(bar, text="Not connected", style="Muted.TLabel")
        self._sftp_status.pack(side=tk.LEFT)
        ttk.Button(bar, text="Connect SFTP", command=self._sftp_connect).pack(side=tk.LEFT, padx=8)
        ttk.Button(bar, text="Disconnect", command=self._sftp_disconnect).pack(side=tk.LEFT, padx=3)
        ttk.Button(bar, text="SM path from IIS site", command=self._sftp_use_site_path).pack(side=tk.LEFT, padx=12)
        ttk.Button(bar, text="/dev/", command=lambda: self._sftp_goto("/dev")).pack(side=tk.LEFT)
        ttk.Button(bar, text="/task/", command=lambda: self._sftp_goto("/task")).pack(side=tk.LEFT, padx=4)

        path_row = ttk.Frame(parent)
        path_row.pack(fill=tk.X, pady=4)
        ttk.Label(path_row, text="Remote path").pack(side=tk.LEFT)
        ttk.Entry(path_row, textvariable=self._sftp_path, width=72).pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        ttk.Button(path_row, text="List", command=self._sftp_list_dir).pack(side=tk.LEFT, padx=3)
        ttk.Button(path_row, text="Up", command=self._sftp_go_up).pack(side=tk.LEFT)
        ttk.Button(path_row, text="Download", command=self._sftp_download).pack(side=tk.RIGHT, padx=3)

        scols = ("name", "kind", "size", "mtime")
        self._sftp_tree = ttk.Treeview(parent, columns=scols, show="headings", height=16)
        for col, label in zip(scols, ("Name", "Type", "Size", "Modified")):
            self._sftp_tree.heading(col, text=label)
        self._sftp_tree.column("name", width=360)
        self._sftp_tree.column("kind", width=80)
        self._sftp_tree.column("size", width=100)
        self._sftp_tree.column("mtime", width=160)
        self._sftp_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self._sftp_tree.bind("<Double-1>", self._sftp_on_double_click)

    def _build_transfer_bar(self) -> None:
        self._xfer_frame = ttk.Frame(self, padding=(12, 4))
        self._xfer_label = ttk.Label(self._xfer_frame, text="")
        self._xfer_label.pack(side=tk.LEFT, padx=(0, 12))
        self._xfer_bar = ttk.Progressbar(self._xfer_frame, mode="determinate", length=420)
        self._xfer_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _show_transfer(self, label: str, total: int | None = None) -> None:
        self._xfer_label.config(text=label)
        if total and total > 0:
            self._xfer_bar.configure(mode="determinate", maximum=total, value=0)
        else:
            self._xfer_bar.configure(mode="indeterminate")
            self._xfer_bar.start(12)
        if not self._xfer_visible:
            self._xfer_frame.pack(fill=tk.X, before=self._status)
            self._xfer_visible = True

    def _update_transfer(self, done: int, total: int, suffix: str = "") -> None:
        if self._xfer_bar["mode"] == "determinate":
            self._xfer_bar["value"] = done
        text = f"{done:,} / {total:,} bytes" if total else f"{done:,} bytes"
        if suffix:
            text = f"{suffix} — {text}"
        self._xfer_label.config(text=text)

    def _hide_transfer(self) -> None:
        if self._xfer_bar["mode"] == "indeterminate":
            self._xfer_bar.stop()
        if self._xfer_visible:
            self._xfer_frame.pack_forget()
            self._xfer_visible = False

    def _show_detection_rules(self) -> None:
        win = tk.Toplevel(self)
        win.title("OMS environment detection")
        win.geometry("520x480")
        text = scrolledtext.ScrolledText(win, font=("Consolas", 10), wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, detection_rules_markdown())
        text.configure(state=tk.DISABLED)

    def _activity_line(self, level: str, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        tag = {"OK": "ok", "ERR": "err", "RUN": "run", "WARN": "run", "INF": "inf"}.get(level.upper(), "inf")
        self._activity.insert(tk.END, f"{ts}  ", ("ts",))
        self._activity.insert(tk.END, f"{level:<4}  ", (tag,))
        self._activity.insert(tk.END, f"{msg}\n", (tag,))
        self._activity.see(tk.END)

    def _run_async(
        self,
        label: str,
        fn: Callable[[], Any],
        on_ok: Callable[[Any], None] | None = None,
        on_fail: Callable[[], None] | None = None,
    ) -> None:
        def worker() -> None:
            try:
                result = fn()
                self._work_q.put((self._on_async_ok, (label, result, on_ok)))
            except Exception as exc:
                self._work_q.put((self._on_async_err, (label, exc, on_fail)))

        self._busy_jobs += 1
        self._status.config(text=f"● Working: {label}…")
        self._activity_line("RUN", label)
        threading.Thread(target=worker, daemon=True).start()
        self.after(150, self._poll_work)

    def _poll_work(self) -> None:
        try:
            while True:
                callback, args = self._work_q.get_nowait()
                callback(*args)
        except queue.Empty:
            pass
        if threading.active_count() > 2:
            self.after(150, self._poll_work)

    def _on_async_ok(self, label: str, result: Any, on_ok: Callable[[Any], None] | None) -> None:
        self._busy_jobs = max(0, self._busy_jobs - 1)
        self._activity_line("OK", label)
        if on_ok:
            on_ok(result)
        elif isinstance(result, str) and result.strip():
            self._activity_line("INF", result.strip()[:500])
        if self._busy_jobs == 0:
            self._status.config(text=f"Ready · {self._region}")

    def _on_cw_groups_preloaded(self, groups: list[str]) -> None:
        self._cw_groups = groups
        self.after(0, lambda: self._cw_combo.configure(values=groups))
        if groups:
            self.after(0, lambda: self._cw_group_var.set(groups[0]))
        self._activity_line("OK", f"CloudWatch preload: {len(groups)} groups")

    def _on_async_err(self, label: str, exc: Exception, on_fail: Callable[[], None] | None = None) -> None:
        detail = str(exc)
        summary = f"{label} failed."
        first = detail.split("\n", 1)[0].strip()
        if first:
            summary = f"{label}: {first[:120]}"
        self._activity_line("ERR", f"{label}: {detail.splitlines()[0][:200]}")
        if on_fail:
            on_fail()
        show_error_dialog(self, "OMS Engine", summary, detail)
        self._busy_jobs = max(0, self._busy_jobs - 1)
        self._status.config(text=f"Ready · {self._region}")

    def _on_live_toggle(self) -> None:
        if self._live_sync.get():
            self._schedule_live_poll()
        elif self._live_after_id:
            self.after_cancel(self._live_after_id)
            self._live_after_id = None

    def _schedule_live_poll(self) -> None:
        if not self._live_sync.get():
            return
        self._live_delta_refresh()
        self._live_after_id = self.after(4000, self._schedule_live_poll)

    def _live_delta_refresh(self) -> None:
        stack = self._current_stack()
        if not stack:
            return
        tab = self._notebook.index(self._notebook.select())
        if tab == 0:
            toro = stack.host_by_role("toronado")
            if toro and self._host_ssm.get(toro.instance_id) == "Online":
                self._executor.submit(self._load_toro_services_bg, toro.instance_id)
        elif tab == 1:
            sm = stack.host_by_role("sitemanager")
            if sm and self._host_ssm.get(sm.instance_id) == "Online":
                self._executor.submit(self._load_iis_bg, sm.instance_id)

    def _refresh_inventory(self) -> None:
        def job():
            refresh_from_aws()
            self._region, self._stacks = load_inventory()
            return "Inventory updated."

        self._run_async("Refresh EC2 inventory", job)

    def _refresh_all(self) -> None:
        def job():
            stack = self._current_stack()
            if not stack:
                return "No stack."
            hosts = list(stack.hosts)
            self.after(0, lambda: self._hosts_pill.config(text=f"{len(hosts)} hosts"))

            def ping_one(h):
                return h, ssm_ping_status(h.instance_id)

            pings: dict[str, str] = {}
            with ThreadPoolExecutor(max_workers=min(6, len(hosts) or 1)) as pool:
                for host, ping in pool.map(lambda h: ping_one(h), hosts):
                    pings[host.instance_id] = ping
                    self._host_ssm[host.instance_id] = ping

            self.after(0, lambda: self._render_host_sidebar(stack, pings))

            futures = []
            toro = stack.host_by_role("toronado")
            sm = stack.host_by_role("sitemanager")
            if toro and pings.get(toro.instance_id) == "Online":
                futures.append(self._executor.submit(self._load_toro_services_bg, toro.instance_id))
            if sm and pings.get(sm.instance_id) == "Online":
                futures.append(self._executor.submit(self._load_iis_bg, sm.instance_id))
            for host in hosts:
                if pings.get(host.instance_id) != "Online":
                    continue
                self._executor.submit(self._fetch_serial_bg, host.instance_id)

            for fut in as_completed(futures):
                fut.result()

            self.after(0, lambda: self._last_refresh.config(text=f"Last refresh {datetime.now().strftime('%H:%M:%S')}"))
            return "Refresh complete."

        self._run_async("Refresh all", job)

    def _render_host_sidebar(self, stack, pings: dict[str, str]) -> None:
        for child in self._host_list.winfo_children():
            child.destroy()
        p = self._palette
        for host in stack.hosts:
            ping = pings.get(host.instance_id, "?")
            card = tk.Frame(self._host_list, bg=p.panel, padx=14, pady=8)
            card.pack(fill=tk.X)
            accent = p.teal if ping == "Online" else p.red
            tk.Frame(card, bg=accent, width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
            inner = tk.Frame(card, bg=p.panel)
            inner.pack(side=tk.LEFT, fill=tk.X, expand=True)
            row1 = tk.Frame(inner, bg=p.panel)
            row1.pack(fill=tk.X)
            role_lbl = tk.Label(
                row1,
                text=host.label,
                bg=p.panel,
                fg=p.ink,
                font=(p.ui, 10, "bold"),
                wraplength=200,
                justify=tk.LEFT,
            )
            role_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            pill_bg = p.green_soft if ping == "Online" else p.red_soft
            pill_fg = p.green if ping == "Online" else p.red
            pill = tk.Label(
                row1,
                text=f"● {ping}",
                bg=pill_bg,
                fg=pill_fg,
                font=(p.mono, 8, "bold"),
                padx=6,
                pady=1,
            )
            pill.pack(side=tk.RIGHT)
            tag_lbl = tk.Label(inner, text=host.name_tag, bg=p.panel, fg=p.ink_muted, font=(p.mono, 9), anchor=tk.W)
            tag_lbl.pack(fill=tk.X)
            meta = tk.Label(
                inner,
                text=f"{host.instance_id}\n{host.private_ip}",
                bg=p.panel,
                fg=p.ink_muted,
                font=(p.mono, 8),
                justify=tk.LEFT,
                anchor=tk.W,
            )
            meta.pack(fill=tk.X)
            tip = f"{host.label}\n{host.name_tag}\n{host.instance_id} · {host.private_ip}\nSSM: {ping}"
            ToolTip(card, tip)

    def _fetch_serial_bg(self, instance_id: str) -> None:
        meta = run_powershell(instance_id, [PS_HOST_META], timeout_seconds=45)
        if meta["status"] == "Success" and meta["stdout"].strip():
            try:
                payload = json.loads(meta["stdout"].strip())
                self._host_serial[instance_id] = str(payload.get("SerialNumber") or "-")
            except json.JSONDecodeError:
                pass

    def _load_toro_services_bg(self, instance_id: str) -> str:
        result = run_powershell(instance_id, [PS_LIST_OMS_SERVICES], timeout_seconds=120)
        ensure_ssm_ok(result)
        rows = _parse_json_rows(result["stdout"])
        self._toro_rows = rows
        self.after(0, self._render_toro_tree)
        self.after(0, self._update_summary)
        self.after(0, lambda: self._notebook.tab(0, text=f"Toronado ({len(rows)})"))
        return f"{len(rows)} services"

    def _load_iis_bg(self, instance_id: str) -> str:
        result = run_powershell(instance_id, [PS_LIST_IIS], timeout_seconds=120)
        ensure_ssm_ok(result)
        payload = json.loads(result["stdout"].strip())
        sites = payload.get("Sites") or []
        if isinstance(sites, dict):
            sites = [sites]
        pools = {p["Name"]: p.get("State", "") for p in (payload.get("AppPools") or [])}
        self._iis_sites = sites
        self._iis_pools = pools
        site_names = [s.get("Name", "") for s in sites]
        self.after(0, self._render_iis_tree)
        self.after(0, self._update_summary)
        self.after(0, lambda: self._log_site_combo.configure(values=site_names))
        if site_names:
            self.after(0, lambda: self._log_site_var.set(site_names[0]))
        self.after(0, lambda: self._notebook.tab(1, text=f"Site Manager ({len(sites)})"))
        return f"{len(sites)} sites"

    def _update_summary(self) -> None:
        running = sum(1 for r in self._toro_rows if "running" in format_service_status(r.get("Status")).lower())
        started = sum(1 for s in self._iis_sites if str(s.get("State", "")).lower() == "started")
        envs: set[str] = set()
        for r in self._toro_rows:
            det = classify_toro_service(str(r.get("Name", "")))
            if det.is_oms and det.environment:
                envs.add(det.environment)
        for s in self._iis_sites:
            det = classify_iis_site(str(s.get("Name", "")), str(s.get("PhysicalPath", "")))
            if det.is_oms and det.environment:
                envs.add(det.environment)
        self._sum_svc.config(text=f"Services {running} / {len(self._toro_rows)} running")
        self._sum_iis.config(text=f"IIS sites {started} / {len(self._iis_sites)} started")
        self._sum_env.config(text=f"Environments detected {len(envs)}")
        self._paint_health_bar(running, len(self._toro_rows), started, len(self._iis_sites))

    def _paint_health_bar(self, running_svc: int, total_svc: int, started_iis: int, total_iis: int) -> None:
        if not hasattr(self, "_health_bar"):
            return
        canvas = self._health_bar
        canvas.delete("all")
        total = total_svc + total_iis
        if total <= 0:
            return
        ok = running_svc + started_iis
        frac = max(0.0, min(1.0, ok / total))
        p = self._palette
        width = max(canvas.winfo_width(), 220)
        canvas.create_rectangle(0, 0, width, 8, fill=p.line, outline="")
        canvas.create_rectangle(0, 0, width * frac, 8, fill=p.green, outline="")

    def _render_toro_tree(self) -> None:
        filt = self._toro_filter.get().strip().lower()
        for item in self._toro_tree.get_children():
            self._toro_tree.delete(item)
        for row in self._toro_rows:
            name = str(row.get("Name", ""))
            if filt and filt not in name.lower():
                continue
            status = format_service_status(row.get("Status"))
            start = format_start_type(row.get("StartType"))
            det = classify_toro_service(name)
            env = det.environment if det.is_oms else "—"
            tag = status_tag(status)
            stripe = "stripe" if len(self._toro_tree.get_children()) % 2 else ""
            tags = tuple(t for t in (tag, stripe) if t)
            self._toro_tree.insert("", tk.END, values=(name, env, status, start), tags=tags)

    def _render_iis_tree(self) -> None:
        filt = self._iis_filter.get().strip().lower()
        seg = self._iis_seg.get()
        for item in self._iis_tree.get_children():
            self._iis_tree.delete(item)
        for site in self._iis_sites:
            name = str(site.get("Name", ""))
            path = str(site.get("PhysicalPath", ""))
            site_state = str(site.get("State", ""))
            pool = str(site.get("AppPool", ""))
            pool_state = str(self._iis_pools.get(pool, ""))
            det = classify_iis_site(name, path)
            if seg == "started" and site_state.lower() != "started":
                continue
            if seg == "stopped" and site_state.lower() != "stopped":
                continue
            if seg == "oms" and not det.is_oms:
                continue
            if filt and filt not in name.lower() and filt not in path.lower():
                continue
            env = det.environment if det.is_oms else "—"
            row_tag = iis_row_tag(site_state, pool_state)
            stripe = "stripe" if len(self._iis_tree.get_children()) % 2 else ""
            tags = (row_tag, stripe) if stripe else (row_tag,)
            self._iis_tree.insert(
                "",
                tk.END,
                values=(name, env, site_state, pool, pool_state, path),
                tags=tags,
            )

    def _iis_row_iid(self, site_name: str) -> str | None:
        for iid in self._iis_tree.get_children():
            if self._iis_tree.item(iid, "values")[0] == site_name:
                return iid
        return None

    def _set_iis_row_transition(self, site_name: str, label: str, pool_label: str | None = None) -> None:
        iid = self._iis_row_iid(site_name)
        if not iid:
            return
        vals = list(self._iis_tree.item(iid, "values"))
        vals[2] = label
        if pool_label is not None:
            vals[4] = pool_label
        self._iis_tree.item(iid, values=vals, tags=("transition",))

    def _optimistic_pool_state(self, pool_name: str, label: str) -> None:
        self._iis_pools[pool_name] = label
        self._refresh_pool_rows(pool_name)

    def _refresh_pool_rows(self, pool_name: str) -> None:
        for iid in self._iis_tree.get_children():
            vals = list(self._iis_tree.item(iid, "values"))
            if len(vals) > 4 and vals[3] == pool_name:
                vals[4] = self._iis_pools.get(pool_name, vals[4])
                tag = iis_row_tag(str(vals[2]), str(vals[4]))
                self._iis_tree.item(iid, values=vals, tags=(tag,))

    def _patch_iis_site_state(self, site_name: str, site_state: str, pool_state: str | None = None) -> None:
        for site in self._iis_sites:
            if site.get("Name") == site_name:
                site["State"] = site_state
                if pool_state and site.get("AppPool"):
                    self._iis_pools[str(site["AppPool"])] = pool_state
                break
        self._render_iis_tree()
        iid = self._iis_row_iid(site_name)
        if iid:
            self._iis_tree.selection_set(iid)
            self._iis_tree.see(iid)

    def _poll_iis_site(self, instance_id: str, site_name: str, want: str, attempts: int = 25) -> None:
        want_l = want.lower()

        def once(remaining: int) -> None:
            if remaining <= 0:
                self._activity_line("WARN", f"IIS {site_name}: timed out waiting for {want}")
                self._load_iis_bg(instance_id)
                return

            def job():
                result = run_powershell(instance_id, [ps_website_state(site_name)], timeout_seconds=45)
                ensure_ssm_ok(result)
                payload = json.loads(result["stdout"].strip())
                state = str(payload.get("State", ""))
                pool = str(payload.get("AppPool", ""))
                pool_state = str(payload.get("PoolState", "") or self._iis_pools.get(pool, ""))
                return state, pool, pool_state

            def on_ok(data):
                state, pool, pool_state = data
                self.after(0, lambda: self._patch_iis_site_state(site_name, state, pool_state))
                if pool:
                    self.after(0, lambda: self._refresh_pool_rows(pool))
                if state.lower() == want_l:
                    self._activity_line("OK", f"IIS {site_name} is {state} (pool {pool_state})")
                else:
                    self.after(900, lambda: once(remaining - 1))

            self._run_async(f"Poll IIS {site_name}", job, on_ok=on_ok)

        once(attempts)

    def _poll_iis_pool(
        self,
        instance_id: str,
        pool_name: str,
        want: str,
        site_name: str | None = None,
        attempts: int = 30,
    ) -> None:
        want_l = want.lower()

        def once(remaining: int) -> None:
            if remaining <= 0:
                self._activity_line("WARN", f"Pool {pool_name}: timed out waiting for {want}")
                return

            def job():
                result = run_powershell(instance_id, [ps_app_pool_state(pool_name)], timeout_seconds=45)
                ensure_ssm_ok(result)
                payload = json.loads(result["stdout"].strip())
                return str(payload.get("PoolState", ""))

            def on_ok(pool_state: str):
                self._iis_pools[pool_name] = pool_state
                self.after(0, lambda: self._refresh_pool_rows(pool_name))
                if pool_state.lower() == want_l:
                    self._activity_line("OK", f"Pool {pool_name} → {pool_state}")
                    if site_name:
                        self._poll_iis_site(instance_id, site_name, "started", attempts=12)
                else:
                    self.after(800, lambda: once(remaining - 1))

            self._run_async(f"Poll pool {pool_name}", job, on_ok=on_ok)

        once(attempts)

    def _selected_toro_service(self) -> str | None:
        sel = self._toro_tree.selection()
        if not sel:
            messagebox.showinfo("Select a service", "Choose a Toronado service.")
            return None
        return str(self._toro_tree.item(sel[0], "values")[0])

    def _patch_toro_status(self, name: str, status: str) -> None:
        for row in self._toro_rows:
            if row.get("Name") == name:
                row["Status"] = status
                break
        self._render_toro_tree()
        for iid in self._toro_tree.get_children():
            if self._toro_tree.item(iid, "values")[0] == name:
                self._toro_tree.selection_set(iid)
                self._toro_tree.see(iid)
                break

    def _poll_toro_service(self, instance_id: str, name: str, want: str, attempts: int = 30) -> None:
        want_l = want.lower()

        def once(remaining: int) -> None:
            if remaining <= 0:
                self._activity_line("WARN", f"{name}: timed out waiting for {want}")
                self._load_toro_services_bg(instance_id)
                return

            def job():
                result = run_powershell(instance_id, [ps_service_status(name)], timeout_seconds=45)
                ensure_ssm_ok(result)
                payload = json.loads(result["stdout"].strip())
                return format_service_status(payload.get("Status"))

            def on_ok(status: str):
                self.after(0, lambda: self._patch_toro_status(name, status))
                if want_l in status.lower():
                    self._activity_line("OK", f"{name} → {status}")
                else:
                    self.after(800, lambda: once(remaining - 1))

            self._run_async(f"Poll {name}", job, on_ok=on_ok)

        once(attempts)

    def _service_action(self, action: str) -> None:
        name = self._selected_toro_service()
        if not name:
            return
        stack = self._current_stack()
        toro = stack.host_by_role("toronado") if stack else None
        if not toro:
            return
        if not messagebox.askyesno("Confirm", f"{action.upper()} service?\n\n{name}"):
            return
        want = "running" if action == "start" else "stopped" if action == "stop" else "running"
        self._patch_toro_status(name, "Start pending" if action == "start" else "Stop pending")

        def job():
            result = run_powershell(toro.instance_id, [ps_service_action(name, action)], timeout_seconds=120)
            ensure_ssm_ok(result)
            return "sent"

        def on_ok(_):
            self._poll_toro_service(toro.instance_id, name, want)

        self._run_async(f"{action} {name}", job, on_ok=on_ok)

    def _selected_iis_row(self) -> tuple[str, str, str] | None:
        sel = self._iis_tree.selection()
        if not sel:
            return None
        vals = self._iis_tree.item(sel[0], "values")
        return str(vals[0]), str(vals[3]), str(vals[5]) if len(vals) > 5 else ""

    def _iis_recycle_pool(self) -> None:
        row = self._selected_iis_row()
        if not row:
            messagebox.showinfo("Select a site", "Choose an IIS site row.")
            return
        site, pool, _ = row
        stack = self._current_stack()
        sm = stack.host_by_role("sitemanager") if stack else None
        if not sm or not pool:
            return
        if not messagebox.askyesno("Confirm", f"Recycle app pool {pool}?"):
            return
        self._set_iis_row_transition(site, "Recycling…", pool_label="Stopping…")
        self._optimistic_pool_state(pool, "Stopping…")

        def job():
            result = run_powershell(sm.instance_id, [ps_iis_recycle_pool(pool)], timeout_seconds=120)
            ensure_ssm_ok(result)
            return pool

        def on_ok(_):
            self._optimistic_pool_state(pool, "Starting…")
            self._poll_iis_pool(sm.instance_id, pool, "started", site_name=site)

        self._run_async(f"Recycle {pool}", job, on_ok=on_ok)

    def _iis_site(self, action: str) -> None:
        row = self._selected_iis_row()
        if not row:
            messagebox.showinfo("Select a site", "Choose an IIS site row.")
            return
        site, _, _ = row
        stack = self._current_stack()
        sm = stack.host_by_role("sitemanager") if stack else None
        if not sm:
            return
        if not messagebox.askyesno("Confirm", f"{action.upper()} site {site}?"):
            return
        want = "started" if action in ("start", "restart") else "stopped"
        self._set_iis_row_transition(site, f"{action.title()}…")

        def job():
            result = run_powershell(sm.instance_id, [ps_iis_site_action(site, action)], timeout_seconds=120)
            ensure_ssm_ok(result)
            return action

        def on_ok(_):
            self._poll_iis_site(sm.instance_id, site, want)

        self._run_async(f"IIS {action} {site}", job, on_ok=on_ok)

    def _file_instance_id(self) -> str | None:
        stack = self._current_stack()
        if not stack:
            return None
        role = self._file_host_role.get()
        host = stack.host_by_role(role)
        if not host:
            messagebox.showinfo("Host", f"No {role} host in this stack.")
            return None
        if self._host_ssm.get(host.instance_id) != "Online":
            messagebox.showwarning("SSM", f"{host.name_tag} is not SSM Online.")
            return None
        return host.instance_id

    def _file_remote_path(self, name: str | None = None) -> str:
        base = self._file_path.get().strip().rstrip("\\")
        if not name:
            return base
        return f"{base}\\{name}"

    def _file_selected_name(self) -> tuple[str, str] | None:
        sel = self._file_tree.selection()
        if not sel:
            return None
        name, kind, *_ = self._file_tree.item(sel[0], "values")
        return str(name), str(kind)

    def _update_file_server_clock(self, server: dict[str, Any]) -> None:
        if not server:
            return
        host = server.get("ComputerName", "?")
        local = server.get("ServerTimeLocal", "?")
        tz = server.get("TimeZone", "")
        utc = server.get("ServerTimeUtc", "")
        self._file_server_label.config(
            text=f"Server {host}  ·  local {local} ({tz})  ·  UTC {utc}"
        )

    def _fill_file_tree(self, rows: list[dict[str, Any]], server: dict[str, Any], path: str, cached: bool = False) -> None:
        self._file_last_listed_path = path
        self._update_file_server_clock(server)
        for item in self._file_tree.get_children():
            self._file_tree.delete(item)
        for idx, row in enumerate(rows):
            kind = "Folder" if row.get("IsDirectory") else "File"
            nbytes = int(row.get("Length") or 0)
            size_disp = "—" if kind == "Folder" else format_file_size(nbytes)
            modified = format_remote_timestamp(row.get("LastWriteTime", ""))
            stripe = "stripe" if idx % 2 else ""
            tags = (stripe,) if stripe else ()
            self._file_tree.insert(
                "",
                tk.END,
                values=(row.get("Name"), kind, size_disp, modified, str(nbytes)),
                tags=tags,
            )
        note = "cached" if cached else "loaded"
        self._activity_line("INF", f"{note} {len(rows)} items · {path}")

    def _file_list_dir(self, revert_path_on_error: str | None = None, force: bool = False) -> None:
        instance_id = self._file_instance_id()
        if not instance_id:
            return
        path = self._file_path.get().strip()
        cache_key = (instance_id, path.lower())
        now = time.time()
        if not force and cache_key in self._dir_cache:
            expiry, server, rows = self._dir_cache[cache_key]
            if expiry > now:
                self._fill_file_tree(rows, server, path, cached=True)
                return

        def job():
            result = run_powershell(instance_id, [ps_list_directory(path)], timeout_seconds=90)
            ensure_ssm_ok(result)
            server, rows = _parse_list_directory_payload(result["stdout"])
            self._dir_cache[cache_key] = (now + DIR_CACHE_TTL_SECONDS, server, rows)
            return server, rows

        def on_ok(payload: tuple[dict[str, Any], list[dict[str, Any]]]):
            server, rows = payload
            self._fill_file_tree(rows, server, path, cached=False)

        def on_fail():
            if revert_path_on_error is not None:
                self._file_path.set(revert_path_on_error)

        self._run_async(f"List {path}", job, on_ok=on_ok, on_fail=on_fail)

    def _file_go_up(self) -> None:
        path = self._file_path.get().strip().rstrip("\\")
        if len(path) <= 3:
            return
        parent = path.rsplit("\\", 1)[0]
        self._file_path.set(parent)
        self._file_list_dir()

    def _file_on_double_click(self, _event) -> None:
        row = self._file_selected_name()
        if not row:
            return
        name, kind = row
        if kind == "Folder":
            base = self._file_path.get().strip().rstrip("\\")
            self._file_path.set(f"{base}\\{name}")
            self._file_list_dir(revert_path_on_error=base)
            return
        self._file_view(name)

    def _file_view(self, filename: str | None = None) -> None:
        if filename is None:
            row = self._file_selected_name()
            if not row:
                messagebox.showinfo("File", "Select a file in the list.")
                return
            filename, kind = row
            if kind != "File":
                messagebox.showinfo("File", "Select a file row (not a folder).")
                return
        instance_id = self._file_instance_id()
        if not instance_id:
            return
        remote = self._file_remote_path(filename)
        text_ext = (".log", ".txt", ".htm", ".html", ".xml", ".config", ".asp", ".aspx", ".json", ".md", ".csv")
        lower = filename.lower()
        if not any(lower.endswith(ext) for ext in text_ext):
            if not messagebox.askyesno(
                "Preview",
                f"{filename} may not be plain text.\n\nTry preview anyway, or use Open on PC / Download.",
            ):
                return

        def job():
            result = run_powershell(instance_id, [ps_tail_text_file(remote)], timeout_seconds=120)
            ensure_ssm_ok(result)
            return result.get("stdout") or ""

        def on_ok(text: str):
            self._show_file_preview(remote, text)

        self._run_async(f"View {filename}", job, on_ok=on_ok)

    def _show_file_preview(self, remote_path: str, text: str) -> None:
        win = tk.Toplevel(self)
        win.title(f"Preview — {remote_path.split(chr(92))[-1]}")
        win.geometry("900x560")
        win.minsize(640, 400)
        header = ttk.Label(win, text=remote_path, font=("Consolas", 9))
        header.pack(anchor=tk.W, padx=12, pady=(10, 4))
        box = scrolledtext.ScrolledText(win, font=("Consolas", 10), wrap=tk.NONE)
        box.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        box.insert(tk.END, text)
        box.see(tk.END)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=(0, 10))

    def _file_open_locally(self) -> None:
        row = self._file_selected_name()
        if not row or row[1] != "File":
            messagebox.showinfo("File", "Select a file to open on your PC.")
            return
        name = row[0]
        instance_id = self._file_instance_id()
        if not instance_id:
            return
        remote = self._file_remote_path(name)
        dest_dir = os.path.join(tempfile.gettempdir(), "oms-engine")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, name)

        def job():
            self._ssm_download_to_file(instance_id, remote, dest)
            return dest

        def on_ok(path: str):
            self._hide_transfer()
            try:
                os.startfile(path)  # type: ignore[attr-defined]
            except OSError:
                subprocess.run(["explorer", "/select,", path], check=False)
            self._activity_line("OK", f"Opened {path}")

        def on_fail():
            self._hide_transfer()

        self._run_async(f"Open {name}", job, on_ok=on_ok, on_fail=on_fail)

    def _file_use_site_path(self) -> None:
        row = self._selected_iis_row()
        if not row:
            messagebox.showinfo("Site", "Select an IIS site on the Site Manager tab first.")
            return
        _, _, physical = row
        if not physical:
            return
        content = content_server_path_from_unc(physical)
        if content:
            self._file_path.set(content)
            self._file_host_role.set("content")
        else:
            self._file_path.set(physical)
            self._file_host_role.set("sitemanager")
        self._select_notebook_tab("Files")
        self._file_list_dir()

    def _ssm_download_to_file(self, instance_id: str, remote: str, dest: str) -> int:
        size_result = run_powershell(instance_id, [ps_file_length(remote)], timeout_seconds=90)
        if size_result["status"] != "Success":
            raise RuntimeError(size_result["stderr"] or size_result["stdout"] or size_result["status"])
        total = int((size_result["stdout"] or "0").strip())
        label = remote.split("\\")[-1]
        self.after(0, lambda: self._show_transfer(f"SSM {label}", total))

        if total <= SSM_INLINE_MAX:
            result = run_powershell(
                instance_id,
                [ps_read_file_base64(remote, max_bytes=SSM_INLINE_MAX)],
                timeout_seconds=300,
            )
            ensure_ssm_ok(result)
            payload = json.loads(result["stdout"].strip())
            data = base64.b64decode(payload["Base64"])
            with open(dest, "wb") as handle:
                handle.write(data)
            self.after(0, lambda: self._update_transfer(total, total))
            return total

        offset = 0
        with open(dest, "wb") as handle:
            while offset < total:
                chunk_len = min(SSM_CHUNK_BYTES, total - offset)
                result = run_powershell(
                    instance_id,
                    [ps_read_file_chunk_base64(remote, offset, chunk_len)],
                    timeout_seconds=180,
                )
                if result["status"] != "Success":
                    raise RuntimeError(result["stderr"] or result["stdout"] or result["status"])
                payload = json.loads(result["stdout"].strip())
                read = int(payload.get("Read", 0))
                handle.write(base64.b64decode(payload["Base64"]))
                offset += read
                done = offset
                self.after(0, lambda d=done, t=total: self._update_transfer(d, t))
        return total

    def _file_download(self) -> None:
        sel = self._file_tree.selection()
        if not sel:
            messagebox.showinfo("File", "Select a file row to download.")
            return
        name, kind, *_ = self._file_tree.item(sel[0], "values")
        if kind != "File":
            messagebox.showinfo("File", "Select a file, not a folder.")
            return
        instance_id = self._file_instance_id()
        if not instance_id:
            return
        remote = f"{self._file_path.get().strip().rstrip(chr(92))}\\{name}"
        dest = filedialog.asksaveasfilename(initialfile=name, title="Save remote file locally")
        if not dest:
            return

        def job():
            try:
                return self._ssm_download_to_file(instance_id, remote, dest)
            finally:
                self.after(0, self._hide_transfer)

        def on_ok(nbytes: int):
            self._activity_line("OK", f"SSM downloaded {nbytes:,} bytes → {dest}")

        self._run_async(f"Download {name}", job, on_ok=on_ok)

    def _sftp_stack_host(self) -> tuple[str, int] | None:
        stack = self._current_stack()
        if not stack or not stack.sftp:
            messagebox.showinfo("SFTP", "No SFTP host configured for this stack in inventory.json.")
            return None
        return stack.sftp.host, stack.sftp.port

    def _sftp_connect(self) -> None:
        host_port = self._sftp_stack_host()
        if not host_port:
            return
        host, port = host_port
        try:
            resolve_credentials(self._sftp_cred_user, self._sftp_cred_pass)
        except ValueError:
            user = simpledialog.askstring("SFTP user", "Domain\\user (e.g. omspod\\you):", parent=self)
            if not user:
                return
            pwd = simpledialog.askstring("SFTP password", "Password (not stored in repo):", show="*", parent=self)
            if pwd is None:
                return
            self._sftp_cred_user = user
            self._sftp_cred_pass = pwd

        def job():
            session = SftpSession(host, port)
            user, pwd = resolve_credentials(self._sftp_cred_user, self._sftp_cred_pass)
            session.connect(user, pwd)
            return session

        def on_ok(session: SftpSession):
            self._sftp = session
            self._sftp_status.config(text=f"Connected {session.username} @ {host}")
            self._activity_line("OK", f"SFTP connected to {host}")

        self._run_async("SFTP connect", job, on_ok=on_ok)

    def _sftp_disconnect(self) -> None:
        self._sftp.close()
        self._sftp_status.config(text="Not connected")

    def _sftp_goto(self, path: str) -> None:
        self._sftp_path.set(path.rstrip("/") or "/")
        self._sftp_list_dir()

    def _sftp_go_up(self) -> None:
        path = self._sftp_path.get().strip().rstrip("/")
        if path in ("", "/"):
            return
        parent = path.rsplit("/", 1)[0] or "/"
        self._sftp_path.set(parent)
        self._sftp_list_dir()

    def _sftp_use_site_path(self) -> None:
        row = self._selected_iis_row()
        if not row:
            messagebox.showinfo("Site", "Select an IIS site first.")
            return
        site, _, physical = row
        stack = self._current_stack()
        if not stack:
            return
        remote = sftp_path_for_iis_site(stack, site, physical)
        if not remote:
            messagebox.showinfo("SFTP", "Could not map this site to an SFTP path.")
            return
        self._sftp_path.set(remote)
        self._select_notebook_tab("SFTP")
        if self._sftp.connected:
            self._sftp_list_dir()
        else:
            messagebox.showinfo("SFTP", "Path set. Connect SFTP, then List.")

    def _sftp_list_dir(self) -> None:
        if not self._sftp.connected:
            messagebox.showinfo("SFTP", "Connect SFTP first.")
            return
        path = self._sftp_path.get().strip() or "/"

        def job():
            return self._sftp.list_dir(path)

        def on_ok(entries):
            for item in self._sftp_tree.get_children():
                self._sftp_tree.delete(item)
            for ent in entries:
                kind = "Folder" if ent.is_directory else "File"
                size = "—" if ent.is_directory else format_file_size(ent.size)
                mtime = datetime.fromtimestamp(ent.mtime).strftime("%Y-%m-%d %H:%M") if ent.mtime else ""
                self._sftp_tree.insert("", tk.END, values=(ent.name, kind, size, mtime))
            self._activity_line("OK", f"SFTP listed {len(entries)} under {path}")

        self._run_async(f"SFTP list {path}", job, on_ok=on_ok)

    def _sftp_on_double_click(self, _event) -> None:
        sel = self._sftp_tree.selection()
        if not sel:
            return
        name, kind, *_ = self._sftp_tree.item(sel[0], "values")
        if kind != "Folder":
            return
        base = self._sftp_path.get().strip().rstrip("/")
        self._sftp_path.set(f"{base}/{name}".replace("//", "/"))
        self._sftp_list_dir()

    def _sftp_download(self) -> None:
        if not self._sftp.connected:
            messagebox.showinfo("SFTP", "Connect SFTP first.")
            return
        sel = self._sftp_tree.selection()
        if not sel:
            messagebox.showinfo("SFTP", "Select a file to download.")
            return
        name, kind, size_str, *_ = self._sftp_tree.item(sel[0], "values")
        if kind != "File":
            messagebox.showinfo("SFTP", "Select a file, not a folder.")
            return
        base = self._sftp_path.get().strip().rstrip("/")
        remote = f"{base}/{name}".replace("//", "/")
        dest = filedialog.asksaveasfilename(initialfile=name, title="Save SFTP file locally")
        if not dest:
            return
        try:
            total = int(size_str) if size_str else 0
        except ValueError:
            total = 0

        def job():
            self.after(0, lambda: self._show_transfer(f"SFTP {name}", total or None))

            def progress(done: int, tot: int) -> None:
                self.after(0, lambda: self._update_transfer(done, tot, f"SFTP {name}"))

            try:
                return self._sftp.download(remote, dest, progress=progress if total else None)
            finally:
                self.after(0, self._hide_transfer)

        def on_ok(nbytes: int):
            self._activity_line("OK", f"SFTP downloaded {nbytes:,} bytes → {dest}")

        self._run_async(f"SFTP download {name}", job, on_ok=on_ok)

    def _site_physical_path(self) -> str | None:
        row = self._selected_iis_row()
        if row and row[2]:
            return row[2]
        name = self._log_site_var.get()
        for site in self._iis_sites:
            if site.get("Name") == name:
                return site.get("PhysicalPath")
        return None

    def _tail_sm_log(self) -> None:
        path = self._site_physical_path()
        if not path:
            messagebox.showinfo("Site required", "Select an IIS site or refresh the stack.")
            return
        stack = self._current_stack()
        sm = stack.host_by_role("sitemanager") if stack else None
        if not sm:
            return
        bases = shoplogic_path_candidates(path)
        hosts: list[tuple[str, str]] = []
        content = stack.host_by_role("content") if stack else None
        if content:
            hosts.append(("Content", content.instance_id))
        hosts.append(("Site Manager", sm.instance_id))
        script = ps_tail_shoplogic_debug_bases(bases, lines=120)

        def job():
            combined: list[str] = []
            for host_label, instance_id in hosts:
                combined.append(f"--- {host_label} ---")
                result = run_powershell(instance_id, [script], timeout_seconds=120)
                combined.append(result.get("stdout") or result.get("stderr") or result["status"])
                if "=== Log file:" in (result.get("stdout") or ""):
                    break
            return "\n".join(combined)

        def on_ok(text: str):
            self._show_log_view(text, title="ShopLogic log")

        self._run_async("Tail ShopLogic", job, on_ok=on_ok)

    def _tail_toro_log(self) -> None:
        name = self._selected_toro_service()
        if not name:
            return
        stack = self._current_stack()
        toro = stack.host_by_role("toronado") if stack else None
        if not toro:
            return

        def job():
            result = run_powershell(toro.instance_id, [ps_tail_toro_logs(name)], timeout_seconds=120)
            ensure_ssm_ok(result)
            return result["stdout"] or result["stderr"]

        def on_ok(text: str):
            self._show_log_view(text, title=f"Toro log — {name}")

        self._run_async("Tail Toro log", job, on_ok=on_ok)

    def _refresh_cw_groups(self) -> None:
        self._cw_group_var.set("Refreshing…")

        def job():
            groups = list_shoplogic_api_log_groups(force_refresh=True)
            self._cw_groups = groups
            self.after(0, lambda: self._cw_combo.configure(values=groups))
            if groups:
                self.after(0, lambda: self._cw_group_var.set(groups[0]))
            return f"{len(groups)} groups"

        self._run_async("CloudWatch groups", job)

    def _tail_cw_log(self) -> None:
        group = self._cw_group_var.get()
        if not group:
            messagebox.showinfo("Log group", "Select a CloudWatch log group.")
            return

        def job():
            return tail_log_group(group, limit=100)

        def on_ok(text: str):
            self._show_log_view(text, title=f"CloudWatch — {group}")

        self._run_async("Tail CloudWatch", job, on_ok=on_ok)

    def _show_log_view(self, text: str, title: str = "Log tail") -> None:
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("960x520")
        win.minsize(640, 360)
        p = self._palette
        box = scrolledtext.ScrolledText(
            win,
            font=("Consolas", 10),
            wrap=tk.NONE,
            bg=p.log_bg,
            fg=p.log_fg,
            insertbackground=p.log_fg,
        )
        box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        box.insert(tk.END, text)
        box.see(tk.END)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=(0, 10))


def main() -> None:
    app = OmsEngineApp()
    app.mainloop()


if __name__ == "__main__":
    main()
