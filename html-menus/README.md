# MAZA HTML Menus — data-driven, real photos, no image generation

On-brand HTML menus rendered from `menu.json` (the single source of truth for
menu text/prices) with real photos from the OneDrive library. Edit data →
re-run build → re-screenshot. That's the whole loop.

## Architecture

```
menu.json  (one level up)   ->  names, prices, notes, subtitles  [TEXT TRUTH]
photo-map.json              ->  "Section > Item" -> photo file   [PHOTO MAPPING]
tv-screens.json             ->  TV screen groupings/cards/layout [TV LAYOUT]
theme.css                   ->  brand tokens for print/web docs  (teal surface)
tv-theme.css                ->  shared TV board styles           (black surface)
templates/*.html            ->  Jinja2 templates
build.py                    ->  renderer (python3 build.py)
out/                        ->  rendered HTML + PNG screenshots
photos/                     ->  synced + downscaled photo cache (auto-managed)
```

Data flow: `menu.json + photo-map.json + tv-screens.json --> build.py --> out/*.html`
Screenshots: headless chromium at 1920x1080 (see commands below).

## Common edits

| You want to...                          | Edit this                              |
|-----------------------------------------|----------------------------------------|
| Change a price / name / description     | `../menu.json` (NEVER the templates)   |
| Swap a photo                            | `photo-map.json` (key = `Section > Item`, exact menu.json names) |
| Move items between TV groups/screens    | `tv-screens.json` (item refs are `["Section", "Item"]` pairs) |
| Change colors / fonts / spacing         | `theme.css` (docs) or `tv-theme.css` (TV) |
| Change layout structure                 | `templates/*.html`                     |

After any edit:

```bash
cd /srv/apps/tricon-projects/maza-mediterranean/html-menus
python3 build.py                      # re-render everything
python3 build.py --tv-only            # just the 3 TV screens
python3 build.py --sync-photos        # force photo re-sync (needed after photo-map swaps)
```

Screenshots (1920x1080 PNGs):

```bash
for s in screen1-wraps screen2-plates screen3-loaded; do
  chromium-browser --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size=1920,1080 --screenshot=/tmp/$s.png file://$PWD/out/$s.html
done
```

ALWAYS inspect screenshots with vision before delivering. Check: photos upright,
no clipping/overflow, prices match menu.json, dead space filled.

## TV screens (1920x1080)

- **screen1-wraps** — WRAPS in 4 groups (Shredded / Shish Kebab / Tikka / Maza
  Specialty), right side 2x2 photo cards, bottom MAKE IT A COMBO banner.
- **screen2-plates** — PLATES two columns grouped by protein (Chicken/Lamb/Plant
  Based | Beef/Mixed), right side 5-photo gallery + SPECIALS box (hero photo +
  3 items).
- **screen3-loaded** — 3 bands: Loaded Fries/Loaded Hummus + photos; Burgers /
  Kids Meals / Sides (3 sub-columns) + photos; Desserts / Drinks (2 cols) /
  Sharbat. Halal badge top center.

Groupings follow the approved conventions (skill: maza-menu-management,
references/tv-board-groupings.md). Shawarma wraps go under Shredded Wraps;
Ribeye Tikka + Shredded Steak plates under Beef; Appetizer Plate under Mixed.

## Pitfalls (learned the hard way — read before editing)

1. **EXIF rotation.** Phone photos often store rotation in EXIF. `build.py`
   runs `ImageOps.exif_transpose` on sync — never bypass it or photos render
   sideways. After changing photo-map entries, run `--sync-photos` (cache is
   mtime-based and won't pick up a remap of an already-synced name... actually
   it keys dest by item name, so a REMAP needs `rm photos/<slug>.jpg` or
   `--sync-photos`).
2. **Baked-in rotations.** `menu/burger-fries-combo.webp` has sideways pixels
   with NO EXIF flag. Use `menu/og/burger-fries-combo.jpg` instead. If a photo
   renders sideways after exif_transpose, the pixels themselves are rotated —
   pick a different source file.
3. **Portrait photos in landscape slots look bad** (user requirement). The
   photo library is mostly portrait for wraps — Screen 1 uses a 2x2 grid with
   near-square slots for that reason. Prefer landscape sources for wide slots;
   check the library scan before mapping.
4. **Fill vertical space** (user requirement). TV text blocks use flexbox with
   `justify-content: space-evenly` so content stretches to fill the band. If
   you add/remove items, re-check the screenshot for dead zones.
5. **Jinja gotcha:** `section.items` collides with `dict.items()` — always
   write `section["items"]` in templates.
6. **TV prices render WITHOUT `$`** (mock style). build.py strips it.
7. **OneDrive reads are slow.** Photos are downscaled to max 1200px JPEG q84
   into `photos/` on sync — work from the cache, don't re-read the library.
8. **Fonts** come from Google Fonts (Cinzel + Montserrat per brand.json).
   Headless chromium needs network for them; offline it falls back to
   serif/sans and looks wrong.
9. Brand tokens: deep teal `#0A1F1E` (docs), black `#000` (TV), gold `#D3AB5E`,
   gold-light `#E9C87B`, off-white `#F5F1E8`. Cinzel display / Montserrat body.

## Render outputs

- `out/full-menu.html` — long-form branded menu doc (also PDF via
  `chromium-browser --headless --print-to-pdf`)
- `out/screen1-wraps.html` / `screen2-plates.html` / `screen3-loaded.html` — TV
- `out/*.png` — latest approved screenshots
