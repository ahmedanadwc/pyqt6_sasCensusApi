import json
from pathlib import Path

uncached = (
    Path("graphify-out/.graphify_uncached.txt").read_text(encoding="utf-8").splitlines()
)
# Filter out graphify-out generated files
uncached = [
    f
    for f in uncached
    if not f.startswith("graphify-out") and not f.startswith("resume_evaluator")
]
print(f"Relevant files: {len(uncached)}")

# Split into chunks of 22
chunk_size = 22
chunks = [uncached[i : i + chunk_size] for i in range(0, len(uncached), chunk_size)]
print(f"Total chunks: {len(chunks)}")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i + 1}: {len(chunk)} files")
    for f in chunk:
        print(f"  {f}")
