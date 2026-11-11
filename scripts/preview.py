#!/usr/bin/env python3
"""Write upscaled PNG previews of the static frames (for local checking only)."""
import sys
from pathlib import Path
from neon import header
out = Path(sys.argv[1] if len(sys.argv) > 1 else "preview")
out.mkdir(parents=True, exist_ok=True)
header.title_svg(); header.skyline_svg()
for name, c in header.PREVIEW.items():
    (out / f"{name}.png").write_bytes(c.scaled_png(3))
    print("wrote", out / f"{name}.png")
