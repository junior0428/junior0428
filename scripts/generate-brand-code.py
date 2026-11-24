#!/usr/bin/env python3
"""Generate brand typing SVG: {text|} with always-visible braces (site nav parity)."""

from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "brand-code.svg"

PHRASES = ["GIS Development", "Remote Sensing", "Map Servers", "Programming"]
PAUSE_FRAMES = 10
MS_PER_FRAME = 90
COLOR = "#f59e0b"
FONT = "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
SIZE = 16
LINE_H = 28
PAD_X = 2


def build_frames() -> list[str]:
    frames: list[str] = []
    for phrase in PHRASES:
        # Type
        for i in range(0, len(phrase) + 1):
            frames.append("{" + phrase[:i] + "|}")
        # Hold full phrase. Keep "|" always so "}" does not jump (space blink caused flicker).
        frames.extend("{" + phrase + "|}" for _ in range(PAUSE_FRAMES))
        # Delete (skip the full-phrase frame to avoid a one-frame stutter)
        for i in range(len(phrase) - 1, -1, -1):
            frames.append("{" + phrase[:i] + "|}")
    return frames


def main() -> None:
    frames = build_frames()
    width = int(max(len(frame) for frame in frames) * 9.6) + 8
    duration_s = len(frames) * MS_PER_FRAME / 1000
    values = ";".join(f"0,{-i * LINE_H}" for i in range(len(frames)))

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{LINE_H}" '
        f'viewBox="0 0 {width} {LINE_H}" role="img" '
        f'aria-label="GIS Development, Remote Sensing, Map Servers, Programming">',
        "  <title>{GIS Development} · {Remote Sensing} · {Map Servers} · {Programming}</title>",
        "  <defs>",
        f'    <clipPath id="v"><rect width="{width}" height="{LINE_H}"/></clipPath>',
        "  </defs>",
        '  <g clip-path="url(#v)">',
        "    <g>",
        '      <animateTransform attributeName="transform" type="translate" calcMode="discrete"',
        f'        values="{values}"',
        f'        dur="{duration_s:.2f}s" repeatCount="indefinite"/>',
    ]
    for i, frame in enumerate(frames):
        y = 20 + i * LINE_H
        lines.append(
            f'      <text x="{PAD_X}" y="{y}" font-family="{FONT}" font-size="{SIZE}" '
            f'font-weight="700" letter-spacing="-0.025em" fill="{COLOR}">{escape(frame)}</text>'
        )
    lines += ["    </g>", "  </g>", "</svg>", ""]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} frames={len(frames)} width={width} dur={duration_s:.2f}s")


if __name__ == "__main__":
    main()
