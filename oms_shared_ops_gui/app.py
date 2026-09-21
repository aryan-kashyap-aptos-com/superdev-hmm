#!/usr/bin/env python3
"""GUI for OMS shared stack health: Toronado, Site Manager IIS, and log tails."""

from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Callable

from cloudwatch_logs import list_shoplogic_api_log_groups, preload_log_groups_background, tail_log_group
from display_utils import format_service_status, format_start_type, status_tag
from inventory_io import INVENTORY_PATH, load_inventory, refresh_from_aws
from path_candidates import shoplogic_path_candidates
from ssm_runner import (
    PS_HOST_META,
    PS_LIST_IIS,
    PS_LIST_OMS_SERVICES,
    ps_iis_recycle_pool,
    ps_iis_site_action,
    ps_service_action,
    ps_tail_shoplogic_debug_bases,
    ps_tail_toro_logs,
    ps_wait_service_settle,
    run_powershell,
    ssm_ping_status,
)

STATUS_COLORS = {
    "Running": "#0d6b2e",
    "Stopped": "#b42318",
    "Pending": "#9a6700",
    "Online": "#0d6b2e",
    "NotManaged": "#b42318",
}


class OpsGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("OMS Shared Ops - Toro and Site Manager")
        self.geometry("1180x780")
        self.minsize(960, 640)
        self.configure(bg="#f4f5f7")

        self._work_q: queue.Queue[tuple[Callable[..., None], tuple]] = queue.Queue()
        self._ssm_lock = threading.Lock()
        self._region, self._stacks = load_inventory()
        self._stack_var = tk.StringVar()
        self._toro_filter = tk.StringVar()
        self._host_ssm: dict[str, str] = {}
        self._host_serial: dict[str, str] = {}
        self._iis_sites: list[dict[str, Any]] = []
        self._cw_groups: list[str] = []

        self._setup_styles()
        self._build_ui()
        if self._stacks:
            self._stack_var.set(self._stacks[0].label)
        self.after(150, self._refresh_all)
        self._cw_group_var.set("Loading CloudWatch groups...")
        preload_log_groups_background(self._on_cw_groups_preloaded)

    def _setup_styles(self) -> None:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), background="#f4f5f7")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#444", background="#f4f5f7")
        style.configure("TFrame", background="#f4f5f7")
        style.configure("TLabelframe", background="#f4f5f7")
        style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))

    def _current_stack(self):
        label = self._stack_var.get()
        for s in self._stacks:
            if s.label == label:
                return s
        return self._stacks[0] if self._stacks else None

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(12, 10, 12, 4))
        header.pack(fill=tk.X)
        ttk.Label(header, text="OMS Shared Operations", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header,
            text="Toronado services, Site Manager IIS, and log tails via AWS SSM and CloudWatch.",
            style="Sub.TLabel",
        ).pack(anchor=tk.W)

        top = ttk.Frame(self, padding=(12, 4, 12, 8))
        top.pack(fill=tk.X)

        ttk.Label(top, text="Stack").pack(side=tk.LEFT)
        stack_combo = ttk.Combobox(
            top,
            textvariable=self._stack_var,
            values=[s.label for s in self._stacks],
            state="readonly",
            width=48,
        )
        stack_combo.pack(side=tk.LEFT, padx=(8, 12))
        stack_combo.bind("<<ComboboxSelected>>", lambda _: self._refresh_all())

        ttk.Button(top, text="Refresh all", command=self._refresh_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="Refresh EC2 IDs", command=self._refresh_inventory).pack(side=tk.LEFT, padx=3)

        self._stack_desc = ttk.Label(top, text="", wraplength=520, style="Sub.TLabel")
        self._stack_desc.pack(side=tk.LEFT, padx=(16, 0))

        host_frame = ttk.LabelFrame(self, text="Hosts", padding=8)
        host_frame.pack(fill=tk.X, padx=12, pady=4)

        hcols = ("role", "name_tag", "instance_id", "private_ip", "serial", "ssm")
        self._host_tree = ttk.Treeview(host_frame, columns=hcols, show="headings", height=3)
        headings = {
            "role": "Role",
            "name_tag": "Name tag",
            "instance_id": "Instance ID",
            "private_ip": "Private IP",
            "serial": "S/N",
            "ssm": "SSM",
        }
        widths = {"role": 140, "name_tag": 260, "instance_id": 170, "private_ip": 110, "serial": 120, "ssm": 90}
        for col in hcols:
            self._host_tree.heading(col, text=headings[col])
            self._host_tree.column(col, width=widths[col], stretch=col == "name_tag")
        self._host_tree.pack(fill=tk.X)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        toro_tab = ttk.Frame(notebook, padding=10)
        notebook.add(toro_tab, text="Toronado")
        self._build_toro_tab(toro_tab)

        iis_tab = ttk.Frame(notebook, padding=10)
        notebook.add(iis_tab, text="Site Manager (IIS)")
        self._build_iis_tab(iis_tab)

        logs_tab = ttk.Frame(notebook, padding=10)
        notebook.add(logs_tab, text="Logs")
        self._build_logs_tab(logs_tab)

        activity = ttk.LabelFrame(self, text="Activity", padding=6)
        activity.pack(fill=tk.X, padx=12, pady=(0, 6))
        self._log = tk.Text(activity, height=5, wrap=tk.WORD, font=("Consolas", 9), bg="#fafbfc")
        self._log.pack(fill=tk.X)

        self._status = ttk.Label(
            self,
            text=f"Region: {self._region}  |  Inventory: {INVENTORY_PATH.name}",
            anchor=tk.W,
            padding=(12, 4),
        )
        self._status.pack(fill=tk.X)

    def _build_toro_tab(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Filter").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self._toro_filter, width=36).pack(side=tk.LEFT, padx=8)
        ttk.Button(row, text="Apply", command=self._apply_toro_filter).pack(side=tk.LEFT)

        btns = ttk.Frame(parent)
        btns.pack(fill=tk.X, pady=(10, 6))
        for label, action in [("Start", "start"), ("Stop", "stop"), ("Restart", "restart")]:
            ttk.Button(btns, text=label, command=lambda a=action: self._service_action(a)).pack(side=tk.LEFT, padx=3)

        cols = ("name", "status", "start_type")
        self._toro_tree = ttk.Treeview(parent, columns=cols, show="headings", height=16)
        self._toro_tree.heading("name", text="Service name")
        self._toro_tree.heading("status", text="Status")
        self._toro_tree.heading("start_type", text="Startup type")
        self._toro_tree.column("name", width=520)
        self._toro_tree.column("status", width=130)
        self._toro_tree.column("start_type", width=120)
        self._toro_tree.pack(fill=tk.BOTH, expand=True)
        for tag, color in STATUS_COLORS.items():
            if tag in ("Running", "Stopped", "Pending"):
                self._toro_tree.tag_configure(tag, foreground=color)

    def _build_iis_tab(self, parent: ttk.Frame) -> None:
        btns = ttk.Frame(parent)
        btns.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btns, text="Recycle app pool", command=self._iis_recycle_pool).pack(side=tk.LEFT, padx=3)
        ttk.Button(btns, text="Start site", command=lambda: self._iis_site("start")).pack(side=tk.LEFT, padx=3)
        ttk.Button(btns, text="Stop site", command=lambda: self._iis_site("stop")).pack(side=tk.LEFT, padx=3)
        ttk.Button(btns, text="Restart site", command=lambda: self._iis_site("restart")).pack(side=tk.LEFT, padx=3)

        iis_cols = ("site", "site_state", "app_pool", "pool_state", "physical_path")
        self._iis_tree = ttk.Treeview(parent, columns=iis_cols, show="headings", height=16)
        labels = ("Site", "Site state", "App pool", "Pool state", "Physical path")
        for col, text in zip(iis_cols, labels):
            self._iis_tree.heading(col, text=text)
        self._iis_tree.column("site", width=200)
        self._iis_tree.column("site_state", width=90)
        self._iis_tree.column("app_pool", width=200)
        self._iis_tree.column("pool_state", width=90)
        self._iis_tree.column("physical_path", width=360)
        self._iis_tree.pack(fill=tk.BOTH, expand=True)

    def _build_logs_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="See LOGS-INTEGRATION.md for SFTP vs SSM vs CloudWatch. Tails below use SSM (SM/Toro) or CloudWatch (API).",
            style="Sub.TLabel",
            wraplength=900,
        ).pack(anchor=tk.W, pady=(0, 8))

        inner = ttk.Notebook(parent)
        inner.pack(fill=tk.BOTH, expand=True)

        sm_lf = ttk.Frame(inner, padding=8)
        inner.add(sm_lf, text="Site Manager")
        ttk.Label(sm_lf, text="IIS site (select row on Site Manager tab first, or pick here):").pack(anchor=tk.W)
        self._log_site_var = tk.StringVar()
        self._log_site_combo = ttk.Combobox(sm_lf, textvariable=self._log_site_var, width=70, state="readonly")
        self._log_site_combo.pack(anchor=tk.W, pady=4)
        ttk.Button(sm_lf, text="Tail ShopLogic log (last 120 lines)", command=self._tail_sm_log).pack(anchor=tk.W, pady=4)

        toro_lf = ttk.Frame(inner, padding=8)
        inner.add(toro_lf, text="Toronado")
        ttk.Label(
            toro_lf,
            text="Select an OMS service on the Toronado tab. Logs are under that service install folder (often ...\\log\\), not only D:\\torojobs root.",
        ).pack(anchor=tk.W)
        ttk.Button(toro_lf, text="Tail latest Toro .log (last 80 lines)", command=self._tail_toro_log).pack(anchor=tk.W, pady=8)

        api_lf = ttk.Frame(inner, padding=8)
        inner.add(api_lf, text="API (CloudWatch)")
        row = ttk.Frame(api_lf)
        row.pack(fill=tk.X)
        ttk.Button(row, text="Refresh log groups", command=self._refresh_cw_groups).pack(side=tk.LEFT)
        self._cw_group_var = tk.StringVar()
        self._cw_combo = ttk.Combobox(row, textvariable=self._cw_group_var, width=72, state="readonly")
        self._cw_combo.pack(side=tk.LEFT, padx=8)
        ttk.Button(api_lf, text="Tail recent events", command=self._tail_cw_log).pack(anchor=tk.W, pady=8)

        self._log_view = scrolledtext.ScrolledText(parent, height=14, font=("Consolas", 9), wrap=tk.WORD)
        self._log_view.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

    def _log_line(self, msg: str) -> None:
        self._log.insert(tk.END, msg + "\n")
        self._log.see(tk.END)

    def _run_async(self, label: str, fn: Callable[[], Any], use_lock: bool = True) -> None:
        def worker() -> None:
            try:
                if use_lock:
                    with self._ssm_lock:
                        result = fn()
                else:
                    result = fn()
                self._work_q.put((self._on_async_ok, (label, result)))
            except Exception as exc:
                self._work_q.put((self._on_async_err, (label, exc)))

        self._status.config(text=f"Working: {label}...")
        threading.Thread(target=worker, daemon=True).start()
        self.after(200, self._poll_work)

    def _poll_work(self) -> None:
        try:
            while True:
                callback, args = self._work_q.get_nowait()
                callback(*args)
        except queue.Empty:
            pass
        if threading.active_count() > 1:
            self.after(200, self._poll_work)
        else:
            self._status.config(text=f"Ready  |  Region: {self._region}")

    def _on_async_ok(self, label: str, result: Any) -> None:
        self._log_line(f"[OK] {label}")
        if isinstance(result, str) and result.strip():
            self._log_line(result.strip()[:800])
        self._status.config(text=f"Ready  |  Region: {self._region}")

    def _on_cw_groups_preloaded(self, groups: list[str]) -> None:
        self._cw_groups = groups
        self.after(0, lambda: self._cw_combo.configure(values=groups))
        if groups:
            self.after(0, lambda: self._cw_group_var.set(groups[0]))
        else:
            self.after(0, lambda: self._cw_group_var.set(""))
        self._log_line(f"[OK] CloudWatch preload: {len(groups)} group(s)")

    def _on_async_err(self, label: str, exc: Exception) -> None:
        self._log_line(f"[ERROR] {label}: {exc}")
        messagebox.showerror("Error", f"{label}\n\n{exc}")

    def _refresh_inventory(self) -> None:
        def job():
            refresh_from_aws()
            self._region, self._stacks = load_inventory()
            return "Inventory updated."

        self._run_async("Refresh EC2 inventory", job, use_lock=False)

    def _refresh_all(self) -> None:
        def job():
            stack = self._current_stack()
            if not stack:
                return "No stack."
            self.after(0, lambda: self._stack_desc.config(text=stack.description))
            self.after(0, self._clear_host_tree)

            for host in stack.hosts:
                ping = ssm_ping_status(host.instance_id)
                self._host_ssm[host.instance_id] = ping
                serial = "-"
                if ping == "Online":
                    meta = run_powershell(host.instance_id, [PS_HOST_META], timeout_seconds=60)
                    if meta["status"] == "Success" and meta["stdout"].strip():
                        try:
                            payload = json.loads(meta["stdout"].strip())
                            serial = str(payload.get("SerialNumber") or "-")
                            self._host_serial[host.instance_id] = serial
                        except json.JSONDecodeError:
                            pass
                self.after(
                    0,
                    lambda h=host, p=ping, s=serial: self._host_tree.insert(
                        "",
                        tk.END,
                        values=(h.label, h.name_tag, h.instance_id, h.private_ip, s, p),
                    ),
                )

            toro = stack.host_by_role("toronado")
            sm = stack.host_by_role("sitemanager")
            msg_parts = []
            if toro:
                msg_parts.append(self._load_toro_services(toro.instance_id))
            if sm:
                msg_parts.append(self._load_iis(sm.instance_id))
            return " | ".join(msg_parts) if msg_parts else "Done."

        self._run_async("Refresh all", job)

    def _clear_host_tree(self) -> None:
        for item in self._host_tree.get_children():
            self._host_tree.delete(item)

    def _load_toro_services(self, instance_id: str, select_name: str | None = None) -> str:
        ping = ssm_ping_status(instance_id)
        if ping != "Online":
            raise RuntimeError(f"Toronado host not SSM Online ({ping})")
        result = run_powershell(instance_id, [PS_LIST_OMS_SERVICES], timeout_seconds=180)
        if result["status"] != "Success":
            raise RuntimeError(result["stderr"] or result["status"])
        raw = result["stdout"].strip()
        rows: list[dict[str, Any]] = []
        if raw:
            data = json.loads(raw)
            rows = [data] if isinstance(data, dict) else data
        self.after(0, lambda r=rows, s=select_name: self._fill_toro_tree(r, s))
        return f"Loaded {len(rows)} Toro service(s)."

    def _fill_toro_tree(self, rows: list[dict[str, Any]], select_name: str | None = None) -> None:
        filt = self._toro_filter.get().strip().lower()
        for item in self._toro_tree.get_children():
            self._toro_tree.delete(item)
        selected_iid = None
        for row in rows:
            name = str(row.get("Name", ""))
            if filt and filt not in name.lower():
                continue
            status = format_service_status(row.get("Status"))
            start = format_start_type(row.get("StartType"))
            tag = status_tag(status)
            iid = self._toro_tree.insert("", tk.END, values=(name, status, start), tags=(tag,) if tag else ())
            if select_name and name == select_name:
                selected_iid = iid
        if selected_iid:
            self._toro_tree.selection_set(selected_iid)
            self._toro_tree.focus(selected_iid)
            self._toro_tree.see(selected_iid)

    def _apply_toro_filter(self) -> None:
        stack = self._current_stack()
        toro = stack.host_by_role("toronado") if stack else None
        if toro:
            self._run_async("Reload Toro services", lambda: self._load_toro_services(toro.instance_id))

    def _selected_toro_service(self) -> str | None:
        sel = self._toro_tree.selection()
        if not sel:
            messagebox.showinfo("Select a service", "Choose an OMS service in the Toronado tab.")
            return None
        return str(self._toro_tree.item(sel[0], "values")[0])

    def _service_action(self, action: str) -> None:
        name = self._selected_toro_service()
        if not name:
            return
        stack = self._current_stack()
        toro = stack.host_by_role("toronado") if stack else None
        if not toro:
            return
        if not messagebox.askyesno("Confirm", f"{action.upper()} service?\n\n{name}\n\nHost: {toro.name_tag}"):
            return

        self._status.config(text=f"{action.capitalize()} in progress, then refreshing list...")
        self._log_line(f"Sending {action} to {name}...")

        def job():
            result = run_powershell(toro.instance_id, [ps_service_action(name, action)], timeout_seconds=120)
            if result["status"] != "Success":
                raise RuntimeError(result["stderr"] or result["stdout"] or result["status"])
            settle = run_powershell(
                toro.instance_id,
                [ps_wait_service_settle(name, seconds=5)],
                timeout_seconds=90,
            )
            status_line = (settle.get("stdout") or "").strip()
            reload_msg = self._load_toro_services(toro.instance_id, select_name=name)
            return f"{action} command sent.\n{status_line}\n{reload_msg}"

        self._run_async(f"{action} {name}", job)

    def _load_iis(self, instance_id: str) -> str:
        ping = ssm_ping_status(instance_id)
        if ping != "Online":
            raise RuntimeError(f"Site Manager host not SSM Online ({ping})")
        result = run_powershell(instance_id, [PS_LIST_IIS], timeout_seconds=180)
        if result["status"] != "Success":
            raise RuntimeError(result["stderr"] or result["status"])
        payload = json.loads(result["stdout"].strip())
        sites = payload.get("Sites") or []
        pools = {p["Name"]: p.get("State", "") for p in (payload.get("AppPools") or [])}
        if isinstance(sites, dict):
            sites = [sites]
        self._iis_sites = sites
        site_names = [s.get("Name", "") for s in sites]
        self.after(0, lambda: self._fill_iis_tree(sites, pools))
        self.after(0, lambda: self._log_site_combo.configure(values=site_names))
        if site_names:
            self.after(0, lambda: self._log_site_var.set(site_names[0]))
        return f"Loaded {len(sites)} IIS site(s)."

    def _fill_iis_tree(self, sites: list[dict], pools: dict[str, str]) -> None:
        for item in self._iis_tree.get_children():
            self._iis_tree.delete(item)
        for site in sites:
            pool = site.get("AppPool", "")
            self._iis_tree.insert(
                "",
                tk.END,
                values=(
                    site.get("Name", ""),
                    site.get("State", ""),
                    pool,
                    pools.get(pool, ""),
                    site.get("PhysicalPath", ""),
                ),
            )

    def _selected_iis_row(self) -> tuple[str, str, str] | None:
        sel = self._iis_tree.selection()
        if not sel:
            return None
        vals = self._iis_tree.item(sel[0], "values")
        return str(vals[0]), str(vals[2]), str(vals[4]) if len(vals) > 4 else ""

    def _iis_recycle_pool(self) -> None:
        row = self._selected_iis_row()
        if not row:
            messagebox.showinfo("Select a site", "Choose a row on the Site Manager tab.")
            return
        site, pool, _ = row
        stack = self._current_stack()
        sm = stack.host_by_role("sitemanager") if stack else None
        if not sm or not pool:
            return
        if not messagebox.askyesno("Confirm", f"Recycle app pool?\n\nPool: {pool}\nSite: {site}"):
            return

        def job():
            result = run_powershell(sm.instance_id, [ps_iis_recycle_pool(pool)], timeout_seconds=120)
            if result["status"] != "Success":
                raise RuntimeError(result["stderr"] or result["status"])
            return self._load_iis(sm.instance_id)

        self._run_async(f"Recycle {pool}", job)

    def _iis_site(self, action: str) -> None:
        row = self._selected_iis_row()
        if not row:
            messagebox.showinfo("Select a site", "Choose a row on the Site Manager tab.")
            return
        site, _, _ = row
        stack = self._current_stack()
        sm = stack.host_by_role("sitemanager") if stack else None
        if not sm:
            return
        if not messagebox.askyesno("Confirm", f"{action.upper()} IIS site?\n\n{site}"):
            return

        def job():
            result = run_powershell(sm.instance_id, [ps_iis_site_action(site, action)], timeout_seconds=180)
            if result["status"] != "Success":
                raise RuntimeError(result["stderr"] or result["status"])
            return self._load_iis(sm.instance_id)

        self._run_async(f"IIS {action} {site}", job)

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
            hosts.append(("Content server", content.instance_id))
        hosts.append(("Site Manager", sm.instance_id))

        def job():
            script = ps_tail_shoplogic_debug_bases(bases, lines=120)
            combined: list[str] = []
            for host_label, instance_id in hosts:
                combined.append(f"--- Trying {host_label} ({instance_id}) ---")
                result = run_powershell(instance_id, [script], timeout_seconds=180)
                if result["status"] != "Success":
                    combined.append(result["stderr"] or result["status"])
                    continue
                chunk = (result["stdout"] or "").strip()
                combined.append(chunk)
                if "=== Log file:" in chunk and "NO_LOG:" not in chunk.splitlines()[0]:
                    text = "\n".join(combined)
                    self.after(0, lambda t=text: self._show_log_view(t))
                    return f"ShopLogic log from {host_label}."
            text = "\n".join(combined)
            self.after(0, lambda t=text: self._show_log_view(t))
            return "ShopLogic log not found on SM or content; see paths tried in viewer."

        self._run_async("Tail ShopLogic log", job)

    def _tail_toro_log(self) -> None:
        name = self._selected_toro_service()
        if not name:
            return
        stack = self._current_stack()
        toro = stack.host_by_role("toronado") if stack else None
        if not toro:
            return

        def job():
            script = ps_tail_toro_logs(name)
            result = run_powershell(toro.instance_id, [script], timeout_seconds=120)
            if result["status"] != "Success":
                raise RuntimeError(result["stderr"] or result["status"])
            text = result["stdout"] or result["stderr"]
            self.after(0, lambda: self._show_log_view(text))
            return "Toro log tail loaded."

        self._run_async("Tail Toro log", job)

    def _refresh_cw_groups(self) -> None:
        self._cw_group_var.set("Refreshing...")

        def job():
            groups = list_shoplogic_api_log_groups(force_refresh=True)
            self._cw_groups = groups
            self.after(0, lambda: self._cw_combo.configure(values=groups))
            if groups:
                self.after(0, lambda: self._cw_group_var.set(groups[0]))
            else:
                self.after(0, lambda: self._cw_group_var.set(""))
            return f"Found {len(groups)} CloudWatch group(s)."

        self._run_async("List CloudWatch groups", job, use_lock=False)

    def _tail_cw_log(self) -> None:
        group = self._cw_group_var.get()
        if not group:
            messagebox.showinfo("Log group", "Refresh and select a CloudWatch log group.")
            return

        def job():
            text = tail_log_group(group, limit=100)
            self.after(0, lambda: self._show_log_view(text))
            return "CloudWatch tail loaded."

        self._run_async("Tail CloudWatch", job, use_lock=False)

    def _show_log_view(self, text: str) -> None:
        self._log_view.delete("1.0", tk.END)
        self._log_view.insert(tk.END, text)


def main() -> None:
    app = OpsGui()
    app.mainloop()


if __name__ == "__main__":
    main()
