import os
import requests

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "nsfw_detector.onnx")

MODEL_URL = "https://huggingface.co/onnx-community/nsfw_image_detection-ONNX/resolve/main/onnx/model_quantized.onnx"

def download_model():
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 10 * 1024 * 1024:
        print(f"Modelo ya existe: {MODEL_PATH}")
        return

    print(f"Descargando modelo ONNX ({MODEL_URL})...")
    resp = requests.get(MODEL_URL, stream=True, allow_redirects=True)
    resp.raise_for_status()

    total_size = int(resp.headers.get('content-length', 0))
    downloaded = 0

    with open(MODEL_PATH, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 512):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(f"Descargado: {pct:.1f}% ({downloaded // (1024*1024)} MB)", end="\r")

    print(f"\nDescarga completada con éxito: {MODEL_PATH}")

if __name__ == "__main__":
    download_model()
