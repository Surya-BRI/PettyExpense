"""Benchmarks OCR latency + concurrent throughput against the sample bill photos.

Measures the real production RapidOCR pipeline (`services.ocr_service.run`) today —
sequential (one request at a time) and concurrent (simulating several mobile users
hitting the endpoint around the same time). The Surya-2 section only runs once a
self-hosted inference endpoint actually exists (pass --surya-endpoint or set
SURYA_ENDPOINT) — there is no self-hosted Surya-2 deployment in this repo yet, so
until then it prints a skip notice instead of fabricating numbers.

Usage: python scripts/ocr_compare/benchmark_load.py [ksa|dubai|all] [--mode auto|en|ar]
       [--repeats 3] [--concurrency 8] [--surya-endpoint http://host:port/path]
"""
import argparse
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Windows terminals default stdout to cp1252, which can't encode Arabic text.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))  # for services.ocr_service
load_dotenv(BACKEND_ROOT / ".env")

from services.ocr_service import ocr_service  # noqa: E402  (production entrypoint, reused as-is)

SAMPLES_DIR = BACKEND_ROOT.parent / "assets"
REGIONS = ("ksa", "dubai")


def _load_images(folder: str) -> list[Path]:
    roots = [SAMPLES_DIR / folder] if folder != "all" else [SAMPLES_DIR / r for r in REGIONS]
    return sorted(
        p for root in roots for p in root.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )


def _percentile(values: list[float], pct: float) -> float:
    values = sorted(values)
    k = (len(values) - 1) * pct
    f, c = int(k), min(int(k) + 1, len(values) - 1)
    return values[f] if f == c else values[f] + (values[c] - values[f]) * (k - f)


def _summarize(label: str, latencies: list[float], wall_seconds: float) -> None:
    n = len(latencies)
    print(f"\n-- {label} --")
    print(f"  requests: {n}")
    print(f"  wall time: {wall_seconds:.2f}s   throughput: {n / wall_seconds:.2f} img/sec")
    print(
        f"  avg: {statistics.mean(latencies) * 1000:.0f}ms   "
        f"p50: {_percentile(latencies, 0.5) * 1000:.0f}ms   "
        f"p95: {_percentile(latencies, 0.95) * 1000:.0f}ms   "
        f"max: {max(latencies) * 1000:.0f}ms"
    )


def _run_one_rapidocr(image_bytes: bytes, name: str, mode: str) -> float:
    start = time.perf_counter()
    ocr_service.run(image_bytes, name, mode=mode)
    return time.perf_counter() - start


def benchmark_sequential(payloads: list[tuple[bytes, str]], mode: str) -> list[float]:
    return [_run_one_rapidocr(image_bytes, name, mode) for image_bytes, name in payloads]


def benchmark_concurrent(payloads: list[tuple[bytes, str]], mode: str, concurrency: int) -> tuple[list[float], float]:
    latencies = []
    start_wall = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(_run_one_rapidocr, image_bytes, name, mode) for image_bytes, name in payloads]
        for f in as_completed(futures):
            latencies.append(f.result())
    return latencies, time.perf_counter() - start_wall


def run_surya_benchmark(payloads: list[tuple[bytes, str]], concurrency: int, endpoint: str | None) -> None:
    if not endpoint:
        print("\n-- Surya-2 (self-hosted) --")
        print("  SKIPPED: no self-hosted Surya-2 endpoint given.")
        print("  Once Surya-2 is deployed on the new GPU box behind an HTTP inference endpoint,")
        print("  re-run with --surya-endpoint http://<host>:<port>/<path> (or SURYA_ENDPOINT env var)")
        print("  for a real, comparable number instead of an estimate.")
        return

    import requests  # local import — only needed for this path, not a core backend dependency

    def _call(image_bytes: bytes, name: str) -> float:
        start = time.perf_counter()
        resp = requests.post(endpoint, files={"file": (name, image_bytes)}, timeout=30)
        resp.raise_for_status()
        return time.perf_counter() - start

    latencies = []
    start_wall = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(_call, b, n) for b, n in payloads]
        for f in as_completed(futures):
            latencies.append(f.result())
    wall = time.perf_counter() - start_wall
    _summarize(f"Surya-2 self-hosted (concurrency={concurrency})", latencies, wall)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", nargs="?", default="all", help="assets/ subfolder: ksa, dubai, or all")
    parser.add_argument("--mode", default="auto", choices=("auto", "en", "ar"))
    parser.add_argument("--repeats", type=int, default=3, help="times each sample image is sent, for a stable average")
    parser.add_argument("--concurrency", type=int, default=8, help="simulated concurrent mobile users")
    parser.add_argument("--surya-endpoint", default=None, help="self-hosted Surya-2 HTTP endpoint, once deployed")
    args = parser.parse_args()

    images = _load_images(args.folder)
    if not images:
        print(f"No sample images found under assets/{args.folder} — nothing to benchmark.")
        return

    payloads = [(p.read_bytes(), p.name) for p in images] * args.repeats
    print(
        f"Benchmarking {len(images)} unique image(s) x {args.repeats} repeat(s) "
        f"= {len(payloads)} requests, mode={args.mode}"
    )

    seq_latencies = benchmark_sequential(payloads, args.mode)
    _summarize("RapidOCR -- sequential (1 request at a time, today's box)", seq_latencies, sum(seq_latencies))

    conc_latencies, conc_wall = benchmark_concurrent(payloads, args.mode, args.concurrency)
    _summarize(
        f"RapidOCR -- concurrent (concurrency={args.concurrency}, simulating multiple mobile users, today's box)",
        conc_latencies,
        conc_wall,
    )

    run_surya_benchmark(payloads, args.concurrency, args.surya_endpoint or os.environ.get("SURYA_ENDPOINT"))


if __name__ == "__main__":
    main()
