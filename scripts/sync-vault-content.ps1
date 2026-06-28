param(
  [string]$VaultPath = "..\Obsidian Vault",
  [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VaultRoot = (Resolve-Path (Join-Path $RepoRoot $VaultPath)).Path
$ContentRoot = Join-Path $RepoRoot "content"

$items = @(
  "AI科技动态",
  "AI论文日报",
  "GitHub Trending",
  "Hacker News",
  "周报",
  "时政要闻",
  "wiki",
  "scripts",
  "index.md",
  "synonyms.json"
)

foreach ($item in $items) {
  $src = Join-Path $VaultRoot $item
  if (Test-Path -LiteralPath $src) {
    Copy-Item -LiteralPath $src -Destination $ContentRoot -Recurse -Force
  }
}

Push-Location $RepoRoot
try {
  git add content
  $hasChanges = git diff --cached --quiet; $LASTEXITCODE -ne 0
  if (-not $hasChanges) {
    Write-Host "No content changes to commit."
    exit 0
  }

  if (-not $CommitMessage) {
    $CommitMessage = "docs: sync vault content $(Get-Date -Format yyyy-MM-dd)"
  }

  git commit -m $CommitMessage
  git push
}
finally {
  Pop-Location
}
