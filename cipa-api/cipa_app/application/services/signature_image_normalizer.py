"""Normalização de PNG de assinatura para exibição sobre marca d'água."""

from __future__ import annotations

import io

from PIL import Image as PillowImage


def transparent_signature_png(raw: bytes) -> bytes:
    """Remove fundo branco de assinaturas, preservando o traço."""
    try:
        with PillowImage.open(io.BytesIO(raw)) as source:
            image = source.convert("RGBA")
            pixels = image.load()
            for y in range(image.height):
                for x in range(image.width):
                    red, green, blue, alpha = pixels[x, y]
                    if red >= 245 and green >= 245 and blue >= 245:
                        pixels[x, y] = (red, green, blue, 0)
            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()
    except Exception:
        return raw
