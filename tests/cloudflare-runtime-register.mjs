import { registerHooks } from "node:module"

const shim = [
  "export class DurableObject {",
  "  constructor(ctx, env) {",
  "    this.ctx = ctx;",
  "    this.env = env;",
  "  }",
  "}",
].join("\n")
const shimUrl = `data:text/javascript,${encodeURIComponent(shim)}`

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === "cloudflare:workers") {
      return { url: shimUrl, shortCircuit: true }
    }
    return nextResolve(specifier, context)
  },
})
