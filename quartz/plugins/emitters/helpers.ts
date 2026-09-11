import path from "path"
import fs from "fs"
import { BuildCtx } from "../../util/ctx"
import { FilePath, FullSlug, joinSegments } from "../../util/path"
import { Readable } from "stream"

type WriteOptions = {
  ctx: BuildCtx
  slug: FullSlug
  ext: `.${string}` | ""
  content: string | Buffer | Readable
}

export const write = async ({ ctx, slug, ext, content }: WriteOptions): Promise<FilePath> => {
  const pathToPage = joinSegments(ctx.argv.output, slug + ext) as FilePath
  const dir = path.dirname(pathToPage)
  await fs.promises.mkdir(dir, { recursive: true })
  await fs.promises.writeFile(pathToPage, content)

  if (ext === ".html" && slug !== "index" && !slug.endsWith("/index")) {
    const directoryIndexPath = joinSegments(ctx.argv.output, slug, "index.html") as FilePath
    await fs.promises.mkdir(path.dirname(directoryIndexPath), { recursive: true })
    await fs.promises.writeFile(directoryIndexPath, content)
  }

  return pathToPage
}
