---
name: cli-aws-ce
description: >
  Use when querying AWS Cost Explorer with the `aws ce` CLI — cost and usage reports, forecasts,
  anomaly detection, savings plans coverage, reservation utilization, rightsizing recommendations,
  and filtering/grouping costs by service, account, tag, region, or instance type.
metadata:
  author: d.horkhover
  version: 1.2.0
---

# aws ce — AWS Cost Explorer CLI

## Overview

`aws ce` is the AWS CLI service for the [Cost Explorer API](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/). The API endpoint is always `ce.us-east-1.amazonaws.com` regardless of your `--region` flag.

> **API cost**: Each `aws ce` API call costs $0.01. Avoid calling in tight loops — cache results.

> **Data freshness**: CE data has a 24–48 hour lag. Current-day data is unavailable. Yesterday's data may still be processing — treat D-2 as the last reliably complete day.

> **Write commands exist**: `create-anomaly-monitor`, `create-anomaly-subscription`, `create-cost-category-definition`, `delete-*`, `update-*`, `tag-resource`, `untag-resource` are all in the `aws ce` namespace. This skill covers **read-only** usage only.

## When to Use

- Querying historical AWS costs and usage by service, account, tag, region, or instance type
- Generating cost forecasts (DAILY up to 3 months, MONTHLY up to 18 months)
- Detecting cost anomalies and reviewing anomaly monitors
- Checking Savings Plans coverage and utilization
- Reviewing Reserved Instance coverage, utilization, and purchase recommendations
- Getting rightsizing recommendations for EC2
- Discovering valid dimension values for filter building

## When NOT to Use

- Setting AWS Budgets (use `aws budgets` instead)
- Real-time billing (CE data lags 24–48 hours; use AWS Cost Anomaly Detection alerts instead)
- Sub-hourly granularity (HOURLY is the finest for `get-cost-and-usage`)
- Querying individual resource line items at scale (use Cost & Usage Reports S3 export instead)
- Mutating anomaly monitors, subscriptions, or cost categories (this skill is read-only)

## Quick Reference: Read-Only Commands

| Command                                     | Purpose                                                                  |
| ------------------------------------------- | ------------------------------------------------------------------------ |
| `get-cost-and-usage`                        | Cost/usage by dimensions, with grouping                                  |
| `get-cost-and-usage-with-resources`         | Resource-level breakdown; requires HOURLY + resource filter; higher cost |
| `get-cost-forecast`                         | Predict future costs (DAILY/MONTHLY)                                     |
| `get-usage-forecast`                        | Predict future usage quantity                                            |
| `get-dimension-values`                      | List valid values for a dimension key                                    |
| `get-tags`                                  | List cost allocation tag keys/values                                     |
| `get-cost-categories`                       | List cost category names/values                                          |
| `get-anomalies`                             | List detected cost anomalies                                             |
| `get-anomaly-monitors`                      | List anomaly monitor configurations                                      |
| `get-anomaly-subscriptions`                 | List anomaly alert subscriptions                                         |
| `get-rightsizing-recommendation`            | EC2 rightsizing recommendations                                          |
| `get-reservation-coverage`                  | RI coverage for compute spend                                            |
| `get-reservation-utilization`               | RI utilization rates                                                     |
| `get-reservation-purchase-recommendation`   | Recommended RI purchases                                                 |
| `get-savings-plans-coverage`                | Savings Plans coverage for eligible spend                                |
| `get-savings-plans-utilization`             | Savings Plans utilization rates                                          |
| `get-savings-plans-utilization-details`     | Per-plan utilization details                                             |
| `get-savings-plans-purchase-recommendation` | Recommended SP purchases                                                 |
| `describe-cost-category-definition`         | Get a cost category rule definition                                      |
| `list-cost-category-definitions`            | List all cost category definitions                                       |
| `list-cost-allocation-tags`                 | List cost allocation tag status                                          |
| `get-approximate-usage-records`             | Estimate number of usage records                                         |

## Key Concepts

### Date Format

All dates use `YYYY-MM-DD`. The `--time-period` is `Start` inclusive, `End` **exclusive**:

```sh
# January 2024: Start=2024-01-01, End=2024-02-01
--time-period Start=2024-01-01,End=2024-02-01
```

### Platform Date Portability

Shell `date` arithmetic differs between Linux and macOS. Use portable alternatives:

```sh
# Linux (GNU date)
date -d "30 days ago" +%Y-%m-%d
date -d "$(date +%Y-%m-01) +1 month" +%Y-%m-%d

# macOS (BSD date)
date -v-30d +%Y-%m-%d
date -v+1m -v1d +%Y-%m-%d

# Portable (Python — works everywhere)
python3 -c "from datetime import date, timedelta; print(date.today() - timedelta(days=30))"
python3 -c "from datetime import date; d=date.today().replace(day=1); print(date(d.year + d.month//12, d.month%12+1, 1))"
```

> **Recommendation**: Use the Python one-liners in scripts that run on both Linux and macOS to avoid silent wrong-date failures.

### Granularity

| Value     | Available in                              | Notes                                           |
| --------- | ----------------------------------------- | ----------------------------------------------- |
| `DAILY`   | `get-cost-and-usage`, `get-cost-forecast` | Max 366 days per request; 13-month retention    |
| `MONTHLY` | `get-cost-and-usage`, `get-cost-forecast` | Up to 18 months for forecast                    |
| `HOURLY`  | `get-cost-and-usage` only                 | Rolling last 14 days (not calendar); no GroupBy |

> **13-month DAILY limit**: DAILY data older than ~13 months returns empty results with no error. Use MONTHLY granularity for historical queries beyond 1 year.

### Metrics

Pass one or more metric names to `--metrics`. **Casing differs by command**:

- `get-cost-and-usage` → camelCase: `BlendedCost`, `UnblendedCost`, `AmortizedCost`
- `get-cost-forecast` / `get-usage-forecast` → SCREAMING_SNAKE_CASE: `BLENDED_COST`, `UNBLENDED_COST`, `AMORTIZED_COST`

| Metric                  | Description                                       |
| ----------------------- | ------------------------------------------------- |
| `BlendedCost`           | Averaged rate across all usage (default for orgs) |
| `UnblendedCost`         | Actual rate for each line item                    |
| `AmortizedCost`         | Upfront RI/SP fees spread over commitment period  |
| `NetAmortizedCost`      | AmortizedCost minus any RI/SP discounts           |
| `NetUnblendedCost`      | UnblendedCost minus discounts                     |
| `UsageQuantity`         | Raw usage amount (hours, GB, requests)            |
| `NormalizedUsageAmount` | Usage normalized to equivalent units              |

### GroupBy Dimensions

```sh
--group-by Type=DIMENSION,Key=SERVICE
--group-by Type=DIMENSION,Key=LINKED_ACCOUNT
--group-by Type=DIMENSION,Key=REGION
--group-by Type=DIMENSION,Key=INSTANCE_TYPE
--group-by Type=DIMENSION,Key=USAGE_TYPE
--group-by Type=DIMENSION,Key=RECORD_TYPE
--group-by Type=TAG,Key=Environment          # cost allocation tag
--group-by Type=COST_CATEGORY,Key=MyCategory # cost category
```

Up to 2 `--group-by` entries allowed. Tags must be activated as cost allocation tags first.

### `get-dimension-values` — Valid `--dimension` Values

```
SERVICE | LINKED_ACCOUNT | REGION | AZ | INSTANCE_TYPE | OPERATION |
PURCHASE_TYPE | USAGE_TYPE | TENANCY | RECORD_TYPE | LEGAL_ENTITY_NAME |
INVOICING_ENTITY | DEPLOYMENT_OPTION | DATABASE_ENGINE | CACHE_ENGINE |
INSTANCE_TYPE_FAMILY | BILLING_ENTITY | RESERVATION_ID | SAVINGS_PLANS_TYPE |
SAVINGS_PLAN_ARN | OPERATING_SYSTEM
```

### Filter Expression Structure

Filters use a recursive JSON `Expression` object. Only **one root operator** per node.

**Simple dimension filter:**

```json
{
  "Dimensions": {
    "Key": "SERVICE",
    "Values": [
      "Amazon EC2",
      "Amazon S3"
    ]
  }
}
```

**Tag filter:**

```json
{
  "Tags": {
    "Key": "Environment",
    "Values": [
      "production"
    ]
  }
}
```

**AND compound filter (service + region):**

```json
{
  "And": [
    {
      "Dimensions": {
        "Key": "SERVICE",
        "Values": [
          "Amazon EC2"
        ]
      }
    },
    {
      "Dimensions": {
        "Key": "REGION",
        "Values": [
          "us-east-1",
          "us-west-2"
        ]
      }
    }
  ]
}
```

**NOT filter (exclude data transfer):**

```json
{
  "Not": {
    "Dimensions": {
      "Key": "USAGE_TYPE",
      "Values": [
        "DataTransfer"
      ]
    }
  }
}
```

**Complex OR + NOT:**

```json
{
  "And": [
    {
      "Or": [
        {
          "Dimensions": {
            "Key": "REGION",
            "Values": [
              "us-east-1"
            ]
          }
        },
        {
          "Tags": {
            "Key": "Team",
            "Values": [
              "platform"
            ]
          }
        }
      ]
    },
    {
      "Not": {
        "Dimensions": {
          "Key": "USAGE_TYPE",
          "Values": [
            "DataTransfer"
          ]
        }
      }
    }
  ]
}
```

**MatchOptions** (for tags and cost categories):

- `EQUALS` (default), `ABSENT`, `STARTS_WITH`, `ENDS_WITH`, `CONTAINS`, `CASE_SENSITIVE`, `CASE_INSENSITIVE`

## Recipes

### Cost by Service This Month

```sh
# Linux
START=$(date +%Y-%m-01)
END=$(date -d "$START +1 month" +%Y-%m-%d)

# macOS: END=$(date -v+1m -v1d +%Y-%m-%d)
# Portable: END=$(python3 -c "from datetime import date; d=date.today().replace(day=1); print(date(d.year + d.month//12, d.month%12+1, 1))")

aws ce get-cost-and-usage \
	--time-period Start=$START,End=$END \
	--granularity MONTHLY \
	--metrics BlendedCost \
	--group-by Type=DIMENSION,Key=SERVICE \
	--query 'ResultsByTime[0].Groups[*].[Keys[0],Metrics.BlendedCost.Amount]' \
	--output table
```

### Daily Costs for Past 30 Days

```sh
# Linux
START=$(date -d "30 days ago" +%Y-%m-%d)
# macOS: START=$(date -v-30d +%Y-%m-%d)
# Portable: START=$(python3 -c "from datetime import date, timedelta; print(date.today()-timedelta(30))")
END=$(date +%Y-%m-%d)

aws ce get-cost-and-usage \
	--time-period Start=$START,End=$END \
	--granularity DAILY \
	--metrics UnblendedCost \
	--query 'ResultsByTime[*].[TimePeriod.Start,Total.UnblendedCost.Amount]' \
	--output table
```

### Cost by Linked Account (Multi-Account Org)

```sh
aws ce get-cost-and-usage \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--granularity MONTHLY \
	--metrics BlendedCost \
	--group-by Type=DIMENSION,Key=LINKED_ACCOUNT \
	--output json | jq '.ResultsByTime[0].Groups[] | {account: .Keys[0], cost: .Metrics.BlendedCost.Amount}'
```

### Filter to EC2 Costs Only

```sh
aws ce get-cost-and-usage \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--granularity MONTHLY \
	--metrics UnblendedCost \
	--filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon EC2"]}}' \
	--group-by Type=DIMENSION,Key=REGION
```

### Cost by Service Filtered by Tag (--filter + --group-by combined)

This is the most common real-world pattern — filter to a tag value, then group by service:

```sh
aws ce get-cost-and-usage \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--granularity MONTHLY \
	--metrics UnblendedCost \
	--filter '{"Tags":{"Key":"Environment","Values":["production"]}}' \
	--group-by Type=DIMENSION,Key=SERVICE \
	--query 'ResultsByTime[0].Groups[*].[Keys[0],Metrics.UnblendedCost.Amount]' \
	--output table
```

> `--filter` and `--group-by` are independent parameters. The filter limits which records are summed;
> the group-by controls how results are bucketed. They can always be combined.

### Cost by Environment Tag

```sh
aws ce get-cost-and-usage \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--granularity MONTHLY \
	--metrics BlendedCost \
	--group-by Type=TAG,Key=Environment \
	--query 'ResultsByTime[0].Groups[*].[Keys[0],Metrics.BlendedCost.Amount]' \
	--output table
```

### Top 10 Costliest Services (with jq)

```sh
aws ce get-cost-and-usage \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--granularity MONTHLY \
	--metrics BlendedCost \
	--group-by Type=DIMENSION,Key=SERVICE \
	--output json |
	jq -r '.ResultsByTime[0].Groups[]
    | [.Keys[0], (.Metrics.BlendedCost.Amount | tonumber | . * 100 | round / 100)]
    | @tsv' |
	sort -t$'\t' -k2 -rn |
	head -10
```

### 3-Month Cost Forecast

```sh
# Linux
START=$(date +%Y-%m-%d)
END=$(date -d "3 months" +%Y-%m-%d)
# macOS: END=$(date -v+3m +%Y-%m-%d)

aws ce get-cost-forecast \
	--time-period Start=$START,End=$END \
	--metric UNBLENDED_COST \
	--granularity MONTHLY \
	--query 'ResultsByTime[*].[TimePeriod.Start,MeanValue]' \
	--output table
```

### Forecast with Prediction Interval (80% confidence)

```sh
aws ce get-cost-forecast \
	--time-period Start=2024-04-01,End=2024-07-01 \
	--metric BLENDED_COST \
	--granularity MONTHLY \
	--prediction-interval-level 80 \
	--output json | jq '.ResultsByTime[] | {period: .TimePeriod.Start, mean: .MeanValue, low: .PredictionIntervalLowerBound, high: .PredictionIntervalUpperBound}'
```

### List Cost Anomalies (Last 30 Days)

```sh
# Linux
START=$(date -d "30 days ago" +%Y-%m-%d)
END=$(date +%Y-%m-%d)
# macOS: START=$(date -v-30d +%Y-%m-%d)

aws ce get-anomalies \
	--date-interval Start=$START,End=$END \
	--query 'Anomalies[*].[AnomalyId,RootCauses[0].Service,Impact.TotalImpact]' \
	--output table
```

### List Anomaly Monitors

```sh
aws ce get-anomaly-monitors \
	--query 'AnomalyMonitors[*].[MonitorName,MonitorType,MonitorSpecification]' \
	--output table
```

### EC2 Rightsizing Recommendations

```sh
# Returns max 8 results per page — use --next-page-token for more
aws ce get-rightsizing-recommendation \
	--service AmazonEC2 \
	--query 'RightsizingRecommendations[*].{ID:CurrentInstance.ResourceId,Type:RightsizingType,Savings:RightsizingRecommendationSummary.EstimatedMonthlySavingsAmount}' \
	--output table
```

### Reservation Utilization (Last Month)

```sh
aws ce get-reservation-utilization \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--granularity MONTHLY \
	--query 'UtilizationsByTime[*].[TimePeriod.Start,Total.UtilizationPercentage]' \
	--output table
```

### Savings Plans Coverage

```sh
aws ce get-savings-plans-coverage \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--granularity MONTHLY \
	--metrics SpendCoveredBySavingsPlans \
	--query 'SavingsPlansCoverages[*].[TimePeriod.Start,Coverage.CoveragePercentage]' \
	--output table
```

### Discover Valid Dimension Values

```sh
# List valid service names
aws ce get-dimension-values \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--dimension SERVICE \
	--query 'DimensionValues[*].Value' \
	--output text | tr '\t' '\n' | sort

# List valid regions
aws ce get-dimension-values \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--dimension REGION \
	--query 'DimensionValues[*].Value' \
	--output text | tr '\t' '\n' | sort
```

### Discover Cost Allocation Tag Values

```sh
aws ce get-tags \
	--time-period Start=2024-01-01,End=2024-02-01 \
	--tag-key Environment \
	--query 'Tags[*]' \
	--output text
```

### Pagination

`get-cost-and-usage` uses `--next-page-token` / `NextPageToken` in the response (not `--starting-token`,
which is the AWS CLI paginator mechanism and does not work with all CE commands):

```sh
#!/usr/bin/env bash
# Requires bash (not sh) — uses bash array syntax
TOKEN=""
while :; do
	ARGS=(--time-period Start=2024-01-01,End=2024-04-01 --granularity DAILY --metrics BlendedCost)
	[[ -n "$TOKEN" ]] && ARGS+=(--next-page-token "$TOKEN")
	RESPONSE=$(aws ce get-cost-and-usage "${ARGS[@]}" --output json)
	echo "$RESPONSE" | jq '.ResultsByTime[]'
	TOKEN=$(echo "$RESPONSE" | jq -r '.NextPageToken // empty')
	[[ -z "$TOKEN" ]] && break
done
```

> For `get-rightsizing-recommendation`, pagination uses `--next-page-token` from `RightsizingRecommendations.NextPageToken` — results are capped at 8 per page.

## Common Mistakes

| Mistake                                              | Fix                                                                                                            |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `End` same as start                                  | `End` is exclusive — set it to the day AFTER your last day                                                     |
| Using `--region` to query different CE endpoint      | CE always uses `us-east-1`; `--region` is ignored                                                              |
| HOURLY granularity with GroupBy                      | HOURLY does not support `--group-by`                                                                           |
| Filter with multiple root operators                  | Each `Expression` node may have only ONE root key (`And`, `Or`, `Not`, `Dimensions`, `Tags`, `CostCategories`) |
| Tag filter with unactivated tag                      | Tags must be activated as cost allocation tags in Billing console first                                        |
| `get-rightsizing-recommendation` with complex filter | Supports only `LINKED_ACCOUNT`, `REGION`, `RIGHTSIZING_TYPE`; no OR/NOT                                        |
| Expecting current-day or yesterday data              | CE data has a 24–48 hour lag — treat D-2 as the last reliably complete day                                     |
| Calling CE in a loop                                 | Each call costs $0.01; cache results when possible                                                             |
| Date format `YYYY/MM/DD`                             | Must be `YYYY-MM-DD`                                                                                           |
| DAILY query older than 13 months returns empty       | Use MONTHLY granularity for historical data beyond ~13 months — no error is raised, results are silently empty |
| macOS `date -d` fails                                | BSD `date` uses `-v` not `-d`; use Python one-liners for portability                                           |
| Using `--starting-token` for CE pagination           | CE uses its own `--next-page-token` param; `--starting-token` is for AWS CLI auto-paginators only              |

## IAM Permissions Required (Read-Only)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostAndUsageWithResources",
        "ce:GetCostForecast",
        "ce:GetUsageForecast",
        "ce:GetDimensionValues",
        "ce:GetTags",
        "ce:GetCostCategories",
        "ce:GetAnomalies",
        "ce:GetAnomalyMonitors",
        "ce:GetAnomalySubscriptions",
        "ce:GetRightsizingRecommendation",
        "ce:GetReservationCoverage",
        "ce:GetReservationUtilization",
        "ce:GetReservationPurchaseRecommendation",
        "ce:GetSavingsPlansCoverage",
        "ce:GetSavingsPlansUtilization",
        "ce:GetSavingsPlansUtilizationDetails",
        "ce:GetSavingsPlansPurchaseRecommendation",
        "ce:DescribeCostCategoryDefinition",
        "ce:ListCostCategoryDefinitions",
        "ce:ListCostAllocationTags",
        "ce:GetApproximateUsageRecords"
      ],
      "Resource": "*"
    }
  ]
}
```

## Output Processing with jq

```sh
# Extract cost as number
jq '.ResultsByTime[0].Total.BlendedCost.Amount | tonumber'

# Sum all groups
jq '[.ResultsByTime[0].Groups[].Metrics.BlendedCost.Amount | tonumber] | add'

# CSV of date + cost
jq -r '.ResultsByTime[] | [.TimePeriod.Start, .Total.UnblendedCost.Amount] | @csv'

# Filter groups above $100
jq '.ResultsByTime[0].Groups[] | select(.Metrics.BlendedCost.Amount | tonumber > 100)'
```
