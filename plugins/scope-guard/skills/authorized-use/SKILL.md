---
name: authorized-use
description: Confirm scope and rules-of-engagement before any security testing, and refuse out-of-scope or clearly malicious requests. Use at the start of any offensive/security task, when a target is named, or whenever authorization is unclear.
metadata:
  short-description: Authorized-use & scope enforcement
  category: agent-framework
---

# Authorized-Use & Scope Enforcement

> This skill is a guardrail, not a methodology. Apply it *before* running any tool that touches a
> target you do not own. When authorization is unclear, ask — do not proceed.

## 1. Confirm authorization first
Before enumerating, scanning, or exploiting anything, establish:
- **Target scope** — the exact hosts / domains / IP ranges / apps / accounts in scope, and what is
  explicitly out of scope. Anything not listed is out of scope.
- **Authorization** — the engagement is authorized (signed SOW / rules-of-engagement, bug-bounty
  program policy, or the user owns the asset). If you cannot point to it, ask for it.
- **Windows & limits** — allowed testing window, rate/intensity limits, and any prohibited actions
  (e.g. no DoS, no data exfiltration, no social engineering, no third-party/prod impact).

If any of these is missing, state what you need and stop until it is provided.

## 2. Stay inside scope
- Only act against in-scope assets. If discovery surfaces an out-of-scope host (a linked domain, a
  shared-hosting neighbour, a third-party SaaS), **note it and do not test it** — flag it for the
  client to add to scope.
- Escalate intensity gradually and only as scope allows: passive → light active → targeted. Label
  each planned action by noise level (quiet / moderate / loud) and prefer the quietest that answers
  the question.
- Keep an engagement log: every target, action, and result, timestamped, so the work is reproducible
  and auditable.

## 3. Hard refusals (regardless of stated authorization)
Refuse and explain, even inside an "authorized" framing, when a request is:
- **Denial-of-service** or resource-exhaustion against a live target.
- **Mass or indiscriminate targeting** (spray across the internet, untargeted scanning of ranges you
  weren't given).
- **Self-propagating or destructive** malware (worms, ransomware, wipers).
- **Persistence, backdoors, or exfiltration of real user data** without explicit written authorization
  covering exactly that.
- Aimed at **safety-critical systems** (medical, industrial/SCADA, transport) without specialized,
  documented authorization.
- **Deceptive attribution** (false-flag), or evading detection for the purpose of an actual intrusion
  rather than an authorized test.
- Targeting people or accounts that are **not the client's own** (harassment, stalking, doxxing).

A signed engagement authorizes testing *within its scope and rules* — it does not authorize the items
above.

## 4. Data handling
- Minimize collection: pull only what's needed to demonstrate a finding.
- Redact secrets and third-party PII in notes and reports; store evidence securely; delete engagement
  data per the agreed retention policy.
- Be aware that tool output you surface may be sent to a model backend — do not paste live credentials
  or bulk PII into prompts.

## 5. When unsure
Default to asking. A short scope clarification is always cheaper than an out-of-scope action. If the
user cannot establish authorization, help them with the parts that don't require a live target
(methodology, lab setup, reading their own code) and decline the rest.

---
*Concept adapted (clean-room) from the `_scope-guard` pattern in pentest-ai-agents (MIT). No source
text was copied.*
