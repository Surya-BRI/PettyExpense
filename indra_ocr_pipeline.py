"""
Indra OCR Pipeline
Converts PDF/image files to markdown, text, or structured JSON with bounding boxes.
Usage:
    python indra_ocr_pipeline.py <file_or_folder> [--format md|text|json] [--out <output_dir>]
"""

import argparse
import json
import sys
from pathlib import Path


def run_pipeline(input_path: str, output_format: str = "md", output_dir: str | None = None, threads: int = 4):
    try:
        import indra_ocr
    except ImportError:
        print("indra-ocr not installed. Run: pip install indra-ocr")
        sys.exit(1)

    input_path = Path(input_path)
    files = []

    if input_path.is_dir():
        files = list(input_path.glob("*.pdf")) + list(input_path.glob("*.png")) + list(input_path.glob("*.jpg"))
    elif input_path.is_file():
        files = [input_path]
    else:
        print(f"Path not found: {input_path}")
        sys.exit(1)

    if not files:
        print("No PDF/PNG/JPG files found.")
        sys.exit(1)

    out_dir = Path(output_dir) if output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    conv = indra_ocr.load(threads=threads)

    for file in files:
        print(f"\n--- Processing: {file.name} ---")
        results = {}

        for i, page in conv.convert(str(file)):
            print(f"  Page {i+1} | source={page.source} | {page.timings.get('total_ms', '?')} ms")

            if output_format == "md":
                content = page.markdown
            elif output_format == "text":
                content = page.text
            elif output_format == "json":
                content = json.dumps({
                    "page": i + 1,
                    "source": page.source,
                    "rotation": page.rotation,
                    "skew": page.skew,
                    "timings": page.timings,
                    "blocks": page.blocks,
                    "lines": [
                        {"text": line.text, "conf": line.conf, "box": line.box}
                        for line in page.lines
                    ],
                }, indent=2)
            else:
                content = page.markdown

            results[i + 1] = content

        if out_dir:
            ext = "json" if output_format == "json" else output_format
            out_file = out_dir / f"{file.stem}.{ext}"
            with open(out_file, "w", encoding="utf-8") as f:
                if output_format == "json":
                    json.dump(results, f, indent=2, ensure_ascii=False)
                else:
                    for page_num, text in results.items():
                        f.write(f"\n\n<!-- Page {page_num} -->\n{text}")
            print(f"  Saved -> {out_file}")
        else:
            for page_num, text in results.items():
                print(f"\n[Page {page_num}]\n{text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indra OCR Pipeline")
    parser.add_argument("input", help="PDF/image file or folder")
    parser.add_argument("--format", choices=["md", "text", "json"], default="md", help="Output format (default: md)")
    parser.add_argument("--out", default=None, help="Output directory (prints to stdout if omitted)")
    parser.add_argument("--threads", type=int, default=4, help="CPU threads (default: 4)")
    args = parser.parse_args()

    run_pipeline(args.input, args.format, args.out, args.threads)
