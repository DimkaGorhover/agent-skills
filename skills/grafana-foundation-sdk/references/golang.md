# Grafana Foundation SDK — Go Reference

## Installation

```bash
go get github.com/grafana/grafana-foundation-sdk/go@v0.0.12
```

## Import Paths

```go
import (
	"github.com/grafana/grafana-foundation-sdk/go/common"
	"github.com/grafana/grafana-foundation-sdk/go/dashboard"
	"github.com/grafana/grafana-foundation-sdk/go/prometheus"

	// Panel sub-packages — one per panel type
	"github.com/grafana/grafana-foundation-sdk/go/gauge"
	"github.com/grafana/grafana-foundation-sdk/go/stat"
	"github.com/grafana/grafana-foundation-sdk/go/table"
	"github.com/grafana/grafana-foundation-sdk/go/text"
	"github.com/grafana/grafana-foundation-sdk/go/timeseries"

	// Manifest output (Kubernetes-style)
	"github.com/grafana/grafana-foundation-sdk/go/resource"
)
```

## Dashboard Builder

```go
builder := dashboard.NewDashboardBuilder("Dashboard Title").
	Uid("my-dashboard-uid").
	Tags([]string{"generated", "my-team"}).
	Editable().
	Refresh("30s").
	Time("now-30m", "now").
	Timezone(common.TimeZoneBrowser).
	Tooltip(dashboard.DashboardCursorSyncOff)

d, err := builder.Build()
```

## Adding Rows and Panels

```go
builder.
	WithRow(dashboard.NewRowBuilder("Section Title")).
	WithPanel(
		timeseries.NewPanelBuilder().
			Title("My Panel").
			Height(8).
			Span(12). // 1-24 column grid
			WithTarget(
				prometheus.NewDataqueryBuilder().
					Expr(`rate(http_requests_total[5m])`).
					LegendFormat("{{ handler }}"),
			),
	)
```

## Panel Builder Common Methods

All panel builders share these methods:

```go
panel := timeseries.NewPanelBuilder().
	Title("Panel Title").
	Description("Optional description").
	Height(8).     // rows tall
	Span(12).      // columns wide (1-24)
	Unit("short"). // unit for Y-axis: "bytes", "bps", "percent", "s", etc.
	Min(0).
	Max(100).
	Datasource(dashboard.DataSourceRef{
		Type: &datasourceType, // e.g. "prometheus"
		Uid:  &datasourceUid,  // e.g. "$datasource"
	})
```

## Timeseries Panel

```go
timeseries.NewPanelBuilder().
	Title("Request Rate").
	Unit("reqps").
	LineWidth(2).
	FillOpacity(30).
	Legend(common.VizLegendOptions{
		DisplayMode: common.LegendDisplayModeList,
		Placement:   common.LegendPlacementBottom,
	}).
	Tooltip(common.VizTooltipOptions{Mode: common.TooltipDisplayModeSingle}).
	WithTarget(
		prometheus.NewDataqueryBuilder().
			Expr(`rate(http_requests_total{job="myapp"}[5m])`).
			LegendFormat("{{ handler }}"),
	)
```

## Stat Panel

```go
stat.NewPanelBuilder().
	Title("Total Requests").
	Unit("short").
	ColorMode(common.BigValueColorModeBackground).
	GraphMode(common.BigValueGraphModeArea).
	WithTarget(
		prometheus.NewDataqueryBuilder().
			Expr(`sum(http_requests_total)`).
			Instant(),
	)
```

## Gauge Panel

```go
gauge.NewPanelBuilder().
	Title("CPU Usage").
	Unit("percent").
	Min(0).
	Max(100).
	WithTarget(
		prometheus.NewDataqueryBuilder().
			Expr(`100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)`).
			Instant(),
	)
```

## Table Panel

```go
table.NewPanelBuilder().
	Title("Services").
	WithTarget(
		prometheus.NewDataqueryBuilder().
			Expr(`up{job="myapp"}`).
			Instant().
			Format(prometheus.PromQueryFormatTable),
	)
```

## Variables

### Datasource Variable

```go
dsType := "prometheus"
builder.WithVariable(
	dashboard.NewDatasourceVariableBuilder("datasource").
		Label("Datasource").
		Type(dsType).
		Regex(""),
)
```

### Query Variable

```go
builder.WithVariable(
    dashboard.NewQueryVariableBuilder("cluster").
        Label("Cluster").
        Query(dashboard.StringOrAny{String: &queryStr}). // queryStr = `label_values(up, cluster)`
        Datasource(dashboard.DataSourceRef{Uid: &dsUid}).
        Current(dashboard.VariableOption{Selected: &trueVal, Text: ..., Value: ...}).
        Refresh(dashboard.VariableRefreshOnTimeRangeChanged).
        Sort(dashboard.VariableSortAlphabeticalAsc).
        Multi(true).
        IncludeAll(true).
        AllValue(".*"),
)
```

### Custom Variable

```go
builder.WithVariable(
    dashboard.NewCustomVariableBuilder("env").
        Label("Environment").
        Query("prod,staging,dev").
        Current(dashboard.VariableOption{...}),
)
```

## DataSource Reference Helper

```go
func datasourceRef(uid string) dashboard.DataSourceRef {
    dsType := "prometheus"
    return dashboard.DataSourceRef{
        Type: &dsType,
        Uid:  &uid,
    }
}

// Usage on panel
timeseries.NewPanelBuilder().
    Datasource(datasourceRef("$datasource"))
```

## Prometheus Query Builder

```go
prometheus.NewDataqueryBuilder().
	Expr(`rate(http_requests_total[5m])`).
	LegendFormat("{{ handler }}").
	RefId("A").                                  // optional; defaults to A, B, C...
	Instant().                                   // instant query instead of range
	Format(prometheus.PromQueryFormatTimeSeries) // or Table, Heatmap
```

## Manifest Output (Kubernetes-style)

```go
import "github.com/grafana/grafana-foundation-sdk/go/resource"

d, _ := builder.Build()

manifest := resource.Manifest{
    ApiVersion: "dashboard.grafana.app/v1beta1",
    Kind:       resource.DashboardKind,
    Metadata: resource.ObjectMeta{
        Name: *d.Uid,
    },
    Spec: d,
}

b, _ := json.MarshalIndent(manifest, "", "  ")
fmt.Println(string(b))
```

## Custom Panel Extension

```go
// 1. Define the panel options type
type CustomPanelOptions struct {
    MyOption string `json:"myOption"`
}

// 2. Implement cog.Builder[dashboard.Panel]
type CustomPanelBuilder struct {
    internal *dashboard.Panel
}

func NewCustomPanelBuilder() *CustomPanelBuilder {
    return &CustomPanelBuilder{
        internal: &dashboard.Panel{Type: "my-custom-panel"},
    }
}

func (b *CustomPanelBuilder) Build() (dashboard.Panel, error) {
    return *b.internal, nil
}

// 3. Use like any other panel
builder.WithPanel(NewCustomPanelBuilder().Title("Custom"))
```

## Custom Query Extension

```go
// Register before building dashboards
cog.RegisterCustomDataquery("my-datasource", func() cog.Builder[variants.Dataquery] {
	return myDatasource.NewDataqueryBuilder()
})
```

## Output JSON

```go
d, err := builder.Build()
if err != nil {
	log.Fatal(err)
}
b, err := json.MarshalIndent(d, "", "  ")
if err != nil {
	log.Fatal(err)
}
fmt.Println(string(b))
```

## API Reference Paths (in-repo docs)

- Dashboard builder: `go/docs/Reference/dashboard/builder-DashboardBuilder.md`
- Timeseries panel: `go/docs/Reference/timeseries/builder-PanelBuilder.md`
- Stat panel: `go/docs/Reference/stat/builder-PanelBuilder.md`
- Gauge panel: `go/docs/Reference/gauge/builder-PanelBuilder.md`
- Table panel: `go/docs/Reference/table/builder-PanelBuilder.md`
- Query variable: `go/docs/Reference/dashboardv2beta1/builder-QueryVariableBuilder.md`
- Datasource variable: `go/docs/Reference/dashboardv2beta1/builder-DatasourceVariableBuilder.md`
- Prometheus query: `go/docs/Reference/prometheus/builder-DataqueryBuilder.md`
