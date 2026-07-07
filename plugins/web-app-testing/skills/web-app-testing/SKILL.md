---
name: web-app-testing
description: Systematic web application security testing methodology aligned to OWASP WSTG — how to scope, which vulnerability classes to test, how to verify a finding before reporting it, and how to write it up. Use when testing a web app or API in an authorized engagement.
metadata:
  short-description: WSTG-aligned web app testing playbook
  category: web
---

# Web Application Testing Methodology

> Authorized engagements only. Confirm scope and rules-of-engagement first (see the `authorized-use`
> skill). Test only the hosts/apps explicitly in scope.

This is a methodology, not an exploit kit. It tells you *what* to look at, *how to confirm* it, and
*how to report* it. Use the app's own tooling and any wrapped scanners you've installed for the
mechanics.

## 1. Map before you test
- **Enumerate the surface**: hosts, subdomains, endpoints, parameters, APIs (REST/GraphQL), auth
  flows, roles, and state-changing actions. Crawl authenticated and unauthenticated.
- **Fingerprint the stack**: framework, server, WAF, auth provider, storage. Known stacks have known
  default weaknesses — note them.
- **Model the trust boundaries**: where does user input cross into a parser, a query, a template, a
  file path, a request to another service, or a privilege check? Those crossings are where bugs live.

## 2. Test taxonomy (WSTG-aligned)
Work these classes against every relevant input/boundary. For each, the goal is a *confirmed,
minimal, reproducible* observation — not a scanner guess.

**Authentication & session**
- Authentication logic (credential handling, MFA bypass, password reset flows, account lockout).
- Session management (token generation, fixation, expiry, logout, cookie flags/scope).
- JWT / token handling (algorithm confusion, weak secrets, unvalidated `jku`/`x5u`, claim tampering).

**Authorization**
- Broken object-level authorization / IDOR (can one user reach another's objects?).
- Broken function-level authorization (can a low-priv role invoke admin functions?).
- Mass assignment (can the client set fields it shouldn't — role, ownership, price?).

**Injection & parser abuse**
- SQL / NoSQL injection.
- Command / template injection (SSTI), expression-language injection.
- XML external entities (XXE), deserialization of untrusted data.
- Header/host-header injection, HTTP request smuggling.

**Client-side**
- Cross-site scripting (reflected / stored / DOM).
- Cross-site request forgery (CSRF) on state-changing actions.
- Open redirects, clickjacking, prototype pollution.

**Server-side request & files**
- Server-side request forgery (SSRF), incl. cloud-metadata reachability.
- Path traversal / LFI / RFI, insecure file upload.

**Logic & exposure**
- Business-logic flaws (race conditions, workflow bypass, quantity/price tampering).
- Information disclosure (stack traces, debug endpoints, secrets in JS/source maps, verbose errors).
- Security misconfiguration (default creds, exposed admin, permissive CORS, missing headers).

## 3. Verify before you report
Adopt an **oracle** mindset: a finding is real only when you can trigger the effect deterministically.
- Reproduce the observation **more than once**; distinguish a genuine effect from a coincidence, cache
  artifact, or scanner false-positive.
- Reduce to the **minimal request(s)** that demonstrate it. Capture the exact request/response.
- State the concrete impact (what an attacker gains), not just "input is reflected."
- If you cannot reproduce it deterministically, mark it *unconfirmed* and keep it out of the findings
  list (or file it as an observation to revisit).

## 4. OpSec noise discipline
Label each action by expected noise and prefer the quietest that answers the question:
- **Quiet** — passive observation, single crafted requests, reading responses.
- **Moderate** — targeted parameter fuzzing, limited automated scanning of specific endpoints.
- **Loud** — full automated scans, brute-force, high request volume.
Escalate only as scope and the rules-of-engagement allow, and stay within any rate limits. Test in the
agreed window; avoid actions that degrade production for real users.

## 5. Handoff to reporting
For each confirmed finding, hand the reporting phase (see the `report-writing` skill):
- A neutral, specific title; severity (impact × likelihood, CVSS optional).
- Affected assets (hosts/URLs/parameters), a minimal reproduction, redacted evidence.
- A concrete, testable remediation with a reference (CWE/OWASP).

---
*Taxonomy structure informed by the vulnerability-class libraries in Strix (Apache-2.0) and the
web-hunter methodology in pentest-ai-agents (MIT); the "verify with an oracle" discipline is informed
by pentest-ai (MIT). Authored clean-room — no source text copied. See `third_party/` for licenses.*
