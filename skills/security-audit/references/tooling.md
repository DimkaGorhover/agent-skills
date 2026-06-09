# Security Audit Tooling

Tools give **breadth and repeatability**; they do not replace manual logic-flaw analysis. Run them for
coverage, then verify each result by hand to eliminate false positives. Use alongside
[`../SKILL.md`](../SKILL.md).

## Static Analysis (SAST) — find vulnerable code patterns

| Tool                                                                   | Notes                                                                                     |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Semgrep**                                                            | Fast, rule-based, multi-language; great default for code audits (`semgrep --config auto`) |
| **CodeQL**                                                             | Deep dataflow/taint analysis; powers GitHub code scanning                                 |
| **SonarQube**                                                          | Broad quality + security; CI-friendly dashboards                                          |
| Bandit (Python), gosec (Go), Brakeman (Rails), ESLint security plugins | Language-specific                                                                         |

## Dependency & Supply-Chain Scanning

| Tool                                      | Notes                                                                   |
| ----------------------------------------- | ----------------------------------------------------------------------- |
| **osv-scanner**                           | Google OSV database; multi-ecosystem                                    |
| **Trivy**                                 | Dependencies, container images, IaC, secrets — one tool, broad coverage |
| `npm audit` / `pip-audit` / `cargo audit` | Built into the ecosystem                                                |
| **Dependabot / Snyk**                     | Continuous monitoring + automated fix PRs                               |
| **Grype**                                 | Container/filesystem vulnerability scanning; pairs with Syft for SBOM   |

## Secret Scanning

| Tool               | Notes                                                                                   |
| ------------------ | --------------------------------------------------------------------------------------- |
| **gitleaks**       | Scans history and working tree for credentials (already used in this repo's pre-commit) |
| **trufflehog**     | Verifies whether found secrets are live                                                 |
| **detect-secrets** | Baseline-based, good for CI gating                                                      |

## Dynamic Analysis (DAST) & Manual Testing — *requires authorization*

> These send traffic to a running target. Confirm scope and written approval first (staging only unless
> production is explicitly authorized).

| Tool           | Notes                                                             |
| -------------- | ----------------------------------------------------------------- |
| **OWASP ZAP**  | Open-source web/API scanner and proxy; scriptable for CI          |
| **Burp Suite** | Industry-standard intercepting proxy for manual web/API testing   |
| **nuclei**     | Template-based scanning for known CVEs and misconfigurations      |
| **sqlmap**     | SQL injection confirmation/exploitation (authorized targets only) |
| **nmap**       | Port/service discovery during reconnaissance                      |

## Infrastructure & Config

| Tool                         | Notes                                                              |
| ---------------------------- | ------------------------------------------------------------------ |
| **Trivy / Checkov / tfsec**  | IaC misconfiguration scanning (Terraform, Kubernetes, Dockerfiles) |
| **kube-bench / kube-hunter** | Kubernetes CIS benchmarks and attack surface                       |
| **Prowler / ScoutSuite**     | Cloud security posture (AWS/Azure/GCP)                             |

## Suggested Order for a Code Audit

1. `gitleaks detect` — fail fast on committed secrets
1. `semgrep --config auto` — flag risky code patterns
1. `osv-scanner` / `trivy fs` — known-vulnerable dependencies
1. Manual trace of entry points and access control (the part tools miss)
1. DAST against staging **only with authorization**
