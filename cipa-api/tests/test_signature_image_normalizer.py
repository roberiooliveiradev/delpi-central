import io

from PIL import Image as PillowImage

from cipa_app.application.services.signature_image_normalizer import transparent_signature_png


def test_transparent_signature_png_clears_white_background():
    image = PillowImage.new("RGBA", (3, 1), (255, 255, 255, 255))
    image.putpixel((1, 0), (20, 30, 40, 255))
    raw = io.BytesIO()
    image.save(raw, format="PNG")

    normalized = PillowImage.open(io.BytesIO(transparent_signature_png(raw.getvalue())))

    assert normalized.getpixel((0, 0))[3] == 0
    assert normalized.getpixel((1, 0))[3] == 255
    assert normalized.getpixel((2, 0))[3] == 0
