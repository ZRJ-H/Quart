import assert from "node:assert/strict"
import { readFile, readdir } from "node:fs/promises"
import test from "node:test"

const workflowsDirectory = new URL("../.github/workflows/", import.meta.url)
const immutableActionRef = /^[^\s@]+@[0-9a-f]{40}$/
const codeownersUrl = new URL("../.github/CODEOWNERS", import.meta.url)

test("every external GitHub Action is pinned to a full commit SHA", async () => {
  const workflowNames = (await readdir(workflowsDirectory)).filter((name) => /\.ya?ml$/.test(name))

  for (const workflowName of workflowNames) {
    const source = await readFile(new URL(workflowName, workflowsDirectory), "utf8")
    const references = [...source.matchAll(/^\s*uses:\s*([^\s#]+)/gm)].map((match) => match[1])
    for (const reference of references) {
      if (reference.startsWith("./")) continue
      assert.match(
        reference,
        immutableActionRef,
        `${workflowName} contains mutable action reference ${reference}`,
      )
    }
  }
})

test("security-critical deployment files require repository-owner review", async () => {
  const source = await readFile(codeownersUrl, "utf8")
  assert.match(source, /^\/\.github\/workflows\/ \s*@ZRJ-H$/m)
  assert.match(source, /^\/worker\/ \s*@ZRJ-H$/m)
})
