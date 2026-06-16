function updateReadingProgress() {
  const bar = document.querySelector(".reading-progress-bar") as HTMLElement | null
  if (!bar) return
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  const progress =
    docHeight > 0 ? Math.min(100, Math.max(0, (window.scrollY / docHeight) * 100)) : 0
  bar.style.width = `${progress}%`
}

document.addEventListener("nav", () => {
  if (!document.querySelector(".reading-progress-bar")) return

  updateReadingProgress()
  window.addEventListener("scroll", updateReadingProgress, { passive: true })
  window.addEventListener("resize", updateReadingProgress)
  window.addCleanup(() => {
    window.removeEventListener("scroll", updateReadingProgress)
    window.removeEventListener("resize", updateReadingProgress)
  })
})
