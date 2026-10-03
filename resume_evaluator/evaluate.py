"""Evaluate resumes against a target role using TypeSafe's Jev model.

Usage:
    python evaluate.py --role "Senior Backend Engineer: Python, distributed systems, 5+ years" \
        resumes/alice.pdf resumes/bob.docx resumes/candidates/

Requires TYPESAFE_API_KEY to be set in the environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from typesafe_sdk import Score, TypeSafeClient

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

QUALITY_CRITERIA = [
    "Poor: disorganized, hard to follow, unprofessional presentation",
    "Below average: readable but cluttered, inconsistent formatting or unclear descriptions",
    "Average: reasonably clear and organized, minor issues",
    "Good: clear, well-organized, professionally presented with strong descriptions",
    "Excellent: exceptionally clear, concise, and compellingly presented",
]

FIT_CRITERIA = [
    "No relevant experience or skills for this role",
    "Minimal overlap with the role's requirements",
    "Some relevant experience but notable gaps against key requirements",
    "Strong match, most key requirements are met",
    "Excellent match, meets or exceeds all key requirements",
]


@dataclass
class DimensionResult:
    score: float
    confidence: float
    probabilities: list
    legend: dict


@dataclass
class ResumeResult:
    file: str
    quality: DimensionResult | None
    fit: DimensionResult | None
    error: str | None


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        from docx import Document

        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace")
    raise ValueError(f"unsupported file type: {suffix}")


def collect_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(f for f in p.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS))
        elif p.is_file():
            files.append(p)
        else:
            print(f"warning: path not found, skipping: {raw}", file=sys.stderr)
    return files


def evaluate_resume(path: Path, role: str) -> ResumeResult:
    try:
        text = extract_text(path)
    except Exception as exc:
        return ResumeResult(file=str(path), quality=None, fit=None, error=f"extraction failed: {exc}")

    if not text.strip():
        return ResumeResult(file=str(path), quality=None, fit=None, error="no extractable text")

    try:
        with TypeSafeClient() as client:
            response = client.system_one(
                state={"resume": text, "target_role": role},
                questions={
                    "quality": Score(
                        instructions=(
                            "Rate the overall quality and clarity of `resume` as a written "
                            "document: how clear, well-organized, and professionally "
                            "presented it is."
                        ),
                        criteria=QUALITY_CRITERIA,
                    ),
                    "fit": Score(
                        instructions=(
                            "Given the requirements described in `target_role`, rate how "
                            "well the experience and skills in `resume` match those "
                            "requirements."
                        ),
                        criteria=FIT_CRITERIA,
                    ),
                },
            )
    except Exception as exc:
        return ResumeResult(file=str(path), quality=None, fit=None, error=f"API error: {exc}")

    quality = response.scores["quality"]
    fit = response.scores["fit"]
    return ResumeResult(
        file=str(path),
        quality=DimensionResult(quality.score, quality.confidence, quality.probabilities, quality.legend),
        fit=DimensionResult(fit.score, fit.confidence, fit.probabilities, fit.legend),
        error=None,
    )


def print_table(results: list[ResumeResult]) -> None:
    header = f"{'File':<40} {'Quality':>10} {'Fit':>10}   Notes"
    print(header)
    print("-" * len(header))
    for r in results:
        if r.error:
            print(f"{r.file:<40} {'--':>10} {'--':>10}   {r.error}")
        else:
            print(f"{r.file:<40} {r.quality.score:>10.2f} {r.fit.score:>10.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate resumes against a target role using TypeSafe/Jev.")
    parser.add_argument(
        "paths",
        nargs="+",
        help="Resume files (.pdf, .docx, .txt, .md) or directories containing them",
    )
    parser.add_argument("--role", required=True, help="Target role/job description text to score fit against")
    parser.add_argument("--output", help="Optional path to write full results as JSON")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent API requests (default: 4)")
    args = parser.parse_args()

    files = collect_files(args.paths)
    if not files:
        print("No resume files found.", file=sys.stderr)
        sys.exit(1)

    results: list[ResumeResult] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(evaluate_resume, path, args.role): path for path in files}
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r.file)

    print_table(results)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        print(f"\nFull results written to {args.output}")


if __name__ == "__main__":
    main()
