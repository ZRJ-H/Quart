import { QuartzFilterPlugin } from "../types"

interface Options {
  days: number
  paths: string[]
}

const defaultOptions: Options = {
  days: 5,
  paths: ["AI科技动态", "GitHub-Trending", "时政要闻"],
}

export const RemoveOldNotes: QuartzFilterPlugin<Partial<Options>> = (userOpts) => {
  const opts = { ...defaultOptions, ...userOpts }
  return {
    name: "RemoveOldNotes",
    shouldPublish(_ctx, [_tree, vfile]) {
      const slug = vfile.data?.slug ?? ""
      const inTarget = opts.paths.some((p) => slug.startsWith(p + "/") || slug === p)
      if (!inTarget) return true

      const match = slug.match(/(\d{4})-(\d{2})-(\d{2})/)
      if (!match) return true

      const fileDate = new Date(match[0])
      if (isNaN(fileDate.getTime())) return true

      const cutoff = new Date()
      cutoff.setDate(cutoff.getDate() - opts.days)
      return fileDate > cutoff
    },
  }
}
