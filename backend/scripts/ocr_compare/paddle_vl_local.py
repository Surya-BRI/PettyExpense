"""Standalone PaddleOCR-VL-1.6 single-image benchmark. Runs under the ISOLATED venv
(C:\\Users\\Tej\\ocrs\\paddle-vl-venv), never backend/.venv. Invoked as a fresh
subprocess per image so cold-start time and peak RAM are real, not skewed by
model caching. Usage: python paddle_vl_local.py <image_path>
Prints one JSON object to stdout. Never falls back to fake data — on failure,
prints {"engine": "paddle_vl", "error": "...", "traceback": "..."} and exits 1.
"""
import json
import sys
import threading
import time
import traceback

PEAK_RSS_MB = 0.0
_STOP = False


def _poll_rss() -> None:
    global PEAK_RSS_MB
    import psutil

    proc = psutil.Process()
    while not _STOP:
        rss_mb = proc.memory_info().rss / (1024 * 1024)
        if rss_mb > PEAK_RSS_MB:
            PEAK_RSS_MB = rss_mb
        time.sleep(0.05)


def main() -> None:
    global _STOP
    image_path = sys.argv[1]

    watcher = threading.Thread(target=_poll_rss, daemon=True)
    watcher.start()

    t0 = time.time()
    try:
        from paddleocr import PaddleOCRVL

        pipeline = PaddleOCRVL()
        cold_start_s = time.time() - t0

        t1 = time.time()
        results = pipeline.predict(image_path)
        inference_s = time.time() - t1

        blocks = []
        raw_text_parts = []
        layout_boxes = []
        for res in results:
            res_json = res.json["res"]
            layout = res_json.get("layout_det_res") or {}
            for box in layout.get("boxes") or []:
                layout_boxes.append(
                    {
                        "coordinate": box.get("coordinate"),
                        "score": box.get("score"),
                        "label": box.get("label"),
                        "cls_id": box.get("cls_id"),
                    }
                )
            for block in res_json.get("parsing_res_list") or []:
                content = block.get("block_content") or ""
                blocks.append(
                    {
                        "block_bbox": block.get("block_bbox"),
                        "block_label": block.get("block_label"),
                        "block_content": content,
                        # PaddleOCRVLBlock (paddlex/inference/pipelines/paddleocr_vl/result.py) has
                        # no confidence attribute at all — this key is always absent, verified from source.
                        "block_confidence": block.get("block_confidence"),
                    }
                )
                if content.strip():
                    raw_text_parts.append(content)

        _STOP = True
        watcher.join(timeout=1)

        print(
            json.dumps(
                {
                    "engine": "paddle_vl",
                    "model": "PaddleOCR-VL-1.6",
                    "image": image_path,
                    "raw_text": "\n".join(raw_text_parts),
                    "blocks": blocks,
                    "layout_boxes": layout_boxes,
                    "bbox_granularity": "block (layout region) — no per-word or per-line boxes",
                    "cold_start_s": round(cold_start_s, 3),
                    "inference_s": round(inference_s, 3),
                    "total_s": round(time.time() - t0, 3),
                    "peak_rss_mb": round(PEAK_RSS_MB, 1),
                    "error": None,
                }
            )
        )
    except Exception as exc:
        _STOP = True
        print(
            json.dumps(
                {
                    "engine": "paddle_vl",
                    "model": "PaddleOCR-VL-1.6",
                    "image": image_path,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                    "peak_rss_mb": round(PEAK_RSS_MB, 1),
                }
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
