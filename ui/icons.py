"""
Procedural vector icon renderer for NextBoot.
Draws crisp, high-DPI resolution-independent OS badges and logos on Tkinter Canvas.
"""

import tkinter as tk
import math
from typing import Tuple

class IconRenderer:
    """Renders vector icons for operating systems and UI actions on a Tkinter Canvas."""

    @staticmethod
    def draw_rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius=12, **kwargs):
        """Draws a smooth rounded rectangle on canvas."""
        points = [
            x1 + radius, y1,
            x1 + radius, y1,
            x2 - radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1 + radius,
            x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    @classmethod
    def draw_os_icon(cls, canvas: tk.Canvas, cx: float, cy: float, size: float, os_family: str):
        """Draws the brand vector icon for the specified OS family."""
        half = size / 2
        bg_radius = size * 0.22

        # 1. Background rounded container
        bg_color = cls.get_brand_color(os_family)
        cls.draw_rounded_rect(
            canvas,
            cx - half, cy - half,
            cx + half, cy + half,
            radius=int(bg_radius),
            fill=bg_color,
            outline=""
        )

        inner_r = half * 0.65

        # 2. Draw brand glyph
        if os_family == "windows":
            # 4 Windows tiles
            gap = size * 0.04
            tile_w = (inner_r * 2 - gap) / 2
            tile_h = tile_w
            x0 = cx - inner_r
            y0 = cy - inner_r
            color = "#ffffff"
            # Top-left, top-right, bottom-left, bottom-right
            canvas.create_rectangle(x0, y0, x0 + tile_w, y0 + tile_h, fill=color, outline="")
            canvas.create_rectangle(x0 + tile_w + gap, y0, x0 + 2*tile_w + gap, y0 + tile_h, fill=color, outline="")
            canvas.create_rectangle(x0, y0 + tile_h + gap, x0 + tile_w, y0 + 2*tile_h + gap, fill=color, outline="")
            canvas.create_rectangle(x0 + tile_w + gap, y0 + tile_h + gap, x0 + 2*tile_w + gap, y0 + 2*tile_h + gap, fill=color, outline="")

        elif os_family == "ubuntu":
            # Ubuntu Circle of Friends
            color = "#ffffff"
            # Outer ring
            ring_w = max(2, int(size * 0.07))
            canvas.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r, outline=color, width=ring_w)
            # Center circle
            canvas.create_oval(cx - inner_r*0.25, cy - inner_r*0.25, cx + inner_r*0.25, cy + inner_r*0.25, fill=color, outline="")
            # 3 outer nodes
            for angle in [0, 120, 240]:
                rad = math.radians(angle)
                node_dist = inner_r * 0.95
                nx = cx + node_dist * math.cos(rad)
                ny = cy + node_dist * math.sin(rad)
                nr = size * 0.08
                canvas.create_oval(nx - nr, ny - nr, nx + nr, ny + nr, fill=bg_color, outline=bg_color)
                canvas.create_oval(nx - nr*0.8, ny - nr*0.8, nx + nr*0.8, ny + nr*0.8, fill=color, outline="")

        elif os_family == "arch":
            # Arch triangular peak with inner swoosh
            color = "#ffffff"
            p1 = (cx, cy - inner_r * 1.1)
            p2 = (cx - inner_r * 1.0, cy + inner_r * 0.9)
            p3 = (cx + inner_r * 1.0, cy + inner_r * 0.9)
            p_arch = (cx, cy + inner_r * 0.3)
            canvas.create_polygon([p1[0], p1[1], p2[0], p2[1], p_arch[0], p_arch[1], p3[0], p3[1]], fill=color, outline="")

        elif os_family == "fedora":
            # Fedora infinity symbol stylized
            color = "#ffffff"
            w = max(3, int(size * 0.08))
            canvas.create_oval(cx - inner_r, cy - inner_r*0.6, cx, cy + inner_r*0.6, outline=color, width=w)
            canvas.create_oval(cx, cy - inner_r*0.6, cx + inner_r, cy + inner_r*0.6, outline=color, width=w)
            canvas.create_line(cx - inner_r*0.2, cy - inner_r*0.9, cx - inner_r*0.2, cy + inner_r*0.9, fill=color, width=w)

        elif os_family == "debian":
            # Debian swirl approximation
            color = "#ffffff"
            w = max(2, int(size * 0.08))
            canvas.create_arc(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r, start=45, extent=280, outline=color, width=w, style="arc")
            canvas.create_arc(cx - inner_r*0.6, cy - inner_r*0.6, cx + inner_r*0.6, cy + inner_r*0.6, start=180, extent=220, outline=color, width=w, style="arc")

        elif os_family == "mint":
            # Linux Mint stylized leaf / LM
            color = "#ffffff"
            w = max(3, int(size * 0.08))
            canvas.create_oval(cx - inner_r*0.9, cy - inner_r*0.9, cx + inner_r*0.9, cy + inner_r*0.9, outline=color, width=w)
            canvas.create_text(cx, cy, text="LM", fill=color, font=("Arial", int(size * 0.28), "bold"))

        elif os_family == "pop_os":
            # Pop! text
            color = "#ffffff"
            canvas.create_text(cx, cy, text="POP!", fill=color, font=("Arial", int(size * 0.24), "bold"))

        elif os_family == "macos":
            # Apple glyph outline
            color = "#ffffff"
            canvas.create_oval(cx - inner_r*0.75, cy - inner_r*0.5, cx + inner_r*0.75, cy + inner_r*0.8, fill=color, outline="")
            # Stem
            canvas.create_arc(cx - inner_r*0.2, cy - inner_r*1.0, cx + inner_r*0.4, cy - inner_r*0.4, start=45, extent=90, outline=color, width=3, style="arc")

        elif os_family == "hardware":
            # Motherboard chip / Network
            color = "#ffffff"
            w = max(2, int(size * 0.06))
            # Chip body
            r = inner_r * 0.65
            canvas.create_rectangle(cx - r, cy - r, cx + r, cy + r, outline=color, width=w, fill=bg_color)
            # Inner core
            canvas.create_rectangle(cx - r*0.5, cy - r*0.5, cx + r*0.5, cy + r*0.5, fill=color, outline="")
            # Pins
            pin_len = size * 0.12
            for offset in [-r*0.5, 0, r*0.5]:
                canvas.create_line(cx + offset, cy - r, cx + offset, cy - r - pin_len, fill=color, width=w)
                canvas.create_line(cx + offset, cy + r, cx + offset, cy + r + pin_len, fill=color, width=w)
                canvas.create_line(cx - r, cy + offset, cx - r - pin_len, cy + offset, fill=color, width=w)
                canvas.create_line(cx + r, cy + offset, cx + r + pin_len, cy + offset, fill=color, width=w)

        else:
            # Generic Linux / Tux / Gear
            color = "#ffffff"
            canvas.create_text(cx, cy, text="LINUX", fill=color, font=("Arial", int(size * 0.20), "bold"))

    @staticmethod
    def get_brand_color(os_family: str) -> str:
        """Returns the primary branding hex color for each OS family."""
        colors = {
            "windows": "#0078D4",   # Microsoft Blue
            "ubuntu": "#E95420",    # Canonical Ubuntu Orange
            "fedora": "#294172",    # Fedora Blue
            "arch": "#1793D1",      # Arch Cyan
            "debian": "#D70A53",    # Debian Red
            "mint": "#6CA32E",      # Linux Mint Green
            "pop_os": "#48B9C7",    # Pop Teal
            "manjaro": "#35BF5C",   # Manjaro Emerald
            "opensuse": "#73BA25",  # Gecko Green
            "kali": "#557CBF",      # Kali Blue
            "zorin": "#0CC1E8",     # Zorin Cyan
            "steamos": "#1A9FFF",   # Valve Steam Blue
            "redhat": "#EE0000",    # Red Hat Red
            "macos": "#7D8590",     # Apple Slate
            "freebsd": "#AB2B28",   # FreeBSD Crimson
            "android": "#3DDC84",   # Android Green
            "grub": "#F59E0B",      # GRUB Amber
            "hardware": "#8B5CF6",  # Hardware / Firmware Purple
            "bootmgr": "#6366F1",   # Indigo
        }
        return colors.get(os_family.lower(), "#64748B")
