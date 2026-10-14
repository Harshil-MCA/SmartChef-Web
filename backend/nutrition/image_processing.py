"""Small, dependency-optional helpers for reading a scale display.

OCR output frequently also contains the scale capacity (for example 5000 g)
and resolution (d=1 g).  This module deliberately scores display candidates
instead of accepting the first number in the text.
"""
from __future__ import annotations

import re
from pathlib import Path
from io import BytesIO
from typing import Iterable

from PIL import Image, ImageEnhance, ImageOps


def normalise_weight(value: object) -> float | None:
    """Convert a genuine positive gram value to grams."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if 0 < parsed <= 10_000 else None


def weight_from_ocr_text(text: str) -> float | None:
    """Return the most likely display value from OCR text, never capacity text."""
    candidates: list[tuple[float, float]] = []
    # OCR may split a display into digit fragments ("1 2 0 g" or one digit
    # per line).  Score the reconstructed display before individual digits.
    for match in re.finditer(r"(?<!\d)(\d(?:\s+\d){1,4})\s*(kg|g|mg)\b", text.lower()):
        grams = float(re.sub(r"\s+", "", match.group(1))) * {"kg": 1000, "g": 1, "mg": 0.001}[match.group(2)]
        if normalise_weight(grams):
            candidates.append((8, grams))
    for line_index, raw_line in enumerate(text.splitlines() or [text]):
        line = raw_line.lower().replace("o", "0").replace("l", "1")
        if re.search(r"(?:max\.?|capacity|d\s*=|division)", line):
            continue
        for match in re.finditer(r"(?<!\d)(\d{1,5}(?:[.,]\d+)?)\s*(kg|g|mg)?\b", line):
            number = float(match.group(1).replace(",", "."))
            unit = match.group(2) or "g"
            grams = number * {"kg": 1000, "g": 1, "mg": 0.001}[unit]
            if not normalise_weight(grams):
                continue
            # A unit, an isolated short line, and lower image OCR are strong
            # signals for a digital display.  Large capacity-like values lose.
            score = (4 if match.group(2) else 1) + (3 if len(re.findall(r"\d", line)) <= 4 else 0)
            score += min(line_index, 4) * 0.25
            if grams >= 1000:
                score -= 4
            candidates.append((score, grams))
    return max(candidates, default=(0, None), key=lambda item: item[0])[1]


def read_scale_weight(image_bytes: bytes) -> float | None:
    """Try installed Tesseract on high-contrast lower-image variants.

    Tesseract is intentionally optional: deployments already using Gemini keep
    working, while installations with local OCR gain a fast, private first pass.
    """
    try:
        source = ImageOps.exif_transpose(Image.open(BytesIO(image_bytes))).convert("RGB")
    except (OSError, ValueError):
        return None

    # Many domestic scales use a blue LCD with black seven-segment digits.
    # Reading that display structurally is more reliable than asking general
    # OCR to choose between the display and printed ``Max. 5000g`` / ``d=1g``
    # labels. This is display-driven: it does not depend on a food name,
    # filename, or expected weight.
    lcd_weight = _read_blue_lcd_weight(source)
    if lcd_weight is not None:
        return lcd_weight

    try:
        import pytesseract  # type: ignore[import-not-found]
        from django.conf import settings
    except ImportError:
        return None
    try:
        configured_path = getattr(settings, "TESSERACT_CMD", "")
        default_windows_path = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
        if configured_path:
            pytesseract.pytesseract.tesseract_cmd = configured_path
        elif default_windows_path.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(default_windows_path)
        grayscale = source.convert("L")
        lower = grayscale.crop((0, int(grayscale.height * 0.45), grayscale.width, grayscale.height))
        lower.thumbnail((1800, 1000), Image.Resampling.LANCZOS)
        full = grayscale.copy()
        full.thumbnail((1800, 1400), Image.Resampling.LANCZOS)
        # The display is usually centered low on a domestic scale.  Keep this
        # focused crop alongside the full/lower views rather than assuming a
        # single camera composition.
        lcd = lower.crop((int(lower.width * 0.18), int(lower.height * 0.20), int(lower.width * 0.82), int(lower.height * 0.82)))
        lcd = lcd.resize((max(1, lcd.width * 2), max(1, lcd.height * 2)), Image.Resampling.LANCZOS)
        variants: Iterable[Image.Image] = (
            full,
            lower,
            ImageEnhance.Contrast(lower).enhance(2.5),
            lower.point(lambda value: 255 if value > 135 else 0),
            ImageEnhance.Contrast(lcd).enhance(3.0),
        )
        values: list[tuple[float, bool]] = []
        for variant in variants:
            text = pytesseract.image_to_string(variant, config="--psm 11")
            value = weight_from_ocr_text(text)
            if value is not None:
                # A number without a unit from one OCR pass is commonly text
                # printed on the food, packaging, or background. Only accept
                # OCR fallback values when multiple image variants agree and
                # at least one pass identified an explicit scale unit.
                has_unit = bool(re.search(r"(?<![a-z])(kg|g)\b", text.lower()))
                values.append((value, has_unit))
        return _consensus_ocr_weight(values)
    except (OSError, ValueError, RuntimeError):
        return None


def _consensus_ocr_weight(values: list[tuple[float, bool]]) -> float | None:
    if len(values) < 2 or not any(has_unit for _, has_unit in values):
        return None

    for value, _ in values:
        agreeing = [candidate for candidate, _ in values if abs(candidate - value) <= 0.5]
        if len(agreeing) >= 2:
            return value
    return None


def _read_blue_lcd_weight(source: Image.Image) -> float | None:
    """Read black seven-segment digits inside the largest blue LCD component."""
    component = _largest_blue_component(source)
    if component is None:
        return None

    left, top, right, bottom = component
    lcd = source.convert("L").crop(component)
    width, height = lcd.size
    if width < 80 or height < 35:
        return None

    # Segment ink is near black, while the illuminated blue panel is much
    # lighter in grayscale. Keep the central display band and identify its
    # digit columns by their dark-pixel density.
    pixels = lcd.load()
    y_start = max(1, int(height * 0.08))
    y_end = min(height - 1, int(height * 0.92))
    min_ink_per_column = max(3, int((y_end - y_start) * 0.025))
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for x in range(width + 1):
        ink = (
            sum(1 for y in range(y_start, y_end) if pixels[x, y] < 60)
            if x < width
            else 0
        )
        if ink >= min_ink_per_column and start is None:
            start = x
        elif ink < min_ink_per_column and start is not None:
            runs.append((start, x))
            start = None

    # Ignore LCD borders and the small unit glyph. A seven-segment ``1`` is
    # naturally narrow, so retain components down to 4.5% of display width.
    digit_runs = [
        run
        for run in runs
        if run[0] > int(width * 0.15)
        and run[1] < int(width * 0.90)
        and run[1] - run[0] >= max(8, int(width * 0.045))
    ]
    if not digit_runs or len(digit_runs) > 5:
        return None

    typical_width = sorted(end - begin for begin, end in digit_runs)[len(digit_runs) // 2]
    digits: list[str] = []
    for begin, end in digit_runs:
        digit = _decode_seven_segment_digit(
            lcd.crop((begin, y_start, end, y_end)),
            narrow=(end - begin) < typical_width * 0.65,
        )
        if digit is None:
            return None
        digits.append(digit)

    return normalise_weight("".join(digits))


def _largest_blue_component(source: Image.Image) -> tuple[int, int, int, int] | None:
    """Return the largest contiguous illuminated-blue region in the lower image."""
    width, height = source.size
    pixels = source.load()
    mask: set[tuple[int, int]] = set()
    for y in range(int(height * 0.45), height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            if blue > 100 and blue > red + 30 and blue > green + 20:
                mask.add((x, y))

    best: tuple[int, int, int, int] | None = None
    best_size = 0
    while mask:
        first = mask.pop()
        queue = [first]
        left = right = first[0]
        top = bottom = first[1]
        size = 0
        while queue:
            x, y = queue.pop()
            size += 1
            left = min(left, x)
            right = max(right, x)
            top = min(top, y)
            bottom = max(bottom, y)
            for neighbour in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbour in mask:
                    mask.remove(neighbour)
                    queue.append(neighbour)
        if size > best_size:
            best_size = size
            best = (left, top, right + 1, bottom + 1)

    return best if best_size >= width * height * 0.01 else None


def _decode_seven_segment_digit(image: Image.Image, *, narrow: bool) -> str | None:
    if narrow:
        return "1"

    grayscale = image.convert("L")
    width, height = grayscale.size
    pixels = grayscale.load()
    regions = {
        "a": (0.25, 0.75, 0.04, 0.17),
        "b": (0.72, 0.96, 0.18, 0.42),
        "c": (0.72, 0.96, 0.58, 0.82),
        "d": (0.25, 0.75, 0.84, 0.97),
        "e": (0.04, 0.28, 0.58, 0.82),
        "f": (0.04, 0.28, 0.18, 0.42),
        "g": (0.25, 0.75, 0.45, 0.57),
    }
    active: set[str] = set()
    for name, (left, right, top, bottom) in regions.items():
        x0, x1 = int(width * left), max(int(width * right), int(width * left) + 1)
        y0, y1 = int(height * top), max(int(height * bottom), int(height * top) + 1)
        total = max(1, (x1 - x0) * (y1 - y0))
        ink = sum(1 for y in range(y0, y1) for x in range(x0, x1) if pixels[x, y] < 60)
        if ink / total >= 0.35:
            active.add(name)

    glyphs = {
        frozenset("abcdef"): "0",
        frozenset("bc"): "1",
        frozenset("abdeg"): "2",
        frozenset("abcdg"): "3",
        frozenset("bcfg"): "4",
        frozenset("acdfg"): "5",
        frozenset("acdefg"): "6",
        frozenset("abc"): "7",
        frozenset("abcdefg"): "8",
        frozenset("abcdfg"): "9",
    }
    return glyphs.get(frozenset(active))
