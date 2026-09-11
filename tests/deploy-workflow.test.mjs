import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

import yaml from "js-yaml"

const workflowUrl = new URL("../.github/workflows/deploy.yaml", import.meta.url)

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
