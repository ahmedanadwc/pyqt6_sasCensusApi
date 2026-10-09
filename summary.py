import json
from pathlib import Path

result = json.loads(
    Path("graphify-out/.graphify_detect.json").read_text(encoding="utf-8")
)
for cat, files in result["files"].items():
    print(f"{cat}: {len(files)} files")
print(f"Total: {result['total_files']} files")
print(f"Total words: {result.get('total_words', 0)}")
if "skipped_sensitive" in result and result["skipped_sensitive"]:
    print(f"Skipped sensitive: {result['skipped_sensitive']}")
