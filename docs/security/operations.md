# Public Repository Security Operations

Last reviewed: 2026-09-14 (Asia/Shanghai)

## Repository controls

The repository now defines these fail-closed controls:

- Browser origins: exact allowlist, currently `https://zrj-h.github.io`; no wildcard CORS.
- Request boundary: JSON only, 8 KiB body, 500-character query, 15-result ceiling, bounded filter schema.
- Burst control: Cloudflare Rate Limiting binding `SEARCH_RATE_LIMITER`, 10 requests per 60 seconds per Worker location and client key.
- Hard paid-AI ceiling: Durable Object binding `AI_BUDGET`, 100 reservations per UTC day, migration tag `v1`.
- Per-request ceiling: at most 48 KiB of source context, 2,000 output tokens, and a 30-second provider timeout.
- Response policy: no-store, nosniff, no-referrer, restricted Permissions Policy, exact CORS, and an API CSP.
- Static-site policy: CSP meta policy hashes every required inline script; `script-src` has neither `unsafe-inline` nor `unsafe-eval`.
- Content safety: generated Markdown is context encoded, URL hosts are validated, raw HTML is sanitized after `rehypeRaw`, and search UI values are escaped.
- Supply chain: Actions use verified full commit SHAs; CODEOWNERS assigns security-critical paths to `@ZRJ-H`.
- Dependency gate: both production and complete npm audits reported zero vulnerabilities after the 2026-09-14 update.

Cloudflare Rate Limiting is a burst control, not a global billing ceiling. The Durable Object is the authoritative daily paid-provider ceiling.

## Pre-rollout external snapshot

GitHub public API snapshot on 2026-09-14:

- Repository: `ZRJ-H/Quart`, public, default branch `main`.
- `main.protected`: `false`.
- Repository Rulesets response: `[]`.
- Latest inspected successful deployment run: `34824900802`.
- Successful job names in that run: `build` and `deploy`.
- The daily collection workflow writes generated content directly to `main`; a blanket “pull request required” rule would break that automation unless an explicitly reviewed automation bypass or PR-based publishing flow is added first.

Local Wrangler 4.131.2 dry-run successfully resolved `AI_BUDGET`, `WIKI_DATA`, `VECTORIZE`, `SEARCH_RATE_LIMITER`, all non-secret limits, and the Durable Object migration. Remote Cloudflare state was not readable in this workstation session because no `CLOUDFLARE_API_TOKEN` was available. This means repository configuration is ready, but the new Worker controls must not be described as active until an authorized deployment is verified.

## Production rollout record

Completed on 2026-09-14 (Asia/Shanghai):

- Security release commit: `7f35b52ce1e83414234cff6381e4857990757d40`.
- Initial push deployment: Actions run `34846322725`, successful; both the Cloudflare sync step and Pages deployment ran.
- Daily collection compatibility check: Actions run `34846322679`, successful, including its normal fast-forward push to `main`.
- Final content commit: `7739e057bb766fe4d8fa70c4aac9d11cd6bc1e9b`.
- Final workflow-run deployment: Actions run `34846569585`, successful; Pages deployment `6437567214` published `https://zrj-h.github.io/Quart/`.
- Current Worker version: `d1917cd2-b075-4797-bc06-753a1106719b`.
- Rollback Worker version: `9d9bb744-4878-4226-89b9-f8b3833f77f2`.
- Active repository Ruleset: `23305251` (`Protect main history`), targeting only `refs/heads/main` with `deletion` and `non_fast_forward` rules.
- Production smoke checks passed for health without Origin, exact allowed Origin, denied foreign Origin, allowed preflight, removed `/api/debug`, rejected `debug` request fields, and static-site CSP without `unsafe-inline` or `unsafe-eval`.

No separate staging Worker was deployed because this workstation had no direct Cloudflare credential or isolated staging bindings. The production release therefore used the reviewed GitHub workflow after local tests, dependency audits, a full Quartz build, and a Wrangler dry-run. Do not destructively exercise the production daily budget or force-push protection merely to prove a denial; verify those controls with an isolated staging namespace when one is available.

## Approval-gated production rollout

Before production deployment:

1. Obtain a read-only Cloudflare snapshot: current deployment/version ID, bindings, routes, migrations, observability, and rollback target. Do not print secret values.
2. Deploy to a staging Worker or a temporary test environment with separate rate-limit and Durable Object resources.
3. Verify exact allowed/disallowed origins, preflight, 8 KiB rejection, 10/60 burst denial, daily-budget denial, UTC rollover, 30-second timeout, generic provider errors, SSE headers, and structured redacted logs.
4. Deploy through the existing reviewed GitHub workflow. Record the new Worker version ID and keep the previous version as the rollback target.
5. Verify the live site’s normal search, a no-result search, CSP console, mobile search, generated pages, and the Worker health response.

Rollback:

1. Stop further releases.
2. Use the recorded previous Worker version with Wrangler’s rollback command.
3. Re-run allowed/disallowed Origin and normal search smoke tests.
4. If static rendering regressed, revert the release commit through the normal repository workflow and redeploy Pages.

## Logging and alerts

Logs use bounded JSON events and exclude raw IP addresses, queries, request bodies, prompts, retrieved text, authorization headers, tokens, provider response bodies, stack traces, and exception messages.

After deployment, create and exercise alerts for:

- sustained `origin_denied` or invalid-input spikes;
- `search_rate_limited` spikes;
- daily AI budget at 80%, 95%, and exhausted;
- `deepseek_stream_failed` and Worker 5xx errors;
- missing rate-limit or budget bindings.

Keep alerts quiet for isolated denials and route only meaningful sustained changes or failures.

## GitHub Ruleset proposal

Do not enable a required-check name until it has succeeded on a pull request. The observed `build` and `deploy` jobs came from a push deployment; `deploy` may not be appropriate as a merge requirement.

Safe rollout:

1. First enable deletion and non-fast-forward/force-push protection for `main`.
2. Decide whether daily collection will use a reviewed bypass or open an automated pull request.
3. Test the chosen publishing flow on a temporary branch/ruleset.
4. Then require pull requests, owner review for CODEOWNERS paths, resolved conversations, stale-approval dismissal, and only checks proven on pull requests.
5. Immediately validate with a real test pull request and record the Ruleset ID.

## Routine verification

Run before each security-sensitive release:

```text
npm test
python -m unittest discover -s tests -p "test_*.py"
npm audit --omit=dev --audit-level=high --registry=https://registry.npmjs.org
npm audit --audit-level=high --registry=https://registry.npmjs.org
npx quartz build --directory content
npx wrangler deploy --dry-run --config worker/wrangler.toml
git diff --check
```
