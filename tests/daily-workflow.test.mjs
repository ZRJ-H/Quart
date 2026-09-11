import assert from "node:assert/strict"
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { spawnSync } from "node:child_process"
import { fileURLToPath } from "node:url"
import test from "node:test"

import yaml from "js-yaml"

const collectUrl = new URL("../.github/workflows/collect-github-trending.yaml", import.meta.url)
const deployUrl = new URL("../.github/workflows/deploy.yaml", import.meta.url)
const trendingGeneratorUrl = new URL("../scripts/generate-github-trending.js", import.meta.url)

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
  const steps = workflow.jobs.collect.steps
  const run = (name) => steps.find((step) => step.name === name)?.run || ""

  assert.match(run("Test daily collectors"), /unittest discover/)
  assert.match(run("Collect daily knowledge"), /collect-daily-content\.py/)
  assert.match(run("Collect daily knowledge"), /generate-github-trending\.js/)
  assert.match(run("Generate weekly report"), /generate-weekly-report\.py/)
  assert.match(run("Collect daily knowledge"), /--require-model/)
  assert.match(run("Commit and push notes"), /git add content/)
  assert.equal(steps.filter((step) => step.name === "Commit and push notes").length, 1)
})

test("Pages deployment waits for the consolidated collector", async () => {
  const workflow = await load(deployUrl)

  assert.deepEqual(workflow.on.workflow_run.workflows, ["Collect Daily Knowledge"])
})
test("Trending generator requests Chinese descriptions and hides English fallback copy", async () => {
  const source = await readFile(trendingGeneratorUrl, "utf8")

  assert.match(source, /descriptionZh/)
  assert.match(source, /中文简介/)
  assert.match(source, /暂无中文简介，请查看项目主页/)
})
test("Trending generation is idempotent within the same day", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "quart-trending-"))
  try {
    const archiveDir = path.join(root, "GitHub 项目档案")
    await mkdir(archiveDir, { recursive: true })
    await writeFile(
      path.join(archiveDir, "owner-repo.md"),
      "# owner/repo\n\n> old\n\n## 历史趋势\n\n| 日期 | 排名 | 星数 | 增量 | 类型 |\n|---|---:|---:|---:|---|\n| 2026-09-10 | #2 | 100 | +10⭐ | 常驻 |\n",
    )
    const input = path.join(root, "trending.json")
    await writeFile(
      input,
      JSON.stringify([{ rank: 1, name: "owner/repo", url: "https://github.com/owner/repo", description: "English description", stars: 150, language: "Python" }]),
    )
    const env = { ...process.env, RUN_DATE: "2026-09-11", TRENDING_JSON: input, CONTENT_ROOT: root, DEEPSEEK_API_KEY: "", GO_API_KEY: "" }
    for (let index = 0; index < 2; index += 1) {
      const result = spawnSync(process.execPath, [fileURLToPath(trendingGeneratorUrl)], { env, encoding: "utf8" })
      assert.equal(result.status, 0, result.stderr)
    }

    const archive = await readFile(path.join(archiveDir, "owner-repo.md"), "utf8")
    assert.equal((archive.match(/^\| 2026-09-11 \|/gm) || []).length, 1)
    assert.match(archive, /\| 2026-09-11 \| #1 \| 150 \| \+50⭐ \|/)
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})