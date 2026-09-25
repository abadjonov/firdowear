"""Yuklangan rasmni avtomatik siqish: WebP thumbnail (katalog) va katta rasm (mahsulot sahifasi)."""
import io
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

THUMB = (600, 800)     # katalog kartochkasi (3:4)
LARGE = (1200, 1600)   # mahsulot sahifasi
QUALITY = 82


def _to_webp(img: Image.Image, size: tuple[int, int]) -> ContentFile:
    im = ImageOps.exif_transpose(img)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGB")
    im.thumbnail(size, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=QUALITY, method=6)
    return ContentFile(buf.getvalue())


def build_variants(field_file):
    """(thumb_file, large_file, thumb_name, large_name) qaytaradi."""
    field_file.open()
    img = Image.open(field_file)
    img.load()
    stem = Path(field_file.name).stem
    return (
        _to_webp(img, THUMB), _to_webp(img, LARGE),
        f"{stem}_thumb.webp", f"{stem}_large.webp",
    )
