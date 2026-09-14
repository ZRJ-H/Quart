import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

import yaml from "js-yaml"
import toml from "toml"

const workflowUrl = new URL("../.github/workflows/deploy.yaml", import.meta.url)
const wranglerUrl = new URL("../worker/wrangler.toml", import.meta.url)
const memoryUrl = new URL("../MEMORY.md", import.meta.url)
const deployScriptUrl = new URL("../scripts/deploy-worker.sh", import.meta.url)

test("content collection completion triggers a Pages deployment", async () => {
  const workflow = yaml.load(await readFile(workflowUrl, "utf8"))

  assert.deepEqual(workflow.on.workflow_run.workflows, ["Collect Daily Knowledge"])
  assert.deepEqual(workflow.on.workflow_run.types, ["completed"])
  assert.match(workflow.jobs.build.if, /workflow_run\.conclusion == 'success'/)
})

test("deployment uses current official Pages actions and a complete artifact", async () => {
  const workflow = yaml.load(await readFile(workflowUrl, "utf8"))
  const steps = workflow.jobs.build.steps
  const use = (name) => steps.find((step) => step.name === name)?.uses
  const run = (name) => steps.find((step) => step.name === name)?.run || ""

  assert.equal(
    use("Checkout repository"),
    "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
  )
  assert.equal(use("Setup Node.js"), "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020")
  assert.equal(use("Setup Python"), "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97")
  assert.equal(
    use("Configure GitHub Pages"),
    "actions/configure-pages@983d7736d9b0ae728b81ab479565c72886d7745b",
  )
  assert.equal(
    use("Upload Pages artifact"),
    "actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b",
  )
  assert.match(run("Prepare Pages artifact"), /\.nojekyll/)
  assert.equal(
    workflow.jobs.deploy.steps[0].uses,
    "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e",
  )
})

test("watchdog has both UTC cron triggers and only non-secret configuration", async () => {
  const config = toml.parse(await readFile(wranglerUrl, "utf8"))

  assert.deepEqual(config.triggers.crons, ["0 3 * * *", "0 6 * * *"])
  assert.deepEqual(
    { ...config.vars },
    {
      ALLOWED_ORIGINS: "https://zrj-h.github.io",
      AI_DAILY_LIMIT: "100",
      UPSTREAM_TIMEOUT_MS: "30000",
      GITHUB_OWNER: "ZRJ-H",
      GITHUB_REPO: "Quart",
      GITHUB_BRANCH: "main",
      GITHUB_WORKFLOW: "collect-github-trending.yaml",
      SITE_BASE_URL: "https://zrj-h.github.io/Quart",
    },
  )
  assert.equal("GITHUB_TOKEN" in config.vars, false)
})

test("Cloudflare deployment securely synchronizes the optional watchdog token", async () => {
  const workflow = yaml.load(await readFile(workflowUrl, "utf8"))
  const steps = workflow.jobs.build.steps
  const credentials = steps.find((step) => step.name === "Check Cloudflare credentials")
  const sync = steps.find((step) => step.name === "Sync Cloudflare search backend")

  assert.equal(credentials.env.CLOUDFLARE_API_TOKEN, "${{ secrets.CF_API_TOKEN }}")
  assert.match(credentials.run, /configured=false.*GITHUB_OUTPUT/s)
  assert.match(credentials.run, /::warning::CF_API_TOKEN/)
  assert.equal(sync.if, "steps.cloudflare.outputs.configured == 'true'")
  assert.equal(sync.env.WATCHDOG_GITHUB_TOKEN, "${{ secrets.WATCHDOG_GITHUB_TOKEN }}")
  assert.match(sync.run, /WATCHDOG_GITHUB_TOKEN/)
  assert.match(sync.run, /GITHUB_TOKEN/)
  assert.match(sync.run, /mktemp/)
  assert.match(sync.run, /trap .*rm -f/)
  assert.match(sync.run, /if ! npx wrangler secret bulk/)
  assert.match(sync.run, /existing Worker secret unchanged/i)
  assert.match(sync.run, /warning/i)
})

test("Worker operations point to the same workers.dev host as the live site", async () => {
  const expected = "https://doge-wiki-search.ruijiezhou22.workers.dev"
  const [memory, deployScript] = await Promise.all([
    readFile(memoryUrl, "utf8"),
    readFile(deployScriptUrl, "utf8"),
  ])

  assert.match(memory, new RegExp(expected))
  assert.match(deployScript, new RegExp(expected))
  assert.doesNotMatch(memory, /zstufjj2004\.workers\.dev/)
  assert.doesNotMatch(deployScript, /zstufjj2004\.workers\.dev/)
})
