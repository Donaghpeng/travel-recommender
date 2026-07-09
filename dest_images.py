"""
dest_images.py — 目的地图片
优先使用 static/img-hosting/ 本地图片，没有则生成 SVG
"""
import os, base64, mimetypes, io
from PIL import Image

IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "img-hosting")

# Type → gradient pairs for SVG fallback
GRADIENTS = {
    "Beach": ("#0077b6", "#00b4d8"),
    "Island": ("#0096c7", "#48cae4"),
    "Mountain": ("#2d6a4f", "#52b788"),
    "Nature": ("#1b4332", "#40916c"),
    "City": ("#3a0ca3", "#4361ee"),
    "Culture": ("#7209b7", "#b5179e"),
    "AncientTown": ("#7f2d2d", "#c1121f"),
    "Food": ("#e85d04", "#f48c06"),
    "Adventure": ("#d00000", "#e63946"),
}


def get_dest_image(name, name_cn=None, dest_type=None):
    """Get image: local file first, SVG fallback"""
    display_name = name_cn or name
    simple = name.split("(")[0].split("/")[0].strip()
    
    # 1. Try local file (Chinese name)
    for possible_name in [display_name, simple]:
        clean = "".join(c for c in possible_name if c not in '\\/*?:"<>|') + ".jpg"
        fpath = os.path.join(IMG_DIR, clean)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                img_data = f.read()
            # Resize large images (>300KB) to max 800px width
            if len(img_data) > 300 * 1024:
                try:
                    img = Image.open(io.BytesIO(img_data))
                    max_w, max_h = 800, 500
                    if img.width > max_w or img.height > max_h:
                        ratio = min(max_w / img.width, max_h / img.height)
                        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=80, optimize=True)
                    img_data = buf.getvalue()
                except Exception:
                    pass  # Fall back to original if resize fails
            b64 = base64.b64encode(img_data).decode("utf-8")
            ext = "jpeg" if clean.endswith(".jpg") else "png"
            return {"url": f"data:image/{ext};base64,{b64}", "source": "local"}
    
    # 2. SVG fallback (zero external dependencies)
    t = dest_type or "City"
    c1, c2 = GRADIENTS.get(t, ("#667eea", "#764ba2"))
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{c1}"/>
      <stop offset="100%" style="stop-color:{c2}"/>
    </linearGradient>
  </defs>
  <rect width="600" height="350" fill="url(#g)"/>
  <circle cx="80" cy="80" r="130" fill="rgba(255,255,255,.05)"/>
  <circle cx="520" cy="280" r="90" fill="rgba(255,255,255,.06)"/>
  <circle cx="100" cy="300" r="60" fill="rgba(255,255,255,.04)"/>
  <rect x="0" y="210" width="600" height="140" fill="url(#g)" opacity=".7"/>
  <text x="300" y="265" text-anchor="middle" font-size="24" font-weight="bold" fill="#fff" font-family="sans-serif">{display_name}</text>
  <text x="300" y="295" text-anchor="middle" font-size="12" fill="rgba(255,255,255,.5)" font-family="sans-serif">{t}</text>
</svg>'''
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return {"url": f"data:image/svg+xml;base64,{b64}", "source": "svg"}
