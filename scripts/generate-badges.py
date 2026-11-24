#!/usr/bin/env python3
"""Generate rounded skill/social badges with embedded Simple Icons."""

from __future__ import annotations

import argparse
import base64
import html
import pathlib
import re
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "badges"
CUSTOM_DIR = ROOT / "assets" / "custom-icons"
SI = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{}.svg"

# Local white logos (override Simple Icons) keyed by badge file slug.
CUSTOM_ICONS = {
    "giro3d": CUSTOM_DIR / "giro3d.svg",
    "postgis": CUSTOM_DIR / "postgis.svg",
    "rustgis": CUSTOM_DIR / "rustgis.svg",
    "geoserver": CUSTOM_DIR / "geoserver.svg",
    "pygeoapi": CUSTOM_DIR / "pygeoapi.svg",
    "grok-bot": CUSTOM_DIR / "grok-bot.svg",
    "openclaw": CUSTOM_DIR / "openclaw.svg",
    "agent-skills": CUSTOM_DIR / "agent-skills.svg",
    "agents-plugins": CUSTOM_DIR / "agents-plugins.svg",
}

BADGES = [
    # Social
    ("linkedin", "LinkedIn", "0077B5", "linkedin", "#fff"),
    ("twitter", "Twitter", "1DA1F2", "x", "#fff"),
    ("tiktok", "TikTok", "000000", "tiktok", "#fff"),
    ("youtube", "YouTube", "FF0000", "youtube", "#fff"),
    ("facebook", "Facebook", "003E54", "facebook", "#fff"),
    ("instagram", "Instagram", "E4405F", "instagram", "#fff"),
    ("slack", "Slack", "4A154B", "slack", "#fff"),
    ("telegram", "Telegram", "2CA5E0", "telegram", "#fff"),
    ("spotify", "Spotify", "1ED760", "spotify", "#fff"),
    # Languages
    ("python", "Python", "3670A0", "python", "#ffdd54"),
    ("typescript", "TypeScript", "3178C6", "typescript", "#fff"),
    ("javascript", "JavaScript", "F0DB4F", "javascript", "#fff"),
    ("sql", "SQL", "4479A1", "sqlite", "#fff"),
    ("r", "R", "276DC3", "r", "#fff"),
    ("rust", "Rust", "000000", "rust", "#fff"),
    ("cpp", "C++", "00599C", "cplusplus", "#fff"),
    # Frontend
    ("angular", "Angular", "DD0031", "angular", "#fff"),
    ("nextjs", "Next.js", "000000", "nextdotjs", "#fff"),
    ("tailwindcss", "Tailwind CSS", "06B6D4", "tailwindcss", "#fff"),
    ("react-native", "React Native", "61DAFB", "react", "#fff"),
    ("leaflet", "Leaflet", "199900", "leaflet", "#fff"),
    ("openlayers", "OpenLayers", "1F6B75", "openlayers", "#fff"),
    ("maplibre-gl", "MapLibre GL", "323E48", "maplibre", "#fff"),
    ("deckgl", "deck.gl", "00ADE6", "deckdotgl", "#fff"),
    ("giro3d", "Giro3D", "0D9488", "threedotjs", "#fff"),
    # Backend
    ("fastapi", "FastAPI", "009688", "fastapi", "#fff"),
    ("django", "Django", "092E20", "django", "#fff"),
    ("django-q", "Django-Q", "092E20", "django", "#fff"),
    ("nodejs", "Node.js", "339933", "nodedotjs", "#fff"),
    ("express", "Express", "404040", "express", "#fff"),
    ("postgresql", "PostgreSQL", "4169E1", "postgresql", "#fff"),
    ("postgis", "PostGIS", "336791", "postgresql", "#fff"),
    ("oracle", "Oracle", "F80000", "oracle", "#fff"),
    ("redis", "Redis", "DC382D", "redis", "#fff"),
    ("duckdb", "DuckDB", "FFF000", "duckdb", "#fff"),
    # Geospatial
    ("qgis", "QGIS", "589632", "qgis", "#fff"),
    ("arcgis", "ArcGIS", "0079C1", "esri", "#fff"),
    ("rustgis", "RustGIS", "DEA584", "rust", "#fff"),
    ("google-earth-engine", "Google Earth Engine", "4285F4", "googleearth", "#fff"),
    ("martin", "Martin", "1B4D3E", "maplibre", "#fff"),
    ("titiler", "TiTiler", "FF6B35", "python", "#fff"),
    ("pygeoapi", "PyGeoAPI", "3776AB", "python", "#fff"),
    ("geoserver", "GeoServer", "1B75BB", "openlayers", "#fff"),
    # AI
    ("codex", "Codex", "10A37F", "openai", "#fff"),
    ("claude-code", "Claude Code", "D97757", "anthropic", "#fff"),
    ("cursor-ai", "Cursor AI", "000000", "cursor", "#fff"),
    ("grok-bot", "Grok Bot", "000000", "x", "#fff"),
    ("openclaw", "OpenClaw", "1DA1F2", "openai", "#fff"),
    ("prompt-engineering", "Prompt Engineering", "7C3AED", "openai", "#fff"),
    ("agent-skills", "Agent Skills", "F59E0B", "fastapi", "#fff"),
    ("mcp", "MCP", "0EA5E9", "modelcontextprotocol", "#fff"),
    ("agents-plugins", "Agents Plugins", "8B5CF6", "github", "#fff"),
    ("geoagent", "GeoAgent", "14B8A6", "googleearth", "#fff"),
    ("ollama", "Ollama", "000000", "ollama", "#fff"),
    ("local-llms", "Local LLMs", "111827", "huggingface", "#fff"),
    # DevOps
    ("linux-server", "Linux Server", "FCC624", "linux", "#fff"),
    ("docker", "Docker", "2496ED", "docker", "#fff"),
    ("compose", "Docker Compose", "2496ED", "docker", "#fff"),
    ("kubernetes", "Kubernetes", "326CE5", "kubernetes", "#fff"),
    ("nginx", "Nginx", "009639", "nginx", "#fff"),
    ("traefik", "Traefik", "24A1C1", "traefikproxy", "#fff"),
    ("git", "Git", "F05032", "git", "#fff"),
    ("github", "GitHub", "181717", "github", "#fff"),
    ("github-actions", "GitHub Actions", "2088FF", "githubactions", "#fff"),
    ("ci", "CI", "2088FF", "githubactions", "#fff"),
    ("google-cloud", "Google Cloud", "4285F4", "googlecloud", "#fff"),
    ("aws", "AWS", "232F3E", "amazonwebservices", "#FF9900"),
]

FALLBACKS = {
    "deckdotgl": ["threedotjs"],
    "modelcontextprotocol": ["json", "openai"],
    "amazonwebservices": ["amazonaws", "amazon"],
}

DARK_TEXT = {"javascript", "duckdb", "linux-server", "react-native"}

_cache: dict[str, str | None] = {}


def fetch_icon(slug: str) -> str | None:
    if slug in _cache:
        return _cache[slug]
    for candidate in [slug, *FALLBACKS.get(slug, [])]:
        try:
            req = urllib.request.Request(
                SI.format(candidate),
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                data = response.read().decode("utf-8")
            if "<svg" in data:
                _cache[slug] = data
                if candidate != slug:
                    print(f"  fallback {slug} -> {candidate}")
                return data
        except Exception:
            continue
    _cache[slug] = None
    return None


def tint_icon(svg: str, color: str) -> str:
    def repl(match: re.Match[str]) -> str:
        attrs = re.sub(r'\sfill="[^"]*"', "", match.group(1))
        return f'<svg{attrs} fill="{color}">'

    svg = re.sub(r"<svg\b([^>]*)>", repl, svg, count=1)
    svg = svg.replace('fill="currentColor"', f'fill="{color}"')
    svg = re.sub(r'\s(width|height)="[^"]*"', "", svg)
    return svg


# Horizontal inset inside the colored label area (matches shields-style padding).
LABEL_PAD_X = 10


def text_width(label: str) -> int:
    # Verdana bold ~11px: slightly generous so glyphs never kiss the edges.
    return max(int(len(label) * 7.6) + 4, 28)


def load_icon(file_slug: str, icon_slug: str, icon_color: str) -> str:
    custom_path = CUSTOM_ICONS.get(file_slug)
    if custom_path is not None and custom_path.exists():
        # Already authored as white glyphs; do not recolor (preserves cutouts).
        return custom_path.read_text()

    icon = fetch_icon(icon_slug)
    if icon is None:
        raise RuntimeError(f"No icon for {icon_slug}")
    return tint_icon(icon, icon_color)


def make_badge(
    file_slug: str,
    label: str,
    color: str,
    icon_slug: str,
    icon_color: str,
) -> str:
    icon = load_icon(file_slug, icon_slug, icon_color)
    if file_slug in CUSTOM_ICONS:
        # Inline local vectors so badges render reliably without nested data images.
        match = re.search(r"<svg\b[^>]*>(.*)</svg>", icon, re.DOTALL)
        if match is None:
            raise ValueError(f"Invalid custom SVG: {file_slug}")
        icon_markup = f'<g transform="translate(6 6) scale(0.666667)">{match.group(1).strip()}</g>'
    else:
        icon_b64 = base64.b64encode(icon.encode()).decode()
        icon_markup = f'<image x="6" y="6" width="16" height="16" href="data:image/svg+xml;base64,{icon_b64}"/>'
    label_w = text_width(label)
    left, height, radius = 28, 28, 14
    total = left + LABEL_PAD_X + label_w + LABEL_PAD_X
    text_x = left + LABEL_PAD_X + label_w / 2
    text_color = "#111111" if file_slug in DARK_TEXT else "#ffffff"
    safe = html.escape(label)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{height}" role="img" aria-label="{safe}">
  <title>{safe}</title>
  <rect width="{total}" height="{height}" rx="{radius}" fill="#{color}"/>
  <path d="M{radius},0 H{left} V{height} H{radius} A{radius},{radius} 0 0 1 {radius},0 Z" fill="#111111"/>
  <circle cx="14" cy="14" r="14" fill="#111111"/>
  {icon_markup}
  <text x="{text_x:.1f}" y="18" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11" font-weight="700" fill="{text_color}">{safe}</text>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--custom-only", action="store_true", help="Regenerate only badges with local icons")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.custom_only:
        badges = [badge for badge in BADGES if badge[0] in CUSTOM_ICONS]
    else:
        badges = BADGES

    failed: list[tuple[str, str]] = []
    for item in badges:
        try:
            (OUT / f"{item[0]}.svg").write_text(make_badge(*item))
            print("OK", item[0])
            time.sleep(0.02)
        except Exception as exc:  # noqa: BLE001
            failed.append((item[0], str(exc)))
            print("FAIL", item[0], exc)

    print(f"total={len(list(OUT.glob('*.svg')))} failed={failed}")


if __name__ == "__main__":
    main()
