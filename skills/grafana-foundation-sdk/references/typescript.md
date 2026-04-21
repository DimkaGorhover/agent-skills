# Grafana Foundation SDK — TypeScript/JavaScript Reference

## Installation

```bash
# yarn (recommended)
yarn add '@grafana/grafana-foundation-sdk@~v0.0.12'

# npm
npm install '@grafana/grafana-foundation-sdk@~v0.0.12'
```

## Import Paths

Each panel type and feature is a separate sub-path — import only what you need:

```typescript
// Dashboard builder
import { DashboardBuilder, RowBuilder } from '@grafana/grafana-foundation-sdk/dashboard';

// Panel builders — one sub-path per panel type
import { PanelBuilder as TimeseriesPanel } from '@grafana/grafana-foundation-sdk/timeseries';
import { PanelBuilder as StatPanel } from '@grafana/grafana-foundation-sdk/stat';
import { PanelBuilder as GaugePanel } from '@grafana/grafana-foundation-sdk/gauge';
import { PanelBuilder as TablePanel } from '@grafana/grafana-foundation-sdk/table';
import { PanelBuilder as TextPanel } from '@grafana/grafana-foundation-sdk/text';

// Query builders
import { DataqueryBuilder as PrometheusQuery } from '@grafana/grafana-foundation-sdk/prometheus';

// Variable builders
import {
    DatasourceVariableBuilder,
    QueryVariableBuilder,
    TextBoxVariableBuilder,
} from '@grafana/grafana-foundation-sdk/dashboard';

// Common types
import { VariableRefresh, VariableSort } from '@grafana/grafana-foundation-sdk/dashboard';
```

## Dashboard Builder

```typescript
const builder = new DashboardBuilder('Dashboard Title')
    .uid('my-dashboard-uid')
    .tags(['generated', 'my-team'])
    .editable()
    .refresh('30s')
    .time({ from: 'now-30m', to: 'now' })   // NOTE: object, not two strings
    .timezone('browser');

const dashboard = builder.build();
```

## Adding Rows and Panels

```typescript
const builder = new DashboardBuilder('My Dashboard')
    .withRow(new RowBuilder('Section Title'))
    .withPanel(
        new TimeseriesPanel()
            .title('Request Rate')
            .height(8)
            .span(12)   // 1-24 column grid
            .withTarget(
                new PrometheusQuery()
                    .expr('rate(http_requests_total[5m])')
                    .legendFormat('{{ handler }}'),
            ),
    );
```

## Panel Builder Common Methods

```typescript
const panel = new TimeseriesPanel()
    .title('Panel Title')
    .description('Optional description')
    .height(8)
    .span(12)
    .unit('short')      // "bytes", "bps", "percent", "s", etc.
    .min(0)
    .max(100)
    .datasource({ uid: '$datasource', type: 'prometheus' });
```

> **Note:** TypeScript uses `.min()` and `.max()` (no `_val` suffix), unlike Python.

## Timeseries Panel

```typescript
import {
    VizLegendOptions, LegendDisplayMode, LegendPlacement,
    VizTooltipOptions, TooltipDisplayMode,
} from '@grafana/grafana-foundation-sdk/common';

new TimeseriesPanel()
    .title('Request Rate')
    .unit('reqps')
    .lineWidth(2)
    .fillOpacity(30)
    .legend({
        displayMode: LegendDisplayMode.List,
        placement: LegendPlacement.Bottom,
    })
    .tooltip({ mode: TooltipDisplayMode.Single })
    .withTarget(
        new PrometheusQuery()
            .expr('rate(http_requests_total{job="myapp"}[5m])')
            .legendFormat('{{ handler }}'),
    )
```

## Stat Panel

```typescript
import { BigValueColorMode, BigValueGraphMode } from '@grafana/grafana-foundation-sdk/common';

new StatPanel()
    .title('Total Requests')
    .unit('short')
    .colorMode(BigValueColorMode.Background)
    .graphMode(BigValueGraphMode.Area)
    .withTarget(
        new PrometheusQuery()
            .expr('sum(http_requests_total)')
            .instant(),
    )
```

## Gauge Panel

```typescript
new GaugePanel()
    .title('CPU Usage')
    .unit('percent')
    .min(0)
    .max(100)
    .withTarget(
        new PrometheusQuery()
            .expr('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)')
            .instant(),
    )
```

## Table Panel

```typescript
import { PromQueryFormat } from '@grafana/grafana-foundation-sdk/prometheus';

new TablePanel()
    .title('Services')
    .withTarget(
        new PrometheusQuery()
            .expr('up{job="myapp"}')
            .instant()
            .format(PromQueryFormat.Table),
    )
```

## Variables

### Datasource Variable

```typescript
builder.withVariable(
    new DatasourceVariableBuilder('datasource')
        .label('Datasource')
        .type('prometheus')
        .regex(''),
);
```

### Query Variable

```typescript
builder.withVariable(
    new QueryVariableBuilder('cluster')
        .label('Cluster')
        .query('label_values(up, cluster)')
        .datasource({ uid: '$datasource' })
        .current({ selected: true, text: 'All', value: '$__all' })
        .refresh(VariableRefresh.OnTimeRangeChanged)
        .sort(VariableSort.AlphabeticalAsc)
        .multi(true)
        .includeAll(true)
        .allValue('.*'),
);
```

### Custom / Text Box Variable

```typescript
// TextBoxVariableBuilder is the TypeScript equivalent of CustomVariable in Python/Go
builder.withVariable(
    new TextBoxVariableBuilder('env')
        .label('Environment')
        .defaultValue('prod'),
);
```

> **Note:** TypeScript names this `TextBoxVariableBuilder`, while Go calls it `CustomVariableBuilder` and Python calls it `CustomVariable`.

## DataSource Reference Helper

```typescript
const datasourceRef = (uid: string, type = 'prometheus') => ({ uid, type });

// Usage on panel
new TimeseriesPanel().datasource(datasourceRef('$datasource'))
```

## Prometheus Query Builder

```typescript
new PrometheusQuery()
    .expr('rate(http_requests_total[5m])')
    .legendFormat('{{ handler }}')
    .refId('A')               // optional; auto-assigned A, B, C...
    .instant()                // instant query instead of range
    .format(PromQueryFormat.TimeSeries)  // or Table, Heatmap
```

## Manifest Output (Kubernetes-style)

```typescript
const dashboard = builder.build();

const manifest = {
    apiVersion: 'dashboard.grafana.app/v1beta1',
    kind: 'Dashboard',
    metadata: { name: dashboard.uid! },
    spec: dashboard,
};

console.log(JSON.stringify(manifest, null, 2));
```

## Custom Panel Extension

```typescript
import { Builder } from '@grafana/grafana-foundation-sdk/cog';
import { Panel } from '@grafana/grafana-foundation-sdk/dashboard';

interface CustomPanelOptions {
    myOption: string;
}

class CustomPanelBuilder implements Builder<Panel> {
    private panel: Panel;

    constructor() {
        this.panel = { type: 'my-custom-panel' } as Panel;
    }

    title(title: string): this {
        this.panel.title = title;
        return this;
    }

    build(): Panel {
        return this.panel;
    }
}

// Use like any other panel
builder.withPanel(new CustomPanelBuilder().title('Custom'));
```

## Custom Query Extension

```typescript
import { runtime } from '@grafana/grafana-foundation-sdk/cog';

// Register before building dashboards
runtime.registerCustomDataquery(
    'my-datasource',
    () => new MyDatasource.DataqueryBuilder(),
);
```

## JavaScript (CommonJS)

```javascript
const {
    DashboardBuilder,
    RowBuilder
} = require('@grafana/grafana-foundation-sdk/dashboard');
const {
    PanelBuilder
} = require('@grafana/grafana-foundation-sdk/timeseries');
const {
    DataqueryBuilder
} = require('@grafana/grafana-foundation-sdk/prometheus');

const builder = new DashboardBuilder('My Dashboard')
    .uid('my-dashboard')
    .time({
        from: 'now-30m',
        to: 'now'
    })
    .timezone('browser')
    .withRow(new RowBuilder('Overview'))
    .withPanel(
        new PanelBuilder()
        .title('Requests')
        .withTarget(
            new DataqueryBuilder().expr('rate(http_requests_total[5m])'),
        ),
    );

console.log(JSON.stringify(builder.build(), null, 2));
```

## API Reference Paths (in-repo docs)

- Dashboard builder: `typescript/docs/Reference/dashboard/builder-DashboardBuilder.md`
- Timeseries panel: `typescript/docs/Reference/timeseries/builder-PanelBuilder.md`
- Stat panel: `typescript/docs/Reference/stat/builder-PanelBuilder.md`
- Gauge panel: `typescript/docs/Reference/gauge/builder-PanelBuilder.md`
- Table panel: `typescript/docs/Reference/table/builder-PanelBuilder.md`
- Query variable: `typescript/docs/Reference/dashboard/builder-QueryVariableBuilder.md`
- Datasource variable: `typescript/docs/Reference/dashboardv2beta1/builder-DatasourceVariableBuilder.md`
- Text box variable: `typescript/docs/Reference/dashboard/builder-TextBoxVariableBuilder.md`
- Prometheus query: `typescript/docs/Reference/prometheus/builder-DataqueryBuilder.md`
