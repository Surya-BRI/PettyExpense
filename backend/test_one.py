from services.ocr_service import OcrService
import json

# OcrService.run() takes image BYTES, not a file path.
with open("../assets/dubai/enoc_test.jpg", "rb") as f:
    image_bytes = f.read()

result = OcrService().run(image_bytes, "enoc_test.jpg", mode="auto")
print(json.dumps(result, indent=2, ensure_ascii=False))
