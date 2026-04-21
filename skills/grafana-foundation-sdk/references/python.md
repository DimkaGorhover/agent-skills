# Grafana Foundation SDK — Python Reference

## Installation

```bash
python3 -m pip install 'grafana_foundation_sdk==v0.0.12'
```

> PyPI distribution name: `grafana-foundation-sdk` — pip normalizes hyphens/underscores.
> Import name: `grafana_foundation_sdk` (underscores).
> Requires Python ≥ 3.11.

## Import Paths

```python
# Dashboard builder + variable builders (all in builders.dashboard)
from grafana_foundation_sdk.builders import dashboard
from grafana_foundation_sdk.builders.dashboard import Dashboard, Row

# Panel builders — one module per panel type
from grafana_foundation_sdk.builders.timeseries import Panel as Timeseries
from grafana_foundation_sdk.builders.stat import Panel as Stat
from grafana_foundation_sdk.builders.gauge import Panel as Gauge
from grafana_foundation_sdk.builders.table import Panel as Table
from grafana_foundation_sdk.builders.text import Panel as Text

# Query builders
from grafana_foundation_sdk.builders.prometheus import Dataquery as PrometheusQuery

# Models (data classes, enums — NOT builders)
from grafana_foundation_sdk.models.common import TimeZoneBrowser
from grafana_foundation_sdk.models.dashboard import (
    DataSourceRef,
    VariableOption,
    VariableRefresh,
    VariableSort,
)

# Manifest output
from grafana_foundation_sdk.cog.encoder import JSONEncoder
from grafana_foundation_sdk.models.resource import Manifest, Metadata, DashboardKind
```

## Dashboard Builder

```python
builder = (
    Dashboard("Dashboard Title")
    .uid("my-dashboard-uid")
    .tags(["generated", "my-team"])
    .editable()
    .refresh("30s")
    .time("now-30m", "now")
    .timezone("browser")  # or TimeZoneBrowser constant
)

dashboard = builder.build()
```

## Adding Rows and Panels

```python
builder = (
    Dashboard("My Dashboard")
    .with_row(Row("Section Title"))
    .with_panel(
        Timeseries()
        .title("Request Rate")
        .height(8)
        .span(12)  # 1-24 column grid
        .with_target(
            PrometheusQuery()
            .expr("rate(http_requests_total[5m])")
            .legend_format("{{ handler }}")
        )
    )
)
```

## Panel Builder Common Methods

```python
panel = Timeseries()
panel.title("Panel Title")
panel.description("Optional description")
panel.height(8)
panel.span(12)
panel.unit("short")  # "bytes", "bps", "percent", "s", etc.
panel.min_val(0)  # NOTE: min_val, NOT min() — avoids conflict with Python built-in
panel.max_val(100)
panel.datasource(DataSourceRef(uid="$datasource", type_val="prometheus"))
```

> **Important:** Python uses `.min_val()` and `.max_val()` instead of `.min()` / `.max()` to avoid shadowing Python built-ins.

## Timeseries Panel

```python
from grafana_foundation_sdk.models.common import (
    VizLegendOptions, LegendDisplayMode, LegendPlacement,
    VizTooltipOptions, TooltipDisplayMode,
)

Timeseries()
.title("Request Rate")
.unit("reqps")
.line_width(2)
.fill_opacity(30)
.legend(VizLegendOptions(
    display_mode=LegendDisplayMode.LIST,
    placement=LegendPlacement.BOTTOM,
))
.tooltip(VizTooltipOptions(mode=TooltipDisplayMode.SINGLE))
.with_target(
    PrometheusQuery()
    .expr('rate(http_requests_total{job="myapp"}[5m])')
    .legend_format("{{ handler }}")
)
```

## Stat Panel

```python
from grafana_foundation_sdk.builders.stat import Panel as Stat
from grafana_foundation_sdk.models.common import BigValueColorMode, BigValueGraphMode

Stat()
.title("Total Requests")
.unit("short")
.color_mode(BigValueColorMode.BACKGROUND)
.graph_mode(BigValueGraphMode.AREA)
.with_target(
    PrometheusQuery()
    .expr('sum(http_requests_total)')
    .instant()
)
```

## Gauge Panel

```python
from grafana_foundation_sdk.builders.gauge import Panel as Gauge

Gauge()
.title("CPU Usage")
.unit("percent")
.min_val(0)
.max_val(100)
.with_target(
    PrometheusQuery()
    .expr('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)')
    .instant()
)
```

## Table Panel

```python
from grafana_foundation_sdk.builders.table import Panel as Table
from grafana_foundation_sdk.models.prometheus import PromQueryFormat

Table()
.title("Services")
.with_target(
    PrometheusQuery()
    .expr('up{job="myapp"}')
    .instant()
    .format_val(PromQueryFormat.TABLE)
)
```

## Variables

### Datasource Variable

```python
builder.with_variable(
    dashboard.DatasourceVariable("datasource")
    .label("Datasource")
    .type("prometheus")
    .regex("")
)
```

### Query Variable

```python
from grafana_foundation_sdk.models.dashboard import (
    VariableOption,
    VariableRefresh,
    VariableSort,
    DataSourceRef,
)

builder.with_variable(
    dashboard.QueryVariable("cluster")
    .label("Cluster")
    .query("label_values(up, cluster)")
    .datasource(DataSourceRef(uid="$datasource"))
    .current(VariableOption(selected=True, text="All", value="$__all"))
    .refresh(VariableRefresh.ON_TIME_RANGE_CHANGED)
    .sort(VariableSort.ALPHABETICAL_ASC)
    .multi(True)
    .include_all(True)
    .all_value(".*")
)
```

### Custom Variable (fixed list)

```python
builder.with_variable(
    dashboard.CustomVariable("env")
    .label("Environment")
    .query("prod,staging,dev")
    .current(VariableOption(selected=True, text="prod", value="prod"))
)
```

### TextBox Variable (free text)

```python
builder.with_variable(
    dashboard.TextBoxVariable("search")
    .label("Search")
    .current(VariableOption(selected=False, text="", value=""))
)
```

## DataSource Reference Helper

```python
def datasource_ref(uid: str, ds_type: str = "prometheus") -> DataSourceRef:
    return DataSourceRef(uid=uid, type_val=ds_type)


# Usage on panel
Timeseries().datasource(datasource_ref("$datasource"))
```

## Prometheus Query Builder

```python
PrometheusQuery()
.expr('rate(http_requests_total[5m])')
.legend_format("{{ handler }}")
.ref_id("A")           # optional; defaults A, B, C...
.instant()             # instant query instead of range
.format_val(PromQueryFormat.TIME_SERIES)  # or TABLE, HEATMAP
```

## Manifest Output (Kubernetes-style)

```python
from grafana_foundation_sdk.cog.encoder import JSONEncoder
from grafana_foundation_sdk.models.resource import Manifest, Metadata, DashboardKind

dashboard_obj = builder.build()

manifest = Manifest(
    api_version="dashboard.grafana.app/v1beta1",
    kind=DashboardKind,
    metadata=Metadata(name=dashboard_obj.uid),
    spec=dashboard_obj,
)

print(JSONEncoder(sort_keys=True, indent=2).encode(manifest))
```

## Custom Panel Extension

```python
from grafana_foundation_sdk.cog import Builder
from grafana_foundation_sdk.models import dashboard


class CustomPanelBuilder(Builder[dashboard.Panel]):
    def __init__(self):
        self._panel = dashboard.Panel(type_val="my-custom-panel")

    def title(self, title: str) -> "CustomPanelBuilder":
        self._panel.title = title
        return self

    def build(self) -> dashboard.Panel:
        return self._panel


# Use like any other panel
builder.with_panel(CustomPanelBuilder().title("Custom"))
```

## Custom Query Extension

```python
from grafana_foundation_sdk.cog import runtime

# Register before building dashboards
runtime.register_custom_dataquery(
    "my-datasource", lambda: my_datasource.DataqueryBuilder()
)
```

## JSON Output

```python
import json
from grafana_foundation_sdk.cog.encoder import JSONEncoder

dashboard = builder.build()

# Option 1: cog encoder (handles custom types)
print(JSONEncoder(sort_keys=True, indent=2).encode(dashboard))

# Option 2: stdlib json (for simple dashboards)
print(json.dumps(dashboard.__dict__, indent=2))
```

## API Reference Paths (in-repo docs)

- Dashboard builder: `python/docs/Reference/dashboard/builder-Dashboard.md`
- Timeseries panel: `python/docs/Reference/timeseries/builder-Panel.md`
- Stat panel: `python/docs/Reference/stat/builder-Panel.md`
- Gauge panel: `python/docs/Reference/gauge/builder-Panel.md`
- Table panel: `python/docs/Reference/table/builder-Panel.md`
- Query variable: `python/docs/Reference/dashboardv2beta1/builder-QueryVariable.md`
- Datasource variable: `python/docs/Reference/dashboardv2beta1/builder-DatasourceVariable.md`
- Prometheus query: `python/docs/Reference/prometheus/builder-Dataquery.md`
