---
name: security-audit
description: >
  Use when auditing a codebase, web application, or API for security vulnerabilities — reviewing
  authentication, authorization, access control, input handling, secrets, or data flow across trust
  boundaries. Triggers on "security audit", "security review", "pentest", "find vulnerabilities",
  "threat model", IDOR, injection, SSRF, OWASP Top 10, broken access control, hardening.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Security Audit

**Trace untrusted data from entry to action; at every trust boundary, ask how it is abused.** Scanners catch
known patterns — run them for breadth — but the highest-value findings are access-control and logic flaws
you reach only by reading the code adversarially.

## When to Use

- Auditing a codebase or PR for security vulnerabilities before release
- Reviewing authentication, authorization, session, or access-control logic
- Threat-modeling a new feature, service, or architecture
- Investigating a suspected vulnerability or hardening an existing system
- Producing a prioritized findings report with remediation steps

## When NOT to Use

- **No authorization or scope approval** for testing — STOP and confirm scope first (see [Authorization Gate](#authorization-gate))
- Running intrusive/exploit tests against **production** without written approval
- You need legal counsel, a formal compliance certification, or a signed penetration-test attestation
- You only want a one-shot automated scan with no manual review — run the scanner directly instead
- General code-quality review with no security focus — use a standard code-review skill
- **In-flow secure coding while building a feature** — use the `security-review` skill for that; this skill is for adversarial, post-hoc auditing of an existing surface

## Authorization Gate

**Before any active testing, confirm and record:**

1. **Scope** — which hosts, repos, endpoints, and accounts are in-bounds (and which are explicitly out)
1. **Authorization** — who approved it, in writing, and for what window
1. **Environment** — staging vs. production; intrusive tests are staging-only unless approved in writing
1. **Data handling** — never exfiltrate, log, or paste real secrets/PII into reports; redact them

If any of these is missing, ask before proceeding. Static source-code review of a repo you were asked to
audit is safe; sending traffic, fuzzing, or exploiting a live system is not — that needs explicit sign-off.

## Audit Methodology

Work the phases in order. Each phase feeds the next; don't jump to exploitation before you've mapped the
attack surface.

| Phase         | Goal                  | Key actions                                                                                                                       |
| ------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **1. Map**    | Understand the system | Identify entry points (UI, API, webhooks, queues, files), data stores, trust boundaries, auth model, and third-party dependencies |
| **2. Trace**  | Follow the data       | For each entry point, trace input → middleware → business logic → storage. Mark every trust boundary crossing                     |
| **3. Probe**  | Attack each boundary  | At every boundary ask the [adversarial questions](#adversarial-questions). Test access control per-object, not just per-endpoint  |
| **4. Scan**   | Catch known patterns  | Run SAST, dependency, and secret scanners for breadth (see [tooling](references/tooling.md))                                      |
| **5. Triage** | Rank by risk          | Rank findings by severity and business impact; confirm each is actually exploitable (no false positives)                          |
| **6. Report** | Make it actionable    | One finding per issue: severity, location, evidence, impact, concrete remediation                                                 |

## Focus First: Broken Access Control

The #1 breach cause and the class scanners miss most. Privileged code (Admin SDK, service account) bypasses
the database's row-level security, so the **application** must enforce ownership. Hunt for:

- **IDOR on shared resources** — `DELETE /api/posts/:id` that never verifies the caller owns `:id`
- **Privileged-account writes** that skip the checks a normal client would hit
- **Mutations on shared global state** any authenticated user can trigger
- **Mass-assignment** — request fields (`role`, `isAdmin`, `ownerId`) bound straight to a model

For every create/update/delete: *"Does this caller own, or have permission for, this exact object?"*
See [A01 in the reference](references/vulnerability-classes.md#a01--broken-access-control) for before/after code.

## Adversarial Questions

Ask these at every feature and every trust boundary:

- How can this be **defaced, hijacked, or destroyed**?
- Can I access **another user's** object by changing an ID?
- What happens if I send this field **twice**, **negative**, **huge**, **null**, or as the **wrong type**?
- Can I reach an **internal** host through this (SSRF)? Does it validate the resolved IP, not just the hostname?
- Is this **input** ever concatenated into SQL, a shell, a path, HTML, or a template?
- Where is **authentication enforced** — and is the choke point actually wired up (correct middleware, matcher, export)?
- What does this **leak on error** (stack traces, internal IDs, existence of records)?
- Does any **secret, token, or key** appear in source, logs, client bundles, or version control?

## Vulnerability Classes (OWASP Top 10:2025)

Walk this checklist for web/API audits. Deep what-to-look-for per class is in
[references/vulnerability-classes.md](references/vulnerability-classes.md). (Taxonomy is version-pinned to the
[2025 list](https://owasp.org/Top10/2025/); the underlying flaws are timeless — only the ranking/grouping shifts between editions.)

- [ ] **A01 Broken Access Control** — IDOR, missing ownership checks, privilege escalation, mass-assignment, SSRF
- [ ] **A02 Security Misconfiguration** — verbose errors, default creds, open CORS, missing security headers
- [ ] **A03 Software Supply Chain Failures** — vulnerable/abandoned dependencies, unpinned CI actions, compromised build or distribution
- [ ] **A04 Cryptographic Failures** — plaintext secrets, weak hashing, missing TLS, hard-coded keys
- [ ] **A05 Injection** — SQL/NoSQL, OS command, LDAP, XSS, template injection
- [ ] **A06 Insecure Design** — missing rate limits, abusable business logic, no threat model
- [ ] **A07 Authentication Failures** — weak sessions, credential stuffing, broken MFA, JWT flaws
- [ ] **A08 Software or Data Integrity Failures** — insecure deserialization, unsigned updates
- [ ] **A09 Security Logging and Alerting Failures** — no audit trail, secrets in logs, no alerting on attacks
- [ ] **A10 Mishandling of Exceptional Conditions** — failing open, improper error handling, logic errors on abnormal input

## Reporting Findings

One finding = one issue. Use this structure so each is independently actionable:

```markdown
### [SEVERITY] Short title

- **Location:** file:line or endpoint
- **Severity:** Critical / High / Medium / Low / Info  (CVSS: vector if scored)
- **Impact:** what an attacker gains, in business terms
- **Evidence:** minimal repro or the vulnerable code (secrets redacted)
- **Remediation:** the specific fix, not "validate input"
```

**Severity = likelihood × impact.** A trivially exploitable IDOR exposing all users' data is Critical; a
self-XSS requiring victim cooperation is Low. Prioritize the fix list by severity, and lead the report with
an executive summary (counts by severity + top 3 risks).

## Quality Gates

Before calling an audit complete:

- [ ] Authorization and scope confirmed and recorded
- [ ] Every entry point traced to its data store across trust boundaries
- [ ] Each access-control finding verified at the **object** level, not just the endpoint
- [ ] Findings confirmed exploitable (no unverified scanner output)
- [ ] Each finding has location, severity, impact, evidence, and concrete remediation
- [ ] No real secrets or PII left in the report
- [ ] Executive summary with severity counts and top risks

## Common Mistakes

| Mistake                          | Fix                                                                                                            |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Trusting scanner output as final | Scanners give coverage only; manually confirm exploitability and hunt the logic flaws they can't see           |
| "Validate input" as remediation  | Name the specific control per sink (parameterized query, arg array, output encoding) — see the injection table |
| Reporting every finding as High  | Severity = likelihood × impact; rank ruthlessly so the real Criticals get fixed first                          |

## Read Next

- [references/vulnerability-classes.md](references/vulnerability-classes.md) — per-class what-to-look-for, with code smells and fixes
- [references/tooling.md](references/tooling.md) — SAST, DAST, dependency, and secret scanners by category
