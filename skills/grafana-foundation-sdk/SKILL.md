---
name: grafana-foundation-sdk
description: Use when building Grafana dashboards programmatically with grafana-foundation-sdk in Go, Python, or TypeScript. Triggers on dashboard-as-code, builder pattern, panels, variables, datasource refs, Prometheus queries, or manifest output.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Grafana Foundation SDK

Strongly typed builder libraries for generating Grafana dashboard JSON from code.
Supports Go, Python, and TypeScript/JavaScript. Targets Grafana 10+ (optimized for 12+).

## When to Use

- Building or generating Grafana dashboards as code
- Creating panels (timeseries, stat, gauge, table, text) programmatically
- Configuring datasource variables, query variables, or custom variables
- Adding Prometheus (or other datasource) targets to panels
- Outputting Kubernetes-style `dashboard.grafana.app/v1beta1` manifests
- Extending the SDK with custom panels or custom query types

## When NOT to Use

- Editing existing dashboard JSON directly — use the Grafana UI or raw JSON
- Grafana plugin development (separate SDK: `@grafana/plugin-tools`)
- Alerting rules unrelated to dashboard composition

## Core Concepts

| Concept             | Description                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Builder pattern** | Every object is constructed via a chainable builder — `NewDashboardBuilder(...)`, `timeseries.NewPanelBuilder()` |
| **Rows**            | Group panels into labelled sections with `WithRow` / `with_row` / `.withRow`                                     |
| **Panel builders**  | `timeseries`, `stat`, `gauge`, `table`, `text` — each is a separate sub-package/module                           |
| **Targets**         | Queries attached to panels via `WithTarget` / `with_target` / `.withTarget`                                      |
| **Variables**       | `DatasourceVariable`, `QueryVariable`, `CustomVariable` — scoped to dashboard                                    |
| **DataSourceRef**   | Pointer to a datasource UID, used on panels and query variables                                                  |
| **Manifest output** | Wrap the built dashboard in `resource.Manifest` (Go) or `Manifest` (Python/TS) for GitOps                        |

## Quick Reference

### Installation

| Language   | Command                                                       |
| ---------- | ------------------------------------------------------------- |
| Go         | `go get github.com/grafana/grafana-foundation-sdk/go@v0.0.12` |
| Python     | `python3 -m pip install 'grafana_foundation_sdk==v0.0.12'`    |
| TypeScript | `yarn add '@grafana/grafana-foundation-sdk@~v0.0.12'`         |

### Dashboard Builder Methods (all languages)

| Method       | Go                                  | Python                   | TypeScript             |
| ------------ | ----------------------------------- | ------------------------ | ---------------------- |
| Set UID      | `.Uid("...")`                       | `.uid("...")`            | `.uid("...")`          |
| Add tags     | `.Tags([]string{...})`              | `.tags([...])`           | `.tags([...])`         |
| Set refresh  | `.Refresh("1m")`                    | `.refresh("1m")`         | `.refresh("1m")`       |
| Time range   | `.Time("now-30m","now")`            | `.time("now-30m","now")` | `.time({from,to})`     |
| Timezone     | `.Timezone(common.TimeZoneBrowser)` | `.timezone("browser")`   | `.timezone("browser")` |
| Add row      | `.WithRow(...)`                     | `.with_row(...)`         | `.withRow(...)`        |
| Add panel    | `.WithPanel(...)`                   | `.with_panel(...)`       | `.withPanel(...)`      |
| Add variable | `.WithVariable(...)`                | `.with_variable(...)`    | `.withVariable(...)`   |

### Panel Builders

| Panel type  | Go import path  | Python builder              | TypeScript import                            |
| ----------- | --------------- | --------------------------- | -------------------------------------------- |
| Time series | `go/timeseries` | `builders.timeseries.Panel` | `@grafana/grafana-foundation-sdk/timeseries` |
| Stat        | `go/stat`       | `builders.stat.Panel`       | `@grafana/grafana-foundation-sdk/stat`       |
| Gauge       | `go/gauge`      | `builders.gauge.Panel`      | `@grafana/grafana-foundation-sdk/gauge`      |
| Table       | `go/table`      | `builders.table.Panel`      | `@grafana/grafana-foundation-sdk/table`      |
| Text        | `go/text`       | `builders.text.Panel`       | `@grafana/grafana-foundation-sdk/text`       |

### Variable Builders

| Variable type       | Go                                     | Python                                 | TypeScript                              |
| ------------------- | -------------------------------------- | -------------------------------------- | --------------------------------------- |
| Datasource          | `NewDatasourceVariableBuilder("name")` | `dashboard.DatasourceVariable("name")` | `new DatasourceVariableBuilder("name")` |
| Query               | `NewQueryVariableBuilder("name")`      | `dashboard.QueryVariable("name")`      | `new QueryVariableBuilder("name")`      |
| Custom (fixed list) | `NewCustomVariableBuilder("name")`     | `dashboard.CustomVariable("name")`     | `new CustomVariableBuilder("name")`     |
| TextBox (free text) | `NewTextBoxVariableBuilder("name")`    | `dashboard.TextBoxVariable("name")`    | `new TextBoxVariableBuilder("name")`    |

## Minimal Dashboard Example (Go)

```go
package main

import (
	"encoding/json"
	"fmt"

	"github.com/grafana/grafana-foundation-sdk/go/common"
	"github.com/grafana/grafana-foundation-sdk/go/dashboard"
	"github.com/grafana/grafana-foundation-sdk/go/prometheus"
	"github.com/grafana/grafana-foundation-sdk/go/timeseries"
)

func main() {
	builder := dashboard.NewDashboardBuilder("My Dashboard").
		Uid("my-dashboard").
		Tags([]string{"generated"}).
		Refresh("1m").
		Time("now-30m", "now").
		Timezone(common.TimeZoneBrowser).
		WithRow(dashboard.NewRowBuilder("Overview")).
		WithPanel(
			timeseries.NewPanelBuilder().
				Title("Request Rate").
				WithTarget(
					prometheus.NewDataqueryBuilder().
						Expr(`rate(http_requests_total[5m])`).
						LegendFormat("{{ handler }}"),
				),
		)

	d, err := builder.Build()
	if err != nil {
		panic(err)
	}
	b, _ := json.MarshalIndent(d, "", "  ")
	fmt.Println(string(b))
}
```

## Common Mistakes

| Mistake                                | Fix                                                                                                                                                 |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Importing `go/dashboard` for panels    | Each panel type is its own sub-package: `go/timeseries`, `go/stat`, etc.                                                                            |
| Using Python `min()` built-in conflict | Panel method is `.min_val(0)` in Python, not `.min(0)`                                                                                              |
| TypeScript time range as string        | Must be `{ from: "now-30m", to: "now" }` object, not a string pair                                                                                  |
| Manifest missing `kind` field          | Always set `kind: "Dashboard"` (or use the `resource.DashboardKind` constant in Go)                                                                 |
| Variable not appearing on dashboard    | Must call `.WithVariable(...)` on the dashboard builder, not the panel                                                                              |
| Panels with no explicit grid position  | Always call `.Height(h).Span(w)` (Go/TS) or `.height(h).span(w)` (Python) — omitting these produces broken layouts where panels overlap or collapse |
| Silently discarding `Build()` errors   | Use `d, err := builder.Build(); if err != nil { panic(err) }` — silent `_` discard hides validation failures                                        |

## Datasource Wiring

Always wire a datasource ref to panels that query data. Use a template variable (`$datasource`) so the
dashboard respects the variable selector.

**Go:**

```go
dsType := "prometheus"
dsUid := "$datasource"
ref := dashboard.DataSourceRef{Type: &dsType, Uid: &dsUid}

timeseries.NewPanelBuilder().
	Datasource(ref).
	WithTarget(prometheus.NewDataqueryBuilder().Expr(`...`))
```

**Python:**

```python
from grafana_foundation_sdk.models.dashboard import DataSourceRef

ref = DataSourceRef(type_val="prometheus", uid="$datasource")

Timeseries().datasource(ref).with_target(PrometheusQuery().expr("..."))
```

**TypeScript:**

```typescript
const ref = { uid: '$datasource', type: 'prometheus' };

new TimeseriesPanel().datasource(ref).withTarget(new PrometheusQuery().expr('...'));
```

## Language-Specific References

Detailed API patterns, import paths, and full examples for each language:

- **Go** → `references/golang.md`
- **Python** → `references/python.md`
- **TypeScript/JavaScript** → `references/typescript.md`
