import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "build-wiki-index.py"
SPEC = importlib.util.spec_from_file_location("build_wiki_index", MODULE_PATH)
indexer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(indexer)


class StaticIndexTests(unittest.TestCase):
    def write_note(self, root: Path, relative: str, text: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_collect_entries_preserves_wikilinks_before_cleaning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_note(
                root,
                "wiki/entities/Alpha.md",
                "---\nname: Alpha\ntags: [example]\n---\n"
                "Alpha has enough useful body text and links to [[Beta|the beta note]].",
            )

            entries = indexer.collect_entries(str(root))

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["links"], ["Beta"])
            self.assertEqual(entries[0]["page_path"], None)
            self.assertNotIn("[[", entries[0]["content"])

    def test_collect_entries_assigns_daily_page_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_note(
                root,
                "AI科技动态/2026-09-11.md",
                "---\ntags: [AI]\n---\n# Daily\n\n## 今日要闻\n\n"
                "### 新模型发布\n\n模型正文包含足够的信息，并关联 [[Alpha]]。",
            )

            entries = indexer.collect_entries(str(root))

            self.assertEqual(entries[0]["page_path"], "AI科技动态/2026-09-11")
            self.assertEqual(entries[0]["links"], ["Alpha"])

    def test_write_json_indexes_is_atomic_and_light_index_omits_content(self):
        entry = {
            "id": "daily/AI科技动态/2026-09-11#model",
            "name": "新模型发布",
            "type": "daily",
            "category": "ai-news",
            "tags": ["AI"],
            "summary": "摘要",
            "content": "正文",
            "last_updated": "2026-09-11",
            "content_length": 2,
            "reference_count": 0,
            "links": ["Alpha"],
            "page_path": "AI科技动态/2026-09-11",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            full_path = output / "public" / "wiki-index.json"
            light_path = output / "public" / "wiki-index-light.json"

            indexer.write_json_indexes([entry], str(full_path), str(light_path))

            full = json.loads(full_path.read_text(encoding="utf-8"))
            light = json.loads(light_path.read_text(encoding="utf-8"))
            self.assertEqual(full, [entry])
            self.assertEqual(light[0]["name"], "新模型发布")
            self.assertEqual(light[0]["page_path"], "AI科技动态/2026-09-11")
            self.assertNotIn("content", light[0])
            self.assertNotIn("content_length", light[0])
            self.assertEqual(list((output / "public").glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
