from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from django.conf import settings
from PIL import Image, ImageEnhance, ImageOps


LABELS = [
    "apple", "banana", "beetroot", "bell pepper", "cabbage", "capsicum",
    "carrot", "cauliflower", "chilli pepper", "corn", "cucumber", "eggplant",
    "garlic", "ginger", "grapes", "jalepeno", "kiwi", "lemon", "lettuce",
    "mango", "onion", "orange", "paprika", "pear", "peas", "pineapple",
    "pomegranate", "potato", "raddish", "soy beans", "spinach", "sweetcorn",
    "sweetpotato", "tomato", "turnip", "watermelon",
]


@dataclass
class DetectionResult:
    items: list[dict[str, Any]]
    candidates: list[dict[str, Any]]
    confidence: float
    margin: float
    message: str
    status: str


class IngredientModelError(RuntimeError):
    pass


class IngredientDetectionService:
    minimum_confidence = 0.55
    minimum_margin = 0.15

    def __init__(self) -> None:
        self._interpreter = None

    def detect(
        self,
        image_path: str,
        filename: str = "",
        manual_corrections: list[str] | None = None,
    ) -> DetectionResult:
        confirmed = [item.strip().lower() for item in (manual_corrections or []) if item.strip()]
        if confirmed:
            items = [{"name": item, "confidence": 1.0} for item in dict.fromkeys(confirmed)]
            return DetectionResult(items, items, 1.0, 1.0, "Using the ingredients confirmed by the user.", "success")

        interpreter = self._load_interpreter()
        input_details = interpreter.get_input_details()[0]
        output_details = interpreter.get_output_details()[0]
        input_shape = input_details["shape"].tolist()
        if input_shape != [1, 224, 224, 3]:
            raise IngredientModelError(f"Unsupported ingredient model input shape: {input_shape}")

        scores = np.mean([self._infer(interpreter, output_details, variant) for variant in self._variants(image_path)], axis=0)
        if len(scores) != len(LABELS):
            raise IngredientModelError(f"Model output has {len(scores)} classes; expected {len(LABELS)}.")
        ranked = np.argsort(scores)[::-1]
        best_index = int(ranked[0])
        best_score = float(scores[best_index])
        second_score = float(scores[int(ranked[1])]) if len(ranked) > 1 else 0.0
        margin = max(0.0, best_score - second_score)
        candidates = [
            {"name": LABELS[int(index)], "confidence": round(float(scores[int(index)]), 4)}
            for index in ranked[:3]
        ]
        reliable = math.isfinite(best_score) and (
            best_score >= self.minimum_confidence and margin >= self.minimum_margin
        )
        if not reliable:
            return DetectionResult(
                [], candidates, best_score, margin,
                "The ingredient is not confidently recognized by the trained dataset model. Please confirm it manually.",
                "unknown",
            )
        item = {"name": LABELS[best_index], "confidence": round(best_score, 4)}
        return DetectionResult(
            [item], candidates, best_score, margin,
            f"Detected {item['name']} from the trained ingredient dataset model.", "success",
        )

    def _load_interpreter(self):
        if self._interpreter is not None:
            return self._interpreter
        model_path = Path(settings.INGREDIENT_MODEL_PATH)
        if not model_path.is_file():
            raise IngredientModelError(f"Ingredient model not found: {model_path}")
        try:
            from ai_edge_litert.interpreter import Interpreter
        except ImportError:
            try:
                from tflite_runtime.interpreter import Interpreter
            except ImportError as error:
                raise IngredientModelError("The backend LiteRT runtime is not installed. Install backend requirements.") from error
        self._interpreter = Interpreter(model_path=str(model_path), num_threads=2)
        self._interpreter.allocate_tensors()
        return self._interpreter

    def _infer(self, interpreter, output_details, image: np.ndarray) -> np.ndarray:
        input_details = interpreter.get_input_details()[0]
        interpreter.set_tensor(input_details["index"], image[None, ...].astype(np.float32))
        interpreter.invoke()
        output = interpreter.get_tensor(output_details["index"]).reshape(-1).astype(np.float32)
        if not np.isfinite(output).all():
            raise IngredientModelError("Ingredient model returned invalid scores.")
        if not (np.all((output >= 0) & (output <= 1)) and abs(float(output.sum()) - 1.0) < 0.25):
            output = np.exp(output - output.max())
            output /= output.sum()
        return output

    def _variants(self, image_path: str) -> list[np.ndarray]:
        with Image.open(image_path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            variants = [self._crop_resize(image)]
            tight = self._center_crop(image, 0.88)
            variants.append(self._crop_resize(tight))
            adjusted = ImageEnhance.Contrast(image).enhance(1.15)
            adjusted = ImageEnhance.Brightness(adjusted).enhance(1.02)
            adjusted = ImageEnhance.Color(adjusted).enhance(1.04)
            variants.append(self._crop_resize(adjusted))
            return [np.asarray(item, dtype=np.float32) / 255.0 for item in variants]

    def _crop_resize(self, image: Image.Image) -> Image.Image:
        return self._center_crop(image, min(image.width, image.height)).resize((224, 224), Image.Resampling.BILINEAR)

    def _center_crop(self, image: Image.Image, size_or_ratio: float) -> Image.Image:
        if size_or_ratio <= 1:
            width = max(1, round(image.width * size_or_ratio))
            height = max(1, round(image.height * size_or_ratio))
        else:
            width = height = min(image.width, image.height)
        left = max(0, (image.width - width) // 2)
        top = max(0, (image.height - height) // 2)
        return image.crop((left, top, left + width, top + height))
