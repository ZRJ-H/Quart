import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

import yaml from "js-yaml"

const collectUrl = new URL("../.github/workflows/collect-github-trending.yaml", import.meta.url)
const deployUrl = new URL("../.github/workflows/deploy.yaml", import.meta.url)

async function load(url) {
  return yaml.load(await readFile(url, "utf8"))
}

test("daily collection runs on schedule, manual dispatch, and collector changes", async () => {
  const workflow = await load(collectUrl)

  assert.equal(workflow.name, "Collect Daily Knowledge")
  assert.deepEqual(workflow.on.schedule, [{ cron: "30 0 * * *" }])
  assert.ok(Object.hasOwn(workflow.on, "workflow_dispatch"))
  assert.deepEqual(workflow.on.push.branches, ["main"])
  assert.ok(workflow.on.push.paths.includes("scripts/daily_digest/**"))
})

test("daily workflow tests, collects, summarizes, and commits once", async () => {
  const workflow = await load(collectUrl)
  assert.equal(workflow.permissions.models, "read")
  const steps = workflow.jobs.collect.steps
  const run = (name) => steps.find((step) => step.name === name)?.run || ""

  assert.match(run("Test daily collectors"), /unittest discover/)
  assert.match(run("Collect daily knowledge"), /collect-daily-content\.py/)
  assert.equal(steps.find((step) => step.name === "Collect daily knowledge").env.GITHUB_MODELS_TOKEN, "${{ github.token }}")
  assert.match(run("Collect daily knowledge"), /generate-github-trending\.js/)
  assert.match(run("Generate weekly report"), /generate-weekly-report\.py/)
  assert.match(run("Commit and push notes"), /git add content/)
  assert.equal(steps.filter((step) => step.name === "Commit and push notes").length, 1)
})

test("Pages deployment waits for the consolidated collector", async () => {
  const workflow = await load(deployUrl)

  assert.deepEqual(workflow.on.workflow_run.workflows, ["Collect Daily Knowledge"])
})
