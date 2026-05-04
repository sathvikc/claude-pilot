#!/usr/bin/env bash
# Generate web-optimized variants for console screenshots.
#
# Usage:
#   1. Drop PNG (or WebP) screenshots into public/console/<name>.png
#      (e.g. public/console/dashboard.png — any resolution; native is fine)
#   2. Run: npm run optimize:screenshots
#      (or VS Code task: "Optimize Screenshots")
#
# What the script does:
#   - PNG inputs → converted to public/console/<name>.webp (lossless q=95),
#     then the source PNG is deleted
#   - Generates public/console/<name>_sm.webp     (1400px wide, q=80) — inline
#   - Generates public/console/thumbs/<name>.webp ( 120px wide, q=80) — thumb
#
# The full-size WebP at public/console/<name>.webp stays as the modal source.
# Re-running the script regenerates only stale or missing variants.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONSOLE_DIR="$SITE_ROOT/public/console"
THUMBS_DIR="$CONSOLE_DIR/thumbs"

if ! command -v cwebp >/dev/null 2>&1; then
  echo "error: cwebp not found. Install with: brew install webp" >&2
  exit 1
fi

mkdir -p "$THUMBS_DIR"

INLINE_WIDTH=1400
INLINE_QUALITY=80
THUMB_WIDTH=120
THUMB_QUALITY=80
SRC_QUALITY=95

is_stale() {
  local src="$1" dst="$2"
  [ ! -f "$dst" ] || [ "$src" -nt "$dst" ]
}

count_png=0
count_inline=0
count_thumb=0
count_skipped=0

shopt -s nullglob

# Step 1 — convert any PNG sources into full-size WebP, then remove the PNG.
for png in "$CONSOLE_DIR"/*.png; do
  base="$(basename "$png" .png)"
  webp="$CONSOLE_DIR/${base}.webp"

  cwebp -q "$SRC_QUALITY" "$png" -o "$webp" >/dev/null 2>&1
  rm -f "$png"
  count_png=$((count_png + 1))
  echo "  source → ${base}.webp (from PNG)"
done

# Step 2 — derive _sm and thumb variants from each source WebP.
for src in "$CONSOLE_DIR"/*.webp; do
  base="$(basename "$src" .webp)"
  case "$base" in
    *_sm) continue ;;
  esac

  inline="$CONSOLE_DIR/${base}_sm.webp"
  thumb="$THUMBS_DIR/${base}.webp"

  if is_stale "$src" "$inline"; then
    cwebp -q "$INLINE_QUALITY" -resize "$INLINE_WIDTH" 0 "$src" -o "$inline" >/dev/null 2>&1
    count_inline=$((count_inline + 1))
    echo "  inline → ${base}_sm.webp"
  else
    count_skipped=$((count_skipped + 1))
  fi

  if is_stale "$src" "$thumb"; then
    cwebp -q "$THUMB_QUALITY" -resize "$THUMB_WIDTH" 0 "$src" -o "$thumb" >/dev/null 2>&1
    count_thumb=$((count_thumb + 1))
    echo "  thumb  → thumbs/${base}.webp"
  fi
done

echo ""
echo "PNG converted: $count_png   inline regenerated: $count_inline   thumbs regenerated: $count_thumb   up-to-date: $count_skipped"
echo ""
echo "To add a new screenshot:"
echo "  1. Save the PNG to public/console/<name>.png"
echo "  2. Add { label, name, alt, desc } to consoleSlides in src/components/ConsoleSection.tsx"
echo "  3. Re-run this script"
