import os
import requests

BASE = "https://huggingface.co/onnx-community/nsfw_image_detection-ONNX/resolve/main/onnx/"
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)
DEST = os.path.join(MODEL_DIR, "nsfw_detector_fp32.onnx")

def download(url):
    tmp = DEST + ".part"
    with requests.get(url, stream=True, allow_redirects=True) as r:
        if r.status_code != 200:
            print(f"Error {r.status_code} en {url}")
            return False
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"Descargado: {done / total * 100:.1f}%", end="\r")
    os.replace(tmp, DEST)
    print(f"\nListo: {DEST} ({os.path.getsize(DEST) // (1024 * 1024)} MB)")
    return True

if __name__ == "__main__":
    download(BASE + "model.onnx")