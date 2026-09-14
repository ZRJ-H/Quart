import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

import yaml from "js-yaml"
import toml from "toml"

const workflowUrl = new URL("../.github/workflows/deploy.yaml", import.meta.url)
const wranglerUrl = new URL("../worker/wrangler.toml", import.meta.url)

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

  assert.equal(use("Checkout repository"), "actions/checkout@v6")
  assert.equal(use("Setup Node.js"), "actions/setup-node@v7")
  assert.equal(use("Setup Python"), "actions/setup-python@v7")
  assert.equal(use("Configure GitHub Pages"), "actions/configure-pages@v5")
  assert.equal(use("Upload Pages artifact"), "actions/upload-pages-artifact@v4")
  assert.match(run("Prepare Pages artifact"), /\.nojekyll/)
  assert.equal(workflow.jobs.deploy.steps[0].uses, "actions/deploy-pages@v4")
})

test("watchdog has both UTC cron triggers and only non-secret configuration", async () => {
  const config = toml.parse(await readFile(wranglerUrl, "utf8"))

  assert.deepEqual(config.triggers.crons, ["0 3 * * *", "0 6 * * *"])
  assert.deepEqual(
    { ...config.vars },
    {
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
  const sync = workflow.jobs.build.steps.find(
    (step) => step.name === "Sync Cloudflare search backend",
  )

  assert.equal(sync.env.WATCHDOG_GITHUB_TOKEN, "${{ secrets.WATCHDOG_GITHUB_TOKEN }}")
  assert.match(sync.run, /if \[ -z "\$CLOUDFLARE_API_TOKEN" \]/)
  assert.match(sync.run, /WATCHDOG_GITHUB_TOKEN/)
  assert.match(sync.run, /GITHUB_TOKEN/)
  assert.match(sync.run, /mktemp/)
  assert.match(sync.run, /trap .*rm -f/)
  assert.match(sync.run, /wrangler secret bulk/)
  assert.match(sync.run, /warning/i)
})
