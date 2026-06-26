import os
import datetime
import re

cutoff = os.environ.get("CONTENT_RETENTION_DAYS", "6")
cutoff = datetime.date.today() - datetime.timedelta(days=int(cutoff))

vault_dir = None
for arg in os.sys.argv[1:]:
    if not arg.startswith("--"):
        vault_dir = arg
        break

if not vault_dir:
    vault_dir = "vault-content"

pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\.md$")
for folder in ["AI科技动态", "时政要闻", "GitHub Trending"]:
    path = os.path.join(vault_dir, folder)
    if not os.path.exists(path):
        continue
    for f in os.listdir(path):
        m = pattern.match(f)
        if m and datetime.date.fromisoformat(m.group(1)) < cutoff:
            filepath = os.path.join(path, f)
            os.remove(filepath)
            print(f"Removed: {filepath}")
