# Public Repository Security Hardening Design

**Date:** 2026-09-14

**Status:** Repository implementation complete; external rollout pending approval

## Purpose

Harden the public Quartz repository and its Cloudflare Worker against unauthorized AI spend, cross-origin abuse, denial-of-wallet attacks, stored XSS, mutable CI dependencies, vulnerable npm dependencies, and weak production observability. The work preserves the public site's normal read experience while making the AI search endpoint fail closed at every cost-bearing boundary.

## Confirmed Findings

- `worker/index.js` emits `Access-Control-Allow-Origin: *` in both ordinary and streaming responses, so browser origins are not restricted consistently.
- `/api/search` has no ingress authentication or anonymous-attestation boundary, no request-size or query-size cap, no short-window rate limit, and no cross-instance hard daily budget before the DeepSeek call.
- `worker/wrangler.toml` currently binds KV and Vectorize, but no rate-limit or atomic budget service.
- `/api/debug` is publicly routed and request bodies can also enable a `debug` response path.
- `quartz/components/scripts/search-ai.inline.js` assigns search, history, modal, and AI-answer data to `innerHTML`.
- `scripts/daily_digest/render.py` interpolates AI and external fields into Markdown. Quartz then permits raw HTML through `allowDangerousHtml` and `rehypeRaw` paths in `quartz/processors/parse.ts` and `quartz/plugins/transformers/ofm.ts`.
- GitHub workflows reference third-party actions by mutable major-version tags.
- The latest known npm audit reported high-severity production and development findings involving dependency chains that include `js-yaml`, `sharp`, `ws`, `minimatch`, and `wrangler`; the exact current graph must be re-audited before upgrades.
- Worker logging is ad hoc and does not define a redaction-safe event contract or production alert thresholds.
- `main` protection, Worker deployment, secrets, resource creation, and alert rules are external state and cannot be enforced merely by committing repository files.

## Security Model

### Trust boundaries

The following inputs are untrusted even when they were previously stored by this application:

- HTTP headers, origin, body, query, and client-generated tokens.
- Search index and KV records.
- DeepSeek output.
- GitHub Trending and other externally collected data.
- Generated Markdown and local browser history.

The DeepSeek API key, Cloudflare binding state, authorization or attestation tokens, and budget counters are confidential server-side state. No secret may be embedded in Quartz's static browser bundle.

### Public access and authentication

CORS is a browser response policy, not authentication. Exact Origin enforcement reduces browser abuse but does not stop scripts or direct HTTP clients. The selected repository scope therefore implements the controls that are safe for a public static site:

- Exact CORS allowlisting.
- Strict input limits.
- Cloudflare Rate Limiting for short-window abuse.
- A Durable Object for a global, atomic daily AI request budget.

If the deployment requires identity rather than anonymous public access, Cloudflare Access must be selected and configured as a separate production decision. A bearer secret must never be shipped to the static frontend. Turnstile may be added later as bot attestation, but it is not represented as user authentication and is outside this converged implementation scope.

## Architecture

### Worker request pipeline

All `/api/search` requests pass through one ordered pipeline:

1. Match the route and method.
2. Validate the request Origin against exact configured origins.
3. Enforce content type and read the body with a byte-counting limit.
4. Validate the parsed schema, query length, result limit, and other numeric bounds.
5. Apply Cloudflare's Rate Limiting binding using a stable abuse-control key.
6. Atomically reserve one request from the Durable Object's UTC daily budget.
7. Bound retrieval result count and total context bytes.
8. Call DeepSeek with a fixed output-token ceiling and timeout.
9. Return a response through one common response-header function.

Every denial occurs before the next, more expensive stage. If the rate-limit or budget binding is unavailable, the endpoint fails closed with a generic `503`. The budget is consumed immediately before the provider call; rejected validation, CORS, and rate-limit requests do not consume it. A request reservation is not refunded on an ambiguous provider failure, because a retry could otherwise exceed the hard request budget.

The Durable Object uses a date key based on UTC, stores `{ day, used }`, and performs the read/check/increment in one serialized call. The configured daily limit is a positive integer. Reaching it returns `429` with a `Retry-After` value ending at the next UTC day boundary. This is a hard request ceiling, not an estimate of provider billing. Context and output-token caps separately bound the maximum cost of each accepted request.

### CORS policy

Allowed origins come from configuration and are parsed as complete origins: scheme, host, and explicit/default port. Comparison is exact; substring, suffix, wildcard, `null`, and malformed origins are rejected. Allowed responses echo the validated Origin and include `Vary: Origin`. Preflight allows only the required method and headers. Disallowed responses do not include an allow-origin header.

Requests without an Origin are not automatically trusted. They may be handled according to the endpoint's explicit public policy, but cannot bypass rate, input, or budget controls.

### Input and upstream limits

The Worker does not call `request.json()` before enforcing a body limit. It streams and counts bytes, rejects oversized bodies with `413`, then parses JSON. The route accepts only `POST` and JSON. Unknown keys may be ignored only if documented; `debug` is rejected or removed and can never alter output.

Configuration defines conservative positive bounds for:

- Request body bytes.
- Query characters and UTF-8 bytes.
- Search result count.
- Retrieved context bytes.
- DeepSeek maximum output tokens.
- Upstream timeout.
- Rate-limit period and count.
- Daily AI request count.

Misconfigured or missing security-critical values cause a closed failure rather than an unlimited default.

### Debug removal

`/api/debug` and body-controlled debug behavior are removed from production code. Unknown routes return a minimal response. Provider responses, prompts, retrieved context, environment names, binding metadata, and stack traces are never returned to callers.

### XSS prevention

XSS is fixed at both the producer and consumer boundaries.

In the browser, untrusted values are inserted with `textContent`, `createTextNode`, attribute setters, and DOM construction. AI answers initially render as plain text with preserved whitespace. Links are parsed and restricted to approved protocols and expected destinations. Search results, modal content, and local browser history remain untrusted after storage. No dynamic untrusted value enters `innerHTML`.

In `scripts/daily_digest/render.py`, AI and external values are encoded for their Markdown context. Link destinations are parsed separately and restricted to safe protocols. HTML escaping alone is insufficient for Markdown link syntax, so text and URLs use distinct helpers.

As defense in depth, every Quartz path that executes `rehypeRaw` is followed by `rehype-sanitize` with an explicit schema. The schema permits only the elements, attributes, and URL protocols needed by existing authored content and Quartz features. Tests protect legitimate code blocks, images, tables, and OFM constructs while denying scripts, event handlers, dangerous URLs, and executable embedded content.

### CSP and response security headers

The implementation adds only headers compatible with the deployed architecture and verifies the generated site before tightening them:

- `Content-Security-Policy` with explicit `default-src`, `script-src`, `style-src`, `img-src`, `font-src`, `connect-src`, `object-src 'none'`, `base-uri 'self'`, and `frame-ancestors 'none'` directives.
- `X-Content-Type-Options: nosniff`.
- `Referrer-Policy: strict-origin-when-cross-origin`.
- `Permissions-Policy` disabling unused capabilities.

Because Quartz currently uses inline assets, a false claim of strict CSP would be harmful. Implementation first inventories generated inline scripts/styles. It then uses hashes/nonces where the hosting path supports them, or documents the narrowest temporarily required inline directive. `unsafe-eval` is not permitted. HSTS is configured only on a production HTTPS hostname where all subdomains are known to be HTTPS-safe; it is not blindly added to local or preview responses.

### GitHub Actions and dependencies

Every third-party workflow action is pinned to a verified full 40-character commit SHA, retaining a version comment for maintainability. A repository test rejects future mutable refs. SHA values are obtained from the official action repository during implementation and are never guessed. Dependabot or equivalent automation may propose pin updates, but normal review remains required.

Dependency remediation begins with a fresh `npm audit` and `npm explain` for every vulnerable chain. Direct dependencies are upgraded one independently testable group at a time. `npm audit fix --force` is prohibited. Production high/critical findings must reach zero. Any temporarily unfixable development-only finding requires a documented reachability assessment, compensating control, owner, and expiry date.

### Logging and alerting

The Worker emits one bounded JSON security event per terminal decision. The schema contains event name, request ID, route, decision, stable reason code, status, duration, and coarse budget state. It never contains authorization headers, tokens, raw IP addresses, request bodies, queries, prompts, retrieved context, provider response bodies, secrets, or stack traces.

Repository code and tests define events for origin denial, invalid input, oversized bodies, short-window rate denial, daily-budget denial, upstream timeout/failure, and internal closed failures. Cloudflare Observability, Logpush destinations, retention, dashboards, and production alert thresholds are external configuration. They are inspected read-only first and changed only with explicit authorization.

## External Operations and Safety Gates

The following sequence is mandatory after repository tests pass:

1. Read and export the current Cloudflare Worker bindings, variables, routes, migrations, observability configuration, and deployment version.
2. Read and export the current GitHub Rulesets/branch protection and exact successful workflow check names.
3. Present the intended diff and rollback steps to the user.
4. With explicit approval, create the Rate Limiting binding and Durable Object namespace/migration, set non-secret variables or secrets, and deploy to staging.
5. Verify staging behavior, logs, limits, daily rollover, streaming responses, CSP, and site rendering.
6. With explicit production approval, deploy and enable alerts.
7. With separate approval, protect `main` using a GitHub Ruleset that requires pull requests, approval, resolved conversations, and already-proven required checks; disables force pushes and deletion; and preserves intentional bot/admin bypass.

Ruleset automation must not run until the exact current job names have succeeded on `main`, because a nonexistent required check can lock the repository. Repository code may document the desired configuration but cannot claim that `main` is protected.

## Testing Strategy

Every change follows red-green-refactor. Tests use malicious fixtures such as `<script>`, event-handler attributes, `javascript:` URLs, malformed origins, suffix-confusion origins, oversized streaming bodies, concurrent budget requests, and unavailable bindings.

Verification is layered:

- Focused Worker security and budget unit tests.
- Python renderer tests.
- Browser/DOM XSS regression tests.
- Quartz parse/OFM and full-build fixtures.
- Workflow pinning and existing workflow tests.
- Type checking and formatting.
- Production and full dependency audits.
- Staging verification after deployment, as required by `AGENTS.md`.

## Acceptance Criteria

- A disallowed Origin never receives an allow-origin header; allowed origins are exact and responses vary on Origin.
- Invalid or oversized input cannot reach search storage, Vectorize, the budget object, or DeepSeek.
- Short-window excess requests are rejected before the daily budget and provider call.
- Concurrent accepted calls cannot exceed the configured UTC daily request budget.
- `/api/debug` and body-controlled debug output are absent.
- Stored search, history, AI, and generated Markdown payloads cannot create executable DOM or unsafe links.
- Quartz raw HTML is sanitized without regressing documented legitimate content.
- CSP/security headers are present at the correct serving layer and validated against a production-like build.
- All third-party Actions use verified 40-character SHAs.
- Production npm audit reports no high/critical findings; any permitted development exception is explicit and time-bounded.
- Security logs are structured and tested for redaction; production alerts are separately verified after authorized configuration.
- External Cloudflare and GitHub state is never changed without a prior read-only snapshot and explicit approval.
