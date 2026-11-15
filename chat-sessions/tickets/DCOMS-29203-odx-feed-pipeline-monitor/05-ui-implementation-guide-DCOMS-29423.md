# UI Implementation Guide — DCOMS-29423 (React Shell)

How to build the ODX Feed Pipeline Monitor React shell so it looks and behaves like existing Site Manager pages (especially Service Manager).

**Ticket:** [DCOMS-29423](https://aptos.atlassian.net/browse/DCOMS-29423)  
**Pattern reference:** Service Manager (`ServiceManager.aspx` + `serviceManager/` module)

---

## Goal for Story 5

Deliver a **working backadmin entry point** that:

1. Loads under Site Manager master page
2. Mounts a React app in a dedicated div
3. Shows a placeholder until Stories 6–7 add real UI
4. Has axios wired to `OdxFeedMonitorController` (can stub until Story 4 merges)
5. Is reachable from backadmin navigation with proper auth

**Out of scope for Story 5:** Landing tiles, ag-Grid, detail timeline (Stories 6–7).

---

## Site Manager placement (from Story 6 spec — prepare nav now)

| Field | Value |
|-------|-------|
| Menu group | Feed Monitoring |
| Tab name | ODX feed pipeline |
| Page title | ODX feed pipeline |
| Description | Monitor OMS and ODX feed processing across queued, started, completed, staged, and file-output states. |
| Navigation path | Site Manager > Content > Tasks tab > ODX feed pipeline |
| Permission checkbox | Content > "ODX feed pipeline" (unchecked by default) |

Story 5 adds the page and nav link. Story 6 adds the permission checkbox enforcement.

---

## File checklist

### 1. ASPX host page

**Create:** `ShopVisible.Core.ShopLogic/backadmin/OdxFeedMonitor.aspx`

Mirror `ServiceManager.aspx`:

```aspx
<%@ Page Language="C#" AutoEventWireup="true" CodeFile="OdxFeedMonitor.aspx.cs"
    Inherits="backadmin_OdxFeedMonitor" Title="Aptos - ODX Feed Pipeline" MasterPageFile="~/backadmin/siteManager.master"%>

<asp:Content ID="PageHeaders" runat="server" ContentPlaceHolderID="Headers">
    <link rel="stylesheet" type="text/css" href="<% =GetReactCssPath() %>" />
</asp:Content>
<asp:Content ContentPlaceHolderID="mainContent" ID="odxFeedMonitorContent" runat="server">
    <div id="odxFeedMonitor"></div>
    <script type="text/javascript" src="<% =GetReactJsPath() %>"></script>
</asp:Content>
```

**Create:** `ShopVisible.Core.ShopLogic/backadmin/OdxFeedMonitor.aspx.cs`

```csharp
public partial class backadmin_OdxFeedMonitor : BaseCommonPage
{
    protected void Page_Load(object sender, EventArgs e)
    {
        base.validateSiteMgrUser();
    }
}
```

### 2. React entry registration

**Edit:** `Shopvisible.Core.Shoplogic.Frontend.React/src/index.js`

Add mount div detection and dynamic import:

```javascript
const odxFeedMonitorPage = document.getElementById('odxFeedMonitor');
// ...
} else if (odxFeedMonitorPage) {
    import('./app/OdxFeedMonitorApp').then(importedModule => moduleImport(importedModule, odxFeedMonitorPage));
}
```

### 3. App wrapper

**Create:** `Shopvisible.Core.Shoplogic.Frontend.React/src/app/OdxFeedMonitorApp.js`

```javascript
import React, { Component } from 'react';
import OdxFeedMonitor from '../odxFeedMonitor/OdxFeedMonitor';
import '../css/affiliateGroupCommon.css';

class OdxFeedMonitorApp extends Component {
  render() {
    return (
      <div className="oms-body" style={{ marginTop: '1rem' }}>
        <OdxFeedMonitor divId={this.props.divId} />
      </div>
    );
  }
}

export default OdxFeedMonitorApp;
```

### 4. Root component with placeholder

**Create:** `Shopvisible.Core.Shoplogic.Frontend.React/src/odxFeedMonitor/OdxFeedMonitor.js`

Follow `ServiceManager.js` state-machine pattern for future landing/detail routing:

```javascript
import React, { Component } from 'react';
import OdxFeedMonitorState from './OdxFeedMonitorState';
// Story 6: import OdxFeedMonitorLanding from './landing/OdxFeedMonitorLanding';
// Story 7: import OdxFeedMonitorDetail from './detail/OdxFeedMonitorDetail';

class OdxFeedMonitor extends Component {
  state = {
    pageState: OdxFeedMonitorState.landing,
    messageId: null,
  };

  render() {
    // Story 5: placeholder only
    return (
      <div>
        <h1>ODX feed pipeline</h1>
        <p>Monitor OMS and ODX feed processing across queued, started, completed, staged, and file-output states.</p>
        <p>ODX Feed Monitor — loading...</p>
      </div>
    );
  }

  changePage = (newPage, messageId) => {
    this.setState({ pageState: newPage, messageId });
  };
}

export default OdxFeedMonitor;
```

**Create:** `Shopvisible.Core.Shoplogic.Frontend.React/src/odxFeedMonitor/OdxFeedMonitorState.js`

```javascript
const OdxFeedMonitorState = {
  landing: 'landing',
  detail: 'detail',
};

export default OdxFeedMonitorState;
```

### 5. API module

**Create:** `Shopvisible.Core.Shoplogic.Frontend.React/src/api/odxFeedMonitorApi.js`

```javascript
import axios from 'axios';

const base = '/api/OdxFeedMonitor';

export const getSummary = (startUtc, endUtc) =>
  axios.get(`${base}/summary`, { params: { startUtc, endUtc } });

export const getBacklog = (startUtc, endUtc, page, pageSize) =>
  axios.get(`${base}/backlog`, { params: { startUtc, endUtc, page, pageSize } });

export const getStuckOrders = (thresholdHours) =>
  axios.get(`${base}/stuckorders`, { params: { thresholdHours } });

export const getErrors = (startUtc, endUtc, limit) =>
  axios.get(`${base}/errors`, { params: { startUtc, endUtc, limit } });

export const getTimeline = (messageId) =>
  axios.get(`${base}/timeline/${messageId}`);

export const searchByReference = (referenceId, startUtc, endUtc, page, pageSize) =>
  axios.get(`${base}/search`, { params: { referenceId, startUtc, endUtc, page, pageSize } });
```

Wire a health-check call in `componentDidMount` once Story 4 is available. Until then, catch 404 gracefully in the placeholder.

### 6. Navigation link

Add menu entry in the same location Service Manager appears under Content > Tasks. Search the codebase for `ServiceManager.aspx` references in navigation config (likely `content.aspx`, menu XML, or database-driven nav).

---

## Visual design — match Service Manager

### Layout patterns from Service Manager

| Element | Service Manager | ODX Monitor (Story 6) |
|---------|-----------------|------------------------|
| Page title | `<h1>Service Manager</h1>` | `<h1>ODX feed pipeline</h1>` |
| Primary action | "Configure Service" button | Time window selector |
| Main content | ag-Grid (`ag-theme-aptos`) | ag-Grid for search results |
| Grid theme | `agThemeAptos.css` | Same |
| Wrapper class | `oms-body` | Same |
| State routing | `ServiceManagerState` enum | `OdxFeedMonitorState` enum |
| Pagination | 10 rows per page | Server-side pagination |
| Filters | `floatingFilter={true}` | Search bar + floating filters |

### CSS to reuse

- `src/css/affiliateGroupCommon.css` — shared backadmin React styles
- `src/css/ag-grid/agThemeAptos.css` — grid theme
- Bootstrap classes from `node_modules/bootstrap`
- Site Manager master styles: `sitemanager2015.css`, `backend.css`

### Do NOT introduce

- New font families (Site Manager uses Roboto from Google Fonts via master page)
- Purple gradients or non-Aptos colour schemes
- React Router (existing pages use component state switching)

---

## Landing page preview (Story 6 — plan ahead)

Based on epic mockups and Story 6 spec, the landing page will have:

```
┌─────────────────────────────────────────────────────────────┐
│ ODX feed pipeline                    [Time window: 24h ▼]    │
│ Monitor OMS and ODX feed processing...                        │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │Fulfillment│ │OrderCreated│ │Inventory │ │Export...│  ← tiles│
│ │ Q:120 S:118│ │ Q:45 D:44 │ │ Q:10 D:9 │ │ ...     │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├──────────────────┬──────────────────┬─────────────────────────┤
│ Backlog (42)     │ Stuck orders (3) │ Recent errors (5)       │
│ [message list]   │ [order IDs]      │ [error summaries]       │
├─────────────────────────────────────────────────────────────┤
│ Search: [order ID / message ID / task name        ] [Go]   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ag-Grid: MessageId | Task | Order | Status | Queued At │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

Story 5 only needs the title + description + placeholder. Story 6 fills in the panels.

---

## Detail page preview (Story 7)

Vertical timeline:

```
Queued ────● 2025-12-18 16:35:29 UTC
Started ───● 2025-12-18 16:35:31 UTC
Done ──────● 2025-12-18 16:35:45 UTC (Success)
Staged ────● 2025-12-18 16:36:00 UTC (omsfeedexport)
File Written ● 2025-12-18 16:40:00 UTC
```

Missing stages show "Pending" or "Not reached".

---

## Acceptance criteria mapping (DCOMS-29423)

| AC | How to verify |
|----|---------------|
| AC1 — Page accessible from backadmin navigation | Log in to backadmin, click ODX feed pipeline menu item, React renders placeholder |
| AC2 — Unauthenticated access blocked | Direct URL without login redirects to login page |

---

## Build and test

1. Build React bundle: follow existing `Shoplogic.Frontend.React` build process
2. Deploy to staging backadmin
3. Navigate to `/backadmin/OdxFeedMonitor.aspx`
4. Confirm `mainReact.js` loads and placeholder renders inside Site Manager chrome
5. Confirm no console errors

---

## Files to reference (existing)

| File | Why |
|------|-----|
| `backadmin/ServiceManager.aspx` | ASPX shell template |
| `src/app/ServiceManagerApp.js` | App wrapper pattern |
| `src/serviceManager/ServiceManager.js` | State-based page routing |
| `src/serviceManager/landingPage/ServiceManagerLanding.js` | ag-Grid landing pattern |
| `src/serviceManager/landingPage/ServiceManagerLandingUi.js` | Grid UI rendering |
| `src/api/serviceManagerApi.js` | Axios API module pattern |
| `DCEOM.WebApi/TaskSchedulerViewController.cs` | Web API auth pattern (`[ClientSideAuthorization]`) |
