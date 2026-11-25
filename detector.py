import os
import time
import numpy as np
from PIL import Image
import onnxruntime as ort

_MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
_FP32 = os.path.join(_MODELS, "nsfw_detector_fp32.onnx")
MODEL_PATH = _FP32 if os.path.exists(_FP32) else os.path.join(_MODELS, "nsfw_detector.onnx")

class NSFWDetector:
    def __init__(self, model_path=MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo ONNX no encontrado en: {model_path}")
        
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        # Priority 1: DirectML (Hardware GPU Acceleration on NVIDIA/AMD/Intel)
        # Priority 2: CPU Fallback
        available_providers = ort.get_available_providers()
        preferred_providers = []
        if 'DmlExecutionProvider' in available_providers:
            preferred_providers.append('DmlExecutionProvider')
        preferred_providers.append('CPUExecutionProvider')

        self.session = ort.InferenceSession(model_path, sess_options=opts, providers=preferred_providers)
        self.active_provider = self.session.get_providers()[0]
        self.input_name = self.session.get_inputs()[0].name
        
        # Mean and std for ViT feature extractor
        self.mean = np.array([0.5, 0.5, 0.5], dtype=np.float32).reshape(1, 3, 1, 1)
        self.std = np.array([0.5, 0.5, 0.5], dtype=np.float32).reshape(1, 3, 1, 1)

        # Warmup GPU
        dummy = np.zeros((1, 3, 224, 224), dtype=np.float32)
        try:
            self.session.run(None, {self.input_name: dummy})
        except Exception:
            pass

    def preprocess(self, pil_image: Image.Image) -> np.ndarray:
        img = pil_image.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
        arr = np.transpose(arr, (2, 0, 1))
        arr = np.expand_dims(arr, axis=0)
        arr = (arr - self.mean) / self.std
        return arr

    def predict(self, pil_image: Image.Image):
        t0 = time.perf_counter()
        inp = self.preprocess(pil_image)
        outputs = self.session.run(None, {self.input_name: inp})
        logits = outputs[0][0]
        
        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        
        latency = (time.perf_counter() - t0) * 1000.0
        
        return {
            "normal": float(probs[0]),
            "nsfw": float(probs[1]),
            "latency_ms": latency,
            "provider": self.active_provider
        }

if __name__ == "__main__":
    print("Inicializando detector con aceleración por hardware...")
    detector = NSFWDetector()
    print(f"Modelo cargado: {MODEL_PATH}")
    print(f"Dispositivo activo: {detector.active_provider}")
    test_img = Image.new("RGB", (224, 224), color=(120, 180, 240))
    res = detector.predict(test_img)
    print(f"Resultado test: {res}")