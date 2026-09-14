const DAILY_SECTIONS = ["ai-news", "daily-news", "arxiv-daily", "hn-daily"]
const SHANGHAI_DATE_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Shanghai",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
})

export function shanghaiDate(now = new Date()) {
  return SHANGHAI_DATE_FORMATTER.format(now)
}

function githubUrl(env, suffix) {
  const owner = encodeURIComponent(env.GITHUB_OWNER)
  const repo = encodeURIComponent(env.GITHUB_REPO)
  const workflow = encodeURIComponent(env.GITHUB_WORKFLOW)
  return `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}${suffix}`
}

async function checkPage(fetchImpl, baseUrl, section, date) {
  const url = `${baseUrl.replace(/\/$/, "")}/${encodeURIComponent(section)}/${date}`
  let response
  try {
    response = await fetchImpl(url, { method: "GET" })
  } catch {
    throw new Error(`page check failed for ${section}: network error`)
  }
  if (response.status === 404) return section
  if (!response.ok) throw new Error(`page check failed for ${section}: ${response.status}`)
  return null
}

async function getWorkflowRuns(fetchImpl, env) {
  const branch = encodeURIComponent(env.GITHUB_BRANCH || "main")
  const response = await fetchImpl(githubUrl(env, `/runs?branch=${branch}&per_page=10`), {
    method: "GET",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "X-GitHub-Api-Version": "2022-11-28",
    },
  })
  if (!response.ok) throw new Error(`workflow runs query failed: ${response.status}`)
  let payload
  try {
    payload = await response.json()
  } catch {
    throw new Error("workflow runs query failed: invalid response")
  }
  if (!payload || !Array.isArray(payload.workflow_runs)) {
    throw new Error("workflow runs query failed: invalid response")
  }
  return payload.workflow_runs
}

async function dispatchWorkflow(fetchImpl, env) {
  const response = await fetchImpl(githubUrl(env, "/dispatches"), {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({ ref: "main" }),
  })
  if (response.status !== 204) throw new Error(`workflow dispatch failed: ${response.status}`)
}

export async function runDailyWatchdog(env, options = {}) {
  const fetchImpl = options.fetch || fetch
  const date = shanghaiDate(options.now || new Date())
  const missing = (await Promise.all(
    DAILY_SECTIONS.map((section) => checkPage(fetchImpl, env.SITE_BASE_URL, section, date)),
  )).filter(Boolean)

  if (missing.length === 0) {
    const result = { status: "healthy", date, missing }
    console.log(JSON.stringify(result))
    return result
  }
  if (!env.GITHUB_TOKEN) throw new Error("watchdog requires GITHUB_TOKEN")

  const runs = await getWorkflowRuns(fetchImpl, env)
  if (runs.some((run) => run && (run.status === "queued" || run.status === "in_progress"))) {
    const result = { status: "collection-active", date, missing }
    console.log(JSON.stringify(result))
    return result
  }

  await dispatchWorkflow(fetchImpl, env)
  const result = { status: "dispatched", date, missing }
  console.log(JSON.stringify(result))
  return result
}

