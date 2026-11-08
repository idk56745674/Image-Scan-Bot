import asyncio
import io

from PIL import Image, ImageOps

import config


def _compress(data: bytes) -> bytes:
    with Image.open(io.BytesIO(data)) as img:
        img.seek(0)
        original_format = img.format
        img = ImageOps.exif_transpose(img)


        max_w, max_h = config.MAX_IMAGE_SIZE
        if img.height > img.width:
            max_w, max_h = max_h, max_w

        fits = img.width <= max_w and img.height <= max_h
        if fits and original_format in ("PNG", "JPEG"):
            return data

        img.thumbnail((max_w, max_h), Image.LANCZOS)

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert("RGB")

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=config.JPEG_QUALITY, optimize=True)
        return out.getvalue()


async def compress_image(data: bytes) -> bytes:
    try:
        return await asyncio.to_thread(_compress, data)
    except Exception as e:
        print(f"Image compression failed, using original: {e}")
        return data
