import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

import yaml from "js-yaml"

const workflowPath = new URL("../.github/workflows/deploy-pages.yml", import.meta.url)

async function loadWorkflow() {
  const source = await readFile(workflowPath, "utf8")
  return yaml.load(source)
}

function findStep(steps, name) {
  const step = steps.find((candidate) => candidate.name === name)
  assert.ok(step, `missing workflow step: ${name}`)
  return step
}

test("deploy workflow refreshes content and publishes a Pages artifact", async () => {
  const workflow = await loadWorkflow()

  assert.deepEqual(workflow.on.push.branches, ["master", "main"])
  assert.equal(workflow.on.schedule[0].cron, "15 0 * * *")
  assert.ok(workflow.on.workflow_dispatch)
  assert.deepEqual(workflow.permissions, {
    contents: "write",
    pages: "write",
    "id-token": "write",
  })

  const build = workflow.jobs.build
  assert.equal(build["runs-on"], "ubuntu-latest")
  const steps = build.steps
  assert.equal(steps[0].uses, "actions/checkout@v6")
  assert.equal(findStep(steps, "Set up Node.js").uses, "actions/setup-node@v7")
  assert.equal(findStep(steps, "Set up Python").uses, "actions/setup-python@v7")

  const crawlerSteps = steps.filter((step) => step.name?.startsWith("Crawl "))
  assert.equal(crawlerSteps.length, 5)
  assert.ok(crawlerSteps.every((step) => step["continue-on-error"] === true))

  const refreshGuard = findStep(steps, "Protect history when every crawler fails")
  assert.equal(refreshGuard.id, "refresh_guard")
  assert.match(refreshGuard.run, /CONTENT_RETENTION_DAYS=36500/)
  assert.match(
    findStep(steps, "Remove expired daily content").if,
    /steps\.refresh_guard\.outputs\.has_fresh == 'true'/,
  )

  assert.match(findStep(steps, "Commit refreshed content").run, /git push/)
  assert.match(findStep(steps, "Build Quartz site").run, /build:pages/)
  assert.match(findStep(steps, "Generate browser search indexes").run, /index:pages/)
  assert.match(findStep(steps, "Prepare Pages artifact").run, /\.nojekyll/)
  assert.equal(findStep(steps, "Configure GitHub Pages").uses, "actions/configure-pages@v5")
  assert.equal(findStep(steps, "Upload Pages artifact").uses, "actions/upload-pages-artifact@v4")

  const deploy = workflow.jobs.deploy
  assert.equal(deploy.needs, "build")
  assert.equal(deploy.environment.name, "github-pages")
  assert.equal(deploy.steps[0].uses, "actions/deploy-pages@v4")
})
