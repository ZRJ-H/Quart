import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import path from "node:path"
import test from "node:test"
import vm from "node:vm"

const generatorUrl = new URL("../scripts/generate-github-trending.js", import.meta.url)
const source = await readFile(process.env.TRENDING_TEST_SOURCE || generatorUrl, "utf8")
// Exercise the source in an isolated VM: all files and model replies are fixtures.
// No production entry point, real filesystem writes, credentials, or network calls.
const executable = source
  .replace(/^import fs from "fs"\r?\n/m, "")
  .replace(/^import path from "path"\r?\n/m, "")
const root = "/fixture/content"
const archivePath = (name) => path.join(root, "GitHub 项目档案", `${name.replace("/", "-")}.md`)
const notePath = (date) => path.join(root, "GitHub Trending", `${date}.md`)

function repo(name, stars, rank = 1) {
  return {
    name,
    stars,
    rank,
    url: `https://github.com/${name}`,
    language: "TypeScript",
    description: "测试项目",
  }
}

function archive(name, date, stars, delta = "+0⭐") {
  return `# ${name}\n\n> 测试项目\n\n## 历史趋势\n\n| 日期 | 排名 | 星数 | 增量 | 类型 |\n|---|---:|---:|---:|---|\n| ${date} | #1 | ${stars} | ${delta} | 常驻 |\n`
}

async function generate(
  rows,
  {
    date = "2026-10-14",
    files = new Map(),
    model = false,
    go = false,
    modelContent = null,
    modelAnalysis = "## 深度解读\n\n离线模型夹具。",
    descriptions = {},
  } = {},
) {
  const storage = new Map(files)
  storage.set("/fixture/input.json", JSON.stringify(rows))
  const writes = []
  const requests = []
  const filesystem = {
    existsSync: (filename) => storage.has(filename),
    readFileSync(filename) {
      assert.ok(storage.has(filename), `Unexpected fixture read: ${filename}`)
      return storage.get(filename)
    },
    mkdirSync() {},
    writeFileSync(filename, value) {
      assert.ok(filename.startsWith(`${root}/`), `Unexpected fixture write: ${filename}`)
      storage.set(filename, value)
      writes.push(filename)
    },
  }
  const context = vm.createContext({
    fs: filesystem,
    path,
    process: {
      env: {
        RUN_DATE: date,
        CONTENT_ROOT: root,
        TRENDING_JSON: "/fixture/input.json",
        DEEPSEEK_API_KEY: model ? "offline-fixture" : "",
        GO_API_KEY: go ? "offline-go-fixture" : "",
      },
    },
    console: { log() {}, error() {} },
    fetch: async (url, request) => {
      assert.ok(model || go, "Unexpected model request in offline fallback test")
      requests.push({ url, body: JSON.parse(request.body) })
      return {
        ok: true,
        json: async () => ({
          choices: [
            {
              message: {
                content: modelContent ?? JSON.stringify({ descriptions, analysis: modelAnalysis }),
              },
            },
          ],
        }),
      }
    },
  })
  const script = new vm.Script(
    `(async () => {\n${executable}\nreturn { items, top5, formatDelta, rankComparable: typeof rankComparable === "function" ? rankComparable : undefined };\n})()`,
  )
  const state = await script.runInContext(context, { timeout: 2000 })
  return { state, files: storage, writes, requests, note: storage.get(notePath(date)) }
}

function topSection(note) {
  return note.split("## 今日增长 TOP 5")[1].split("\n---")[0]
}

test("direct Trending uses Flash non-thinking JSON without increasing the output cap", async () => {
  const result = await generate([repo("owner/repo", 100)], {
    model: true,
    go: true,
    descriptions: { "owner/repo": "离线中文简介。" },
  })
  assert.equal(result.requests.length, 1)
  const { url, body } = result.requests[0]
  assert.equal(url, "https://api.deepseek.com/chat/completions")
  assert.equal(body.model, "deepseek-flash")
  assert.deepEqual(body.thinking, { type: "disabled" })
  assert.deepEqual(body.response_format, { type: "json_object" })
  assert.equal(body.max_tokens, 3000)
  assert.match(result.note, /离线中文简介/)
})

test("GO-only Trending keeps its original Pro contract", async () => {
  const result = await generate([repo("owner/repo", 100)], { go: true })
  assert.equal(result.requests.length, 1)
  const { url, body } = result.requests[0]
  assert.equal(url, "https://opencode.ai/zen/go/v1/chat/completions")
  assert.equal(body.model, "deepseek-v4-pro")
  assert.equal(body.max_tokens, 3000)
  assert.equal(Object.hasOwn(body, "thinking"), false)
  assert.equal(Object.hasOwn(body, "response_format"), false)
})

test("empty or malformed Flash output preserves local fallback without another provider call", async () => {
  for (const modelContent of ["", '{"descriptions":']) {
    const result = await generate([repo("owner/repo", 100)], {
      model: true,
      go: true,
      modelContent,
    })
    assert.equal(result.requests.length, 1)
    assert.equal(result.requests[0].body.model, "deepseek-flash")
    assert.match(result.note, /测试项目/)
    assert.doesNotMatch(result.note, /undefined|NaN/)
  }
})

test("first-seen stars are not a measured increment", async () => {
  const result = await generate([repo("morluto/rea", 215408)])
  assert.equal(result.state.items[0].delta, null)
  assert.equal(result.state.items[0].type, "新晋")
  assert.match(result.note, /总星数\*\*: 215,408/)
  assert.match(result.note, /本次增量\*\*: 未知（缺少历史基线）/)
  assert.doesNotMatch(result.note, /\+215,408|未知[^\n]*⭐|NaN|null|undefined/)
  assert.match(
    result.files.get(archivePath("morluto/rea")),
    /\| 215,408 \| 未知（缺少历史基线） \| 新晋 \|/,
  )
  assert.equal(result.requests.length, 0)
})

test("unknown increments are excluded from TOP5 and fallback winner", async () => {
  const files = new Map([
    [
      archivePath("DietrichGebert/ponytail"),
      archive("DietrichGebert/ponytail", "2026-10-13", 160610),
    ],
    [archivePath("mattpocock/skills"), archive("mattpocock/skills", "2026-10-13", 288392)],
  ])
  const result = await generate(
    [
      repo("morluto/rea", 215408),
      repo("mattpocock/skills", 289972, 5),
      repo("DietrichGebert/ponytail", 162906, 25),
    ],
    { files },
  )
  assert.deepEqual(
    Array.from(result.state.top5, (item) => [item.name, item.delta]),
    [
      ["DietrichGebert/ponytail", 2296],
      ["mattpocock/skills", 1580],
    ],
  )
  assert.doesNotMatch(topSection(result.note), /morluto\/rea/)
  assert.match(result.note, /### 本日之星：DietrichGebert\/ponytail/)
  assert.match(result.note, /本次记录增量 \+2,296⭐/)
})

test("same-day first-seen rerun stays unknown and replaces one archive row", async () => {
  const first = await generate([repo("morluto/rea", 211925)])
  const second = await generate([repo("morluto/rea", 215408)], { files: first.files })
  const record = second.files.get(archivePath("morluto/rea"))
  assert.equal(second.state.items[0].delta, null)
  assert.equal((record.match(/^\| 2026-10-14 \|/gm) || []).length, 1)
  assert.match(record, /\| 215,408 \| 未知（缺少历史基线） \| 新晋 \|/)
  assert.doesNotMatch(second.note, /\+3,483|\+215,408/)
})

test("the next day uses the prior day's stars even if its increment was unknown", async () => {
  const first = await generate([repo("morluto/rea", 215408)])
  const next = await generate([repo("morluto/rea", 215508)], {
    date: "2026-10-15",
    files: first.files,
  })
  assert.equal(next.state.items[0].delta, 100)
  assert.equal(next.state.items[0].type, "常驻")
  assert.match(topSection(next.note), /\+100⭐/)
  assert.match(
    next.files.get(archivePath("morluto/rea")),
    /\| 2026-10-15 \| #1 \| 215,508 \| \+100⭐ \| 常驻 \|/,
  )
})

test("known zero and negative increments remain comparable", async () => {
  const files = new Map([
    [archivePath("owner/zero"), archive("owner/zero", "2026-10-13", 100)],
    [archivePath("owner/negative"), archive("owner/negative", "2026-10-13", 100)],
  ])
  const result = await generate(
    [repo("owner/new", 999999), repo("owner/negative", 66), repo("owner/zero", 100)],
    { files },
  )
  assert.deepEqual(
    Array.from(result.state.top5, (item) => item.delta),
    [0, -34],
  )
  assert.match(topSection(result.note), /\+0⭐/)
  assert.match(topSection(result.note), /-34⭐/)
  assert.equal(result.state.items[1].type, "回落")
  assert.equal(result.state.items[2].type, "常驻")
})

test("empty and all-new inputs have no invented increment winner", async () => {
  for (const rows of [[], [repo("owner/new", 1000), repo("owner/another", 2000)]]) {
    const result = await generate(rows)
    assert.equal(result.state.top5.length, 0)
    assert.match(result.note, /### 本日之星：暂无可比项目/)
    assert.match(result.note, /今日没有具备历史基线的可比增量/)
    assert.doesNotMatch(result.note, /NaN|null|undefined|\+1,000⭐|\+2,000⭐/)
  }
})

test("missing and malformed archive stars do not become a zero baseline", async () => {
  for (const stars of ["", "not-a-number", "100stars", "12,34", "Infinity", "9007199254740992"]) {
    const files = new Map([[archivePath("owner/repo"), archive("owner/repo", "2026-10-13", stars)]])
    const result = await generate([repo("owner/repo", 1000)], { files })
    assert.equal(result.state.items[0].delta, null)
    assert.equal(result.state.top5.length, 0)
    assert.doesNotMatch(result.note, /\+1,000⭐|NaN/)
  }
})

test("an actual historical zero is a valid baseline", async () => {
  const files = new Map([[archivePath("owner/repo"), archive("owner/repo", "2026-10-13", 0)]])
  const result = await generate([repo("owner/repo", 800)], { files })
  assert.equal(result.state.items[0].delta, 800)
  assert.equal(result.state.items[0].type, "爆火")
  assert.match(topSection(result.note), /\+800⭐/)
})

test("formatting and ranking reject non-finite increments without coercing null to zero", async () => {
  const result = await generate([])
  for (const delta of [null, undefined, Number.NaN, Infinity, -Infinity]) {
    assert.equal(result.state.formatDelta(delta), "未知（缺少历史基线）")
  }
  assert.equal(result.state.formatDelta(0), "+0⭐")
  assert.equal(result.state.formatDelta(-34), "-34⭐")
  const input = [
    { delta: null },
    { delta: Number.NaN },
    { delta: 0 },
    { delta: -1 },
    { delta: 500 },
  ]
  assert.deepEqual(
    Array.from(result.state.rankComparable(input), (item) => item.delta),
    [500, 0, -1],
  )
  assert.equal(input[0].delta, null)
})

test("model evidence preserves JSON null and explains its meaning using only a fake response", async () => {
  const result = await generate([repo("owner/new", 1000)], { model: true })
  assert.equal(result.requests.length, 1)
  const prompt = result.requests[0].body.messages[0].content
  assert.match(prompt, /"stars":1000,"delta":null,"type":"新晋"/)
  assert.match(prompt, /delta 为 null 表示缺少历史采集基线，不是零/)
  assert.match(prompt, /不得用 stars 替代增量/)
  assert.match(prompt, /不得将这类项目纳入增量排名/)
  assert.equal(result.state.top5.length, 0)
  assert.doesNotMatch(result.note, /null|NaN|\+1,000⭐/)
})

test("known-baseline same-day reruns retain yesterday's baseline", async () => {
  const files = new Map([[archivePath("owner/repo"), archive("owner/repo", "2026-10-13", 100)]])
  const first = await generate([repo("owner/repo", 150)], { files })
  const second = await generate([repo("owner/repo", 170)], { files: first.files })
  assert.equal(second.state.items[0].delta, 70)
  const record = second.files.get(archivePath("owner/repo"))
  assert.equal((record.match(/^\| 2026-10-14 \|/gm) || []).length, 1)
  assert.match(record, /\| 170 \| \+70⭐ \| 常驻 \|/)
})

test("October 14 numeric fixture keeps exactly five comparable projects in descending order", async () => {
  const measured = [
    ["DietrichGebert/ponytail", 2296],
    ["mattpocock/skills", 1580],
    ["public-apis/public-apis", 386],
    ["firecrawl/firecrawl", 336],
    ["NousResearch/hermes-agent", 311],
    ["anomalyco/opencode", 285],
    ["nilbuild/developer-roadmap", 269],
    ["torvalds/linux", 209],
  ]
  const files = new Map(
    measured.map(([name]) => [archivePath(name), archive(name, "2026-10-13", 100000)]),
  )
  const result = await generate(
    [repo("morluto/rea", 215408), ...measured.map(([name, delta]) => repo(name, 100000 + delta))],
    { files },
  )
  assert.deepEqual(
    Array.from(result.state.top5, (item) => [item.name, item.delta]),
    measured.slice(0, 5),
  )
  assert.match(topSection(result.note), /首次收录项目不参与增量排名/)
  assert.doesNotMatch(topSection(result.note), /morluto\/rea/)
})

test("a model cannot nominate an incomparable project or invent its winning increment", async () => {
  const files = new Map([[archivePath("owner/known"), archive("owner/known", "2026-10-13", 100)]])
  const result = await generate([repo("owner/new", 215408), repo("owner/known", 600)], {
    files,
    model: true,
    modelAnalysis:
      "## 深度解读\n\n### 本日之星：owner/new\n\nowner/new 今日新增 215,408⭐，增量最高。\n\n### 趋势脉动\n\n保持该段。\n\n### 项目生态关联\n\n保持生态段。",
  })
  assert.match(result.note, /### 本日之星：owner\/known/)
  assert.match(result.note, /本次记录增量 \+500⭐/)
  assert.doesNotMatch(result.note, /今日新增 215,408|### 本日之星：owner\/new/)
  assert.doesNotMatch(result.note, /保持该段|保持生态段/)
  assert.match(result.note, /### 数据边界/)
})

test("all-new model output cannot invent a comparable winner", async () => {
  const result = await generate([repo("owner/new", 215408)], {
    model: true,
    modelAnalysis: "## 深度解读\n\n### 本日之星\n\nowner/new 增量最高，+215,408⭐。",
  })
  assert.match(result.note, /### 本日之星：暂无可比项目/)
  assert.doesNotMatch(result.note, /增量最高|\+215,408/)
})

test("missing model winner section falls back safely", async () => {
  const result = await generate([repo("owner/new", 215408)], {
    model: true,
    modelAnalysis: "## 深度解读\n\nowner/new 今日新增 215,408⭐。",
  })
  assert.match(result.note, /### 本日之星：暂无可比项目/)
  assert.doesNotMatch(result.note, /今日新增 215,408/)
})

test("accepted Chinese descriptions stay in project details, outside the measured summary", async () => {
  const item = { ...repo("owner/known", 600), description: "English description" }
  const files = new Map([[archivePath(item.name), archive(item.name, "2026-10-13", 100)]])
  const result = await generate([item], {
    files,
    model: true,
    descriptions: { "owner/known": "经过模型翻译的中文简介。" },
    modelAnalysis: "## 深度解读\n\n### 本日之星\n\n错误文案。\n\n### 项目生态关联\n\n生态文案。",
  })
  const star = result.note.split("### 本日之星")[1].split("### 项目生态关联")[0]
  assert.match(result.note, /> 经过模型翻译的中文简介/)
  assert.doesNotMatch(star, /经过模型翻译的中文简介|暂无中文简介|错误文案/)
})

test("duplicate model winner sections fall back to one deterministic winner", async () => {
  const files = new Map([[archivePath("owner/known"), archive("owner/known", "2026-10-13", 100)]])
  for (const heading of ["#", "##", "###", "####", "#####", "######"]) {
    const result = await generate([repo("owner/new", 215408), repo("owner/known", 600)], {
      files,
      model: true,
      modelAnalysis: `## 深度解读\n\n### 本日之星：owner/known\n\n正常候选。\n\n${heading} 本日之星：owner/new\n\nowner/new 今日新增 215,408⭐，增量最高。`,
    })
    assert.equal((result.note.match(/^### 本日之星/gm) || []).length, 1)
    assert.match(result.note, /### 本日之星：owner\/known/)
    assert.doesNotMatch(result.note, /今日新增 215,408|本日之星：owner\/new/)
  }
})

// Captured 2026-10-16 archive totals/deltas; ECC's previous snapshot is 2026-10-13.
// Columns: repository, current stars, increment, rank, previous snapshot date.
const october16 = [
  ["public-apis/public-apis", 489184, 355, 1, "2026-10-15"],
  ["freeCodeCamp/freeCodeCamp", 457131, 59, 2, "2026-10-15"],
  ["EbookFoundation/free-programming-books", 399150, 84, 3, "2026-10-15"],
  ["openclaw/openclaw", 392133, 85, 4, "2026-10-15"],
  ["nilbuild/developer-roadmap", 369500, 80, 5, "2026-10-15"],
  ["vinta/awesome-python", 327737, 236, 6, "2026-10-15"],
  ["awesome-selfhosted/awesome-selfhosted", 327018, 298, 7, "2026-10-15"],
  ["affaan-m/ECC", 280565, 2475, 8, "2026-10-13"],
  ["morluto/rea", 275267, 26736, 9, "2026-10-15"],
  ["NousResearch/hermes-agent", 254180, 321, 10, "2026-10-15"],
  ["torvalds/linux", 251998, 133, 11, "2026-10-15"],
  ["react/react", 251085, 51, 12, "2026-10-15"],
  ["deepseek-ai/deepseek-harness", 250587, 726, 13, "2026-10-15"],
  ["TheAlgorithms/Python", 225293, 25, 14, "2026-10-15"],
  ["anomalyco/opencode", 213994, 421, 15, "2026-10-15"],
  ["n8n-io/n8n", 207571, 154, 16, "2026-10-15"],
  ["tensorflow/tensorflow", 200993, 22, 17, "2026-10-15"],
  ["microsoft/vscode", 193673, 49, 18, "2026-10-15"],
  ["firecrawl/firecrawl", 191957, 325, 19, "2026-10-15"],
  ["avelino/awesome-go", 188633, 167, 20, "2026-10-15"],
  ["Significant-Gravitas/AutoGPT", 187602, 22, 21, "2026-10-15"],
  ["ollama/ollama", 183369, 173, 22, "2026-10-15"],
  ["flutter/flutter", 180231, 41, 23, "2026-10-15"],
  ["twbs/bootstrap", 174867, 25, 24, "2026-10-15"],
  ["f/prompts.chat", 173109, 82, 25, "2026-10-15"],
]

function october16Fixture(modelAnalysis) {
  const files = new Map(
    october16.map(([name, stars, delta, , previousDate]) => [
      archivePath(name),
      archive(name, previousDate, stars - delta),
    ]),
  )
  return generate(
    october16.map(([name, stars, , rank]) => repo(name, stars, rank)),
    {
      files,
      date: "2026-10-16",
      model: true,
      modelAnalysis,
    },
  )
}

function analysisSection(note) {
  return note.split("## 深度解读")[1].split("\n---")[0]
}

test("October 16 regression: +726 is above the burst threshold, despite model prose", async () => {
  const result = await october16Fixture(
    "## 深度解读\n\n### 本日之星\n\ndeepseek-ai/deepseek-harness 增量726，虽未达爆火阈值。\n\n### 趋势脉动\n\n模型统计。",
  )
  const analysis = analysisSection(result.note)
  assert.doesNotMatch(analysis, /未达爆火阈值|模型统计/)
  assert.match(analysis, /\*\*爆火\*\*：3 个；本次增量范围 \+726⭐ 至 \+26,736⭐/)
  assert.match(analysis, /已知增量 ≥500⭐ 为爆火/)
  assert.match(analysis, /### 本日之星：morluto\/rea/)
})

test("October 16 regression: measured rising range is 236 to 421, never 167 to 421", async () => {
  const result = await october16Fixture(
    "## 深度解读\n\n### 本日之星\n\nmorluto/rea。\n\n### 趋势脉动\n\n跃升项目增量在167至421之间。",
  )
  const analysis = analysisSection(result.note)
  assert.match(analysis, /\*\*跃升\*\*：6 个；本次增量范围 \+236⭐ 至 \+421⭐/)
  assert.doesNotMatch(analysis, /167至421/)
})

test("October 16 regression: resident increments cannot exceed the measured rising range", async () => {
  const result = await october16Fixture(
    "## 深度解读\n\n### 本日之星\n\nmorluto/rea。\n\n### 趋势脉动\n\n部分常驻项目增量也高于个别跃升项目。",
  )
  const analysis = analysisSection(result.note)
  assert.doesNotMatch(analysis, /常驻项目增量也高于/)
  assert.match(analysis, /\*\*常驻\*\*：16 个；本次增量范围 \+22⭐ 至 \+173⭐/)
  assert.match(analysis, /\*\*跃升\*\*：6 个；本次增量范围 \+236⭐ 至 \+421⭐/)
  assert.match(analysis, /200–499⭐ 为跃升，0–199⭐ 为常驻/)
})

test("all model analysis is ignored, including preambles and unexpected heading levels", async () => {
  for (const modelAnalysis of [
    "全站第一，新增999999星。",
    "## 深度解读\n\n全站新增999999星。\n\n### 本日之星\n\n错误。\n\n### 项目生态关联\n\n全站新增999999星。",
    "## 深度解读\n\n#### 趋势脉动\n\n全站新增999999星。\n\n## 其他结论\n\n错误分类。",
  ]) {
    const result = await october16Fixture(modelAnalysis)
    assert.doesNotMatch(analysisSection(result.note), /999999|全站新增|错误分类|错误。/)
    assert.equal((result.note.match(/^### 趋势脉动/gm) || []).length, 1)
    assert.equal((result.note.match(/^### 本日之星/gm) || []).length, 1)
    assert.match(analysisSection(result.note), /\*\*爆火\*\*：3 个/)
  }
})

test("statistical summary covers unknown, zero, negative, and classification boundaries", async () => {
  const deltas = [500, 499, 200, 199, 0, -1]
  const files = new Map(
    deltas.map((delta, index) => [
      archivePath(`owner/item${index}`),
      archive(`owner/item${index}`, "2026-10-15", 1000),
    ]),
  )
  const result = await generate(
    [
      repo("owner/new", 500000),
      ...deltas.map((delta, index) => repo(`owner/item${index}`, 1000 + delta)),
    ],
    {
      files,
      date: "2026-10-16",
    },
  )
  const analysis = analysisSection(result.note)
  assert.match(analysis, /\*\*新晋\*\*：1 个；增量未知（缺少历史基线）/)
  assert.match(analysis, /\*\*爆火\*\*：1 个；本次增量范围 \+500⭐ 至 \+500⭐/)
  assert.match(analysis, /\*\*跃升\*\*：2 个；本次增量范围 \+200⭐ 至 \+499⭐/)
  assert.match(analysis, /\*\*常驻\*\*：2 个；本次增量范围 \+0⭐ 至 \+199⭐/)
  assert.match(analysis, /\*\*回落\*\*：1 个；本次增量范围 -1⭐ 至 -1⭐/)
  assert.doesNotMatch(analysis, /NaN|null|undefined|500,000⭐/)
  assert.match(analysis, /不一定覆盖完整一天/)
})

test("model and offline paths render the same measured summary", async () => {
  const rows = [repo("owner/known", 600)]
  const files = new Map([[archivePath("owner/known"), archive("owner/known", "2026-10-13", 100)]])
  const offline = await generate(rows, { files })
  const model = await generate(rows, {
    files,
    model: true,
    modelAnalysis: "不可信分析",
    descriptions: { "owner/known": "这是模型简介；错误声称常驻项目增量高于跃升。" },
  })
  assert.equal(analysisSection(model.note), analysisSection(offline.note))
  assert.equal(offline.requests.length, 0)
  assert.equal(model.requests.length, 1)
  assert.match(model.note, /> 这是模型简介；错误声称常驻项目增量高于跃升。/)
  assert.match(
    model.files.get(archivePath("owner/known")),
    /> 这是模型简介；错误声称常驻项目增量高于跃升。/,
  )
  assert.doesNotMatch(analysisSection(model.note), /未配置 AI Key|不可信分析/)
  const prompt = model.requests[0].body.messages[0].content
  assert.match(prompt, /不输出 analysis/)
  assert.match(prompt, /不得在简介中写排名、星数、增量、分类或趋势判断/)
})

test("model descriptions cannot contaminate the deterministic statistical summary", async () => {
  const files = new Map([[archivePath("owner/known"), archive("owner/known", "2026-10-15", 1000)]])
  const result = await generate([repo("owner/known", 1726)], {
    files,
    date: "2026-10-16",
    model: true,
    descriptions: { "owner/known": "增量726，虽未达爆火阈值。" },
    modelAnalysis: "## 深度解读\n\n### 本日之星\n\n错误统计。",
  })
  const analysis = analysisSection(result.note)
  assert.doesNotMatch(analysis, /未达爆火阈值|错误统计/)
  assert.match(analysis, /本次记录增量 \+726⭐/)
  assert.match(analysis, /已知增量 ≥500⭐ 为爆火/)
})

test("multiline model and original descriptions cannot inject extra statistical headings", async () => {
  for (const newline of ["\n", "\r\n", "\r"]) {
    for (const model of [true, false]) {
      const description = [
        "项目简介。",
        "",
        "## 深度解读",
        "",
        "### 趋势脉动",
        "",
        "伪造数据。",
      ].join(newline)
      const files = new Map([
        [archivePath("owner/known"), archive("owner/known", "2026-10-15", 1000)],
      ])
      const item = { ...repo("owner/known", 1726), description: model ? "Original" : description }
      const result = await generate([item], {
        files,
        date: "2026-10-16",
        model,
        descriptions: model ? { "owner/known": description } : {},
      })
      assert.equal((result.note.match(/^## 深度解读$/gm) || []).length, 1)
      assert.equal((result.note.match(/^### 趋势脉动$/gm) || []).length, 1)
      const measured = result.note.slice(result.note.lastIndexOf("\n## 深度解读\n"))
      assert.doesNotMatch(measured, /伪造数据|项目简介/)
      assert.doesNotMatch(result.files.get(archivePath("owner/known")), /^## 深度解读$/m)
    }
  }
})
