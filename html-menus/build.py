#!/usr/bin/env python3
"""
MAZA HTML menu builder.

Reads menu.json (single source of truth), maps items to REAL photos via
photo-map.json (no image generation — user content only), and renders
branded HTML through Jinja2 templates.

Usage:
  python3 build.py                      # render all templates -> out/
  python3 build.py --template full-menu # render one template
  python3 build.py --sync-photos        # force re-copy photos from library

Data flow:  menu.json + photo-map.json  -->  build.py  -->  out/<name>.html
Styling:    theme.css (brand tokens — edit once, applies everywhere)
Photos:     copied from the OneDrive photo library into photos/
"""
import argparse
import json
import shutil
import sys
import unicodedata
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import ImageOps

HERE = Path(__file__).resolve().parent
MENU_JSON = HERE.parent / "menu.json"
PHOTO_MAP = HERE / "photo-map.json"
TEMPLATE_DIR = HERE / "templates"
OUT_DIR = HERE / "out"
PHOTOS_DIR = HERE / "photos"

BRAND = {
    "name": "Maza Mediterranean Cuisine",
    "display": "Maza",
    "tagline": "Mediterranean Cuisine",
    "address": "3491 W Frye Rd, Suite 2, Chandler AZ 85226",
    "phone": "(480) 534-6550",
    "hours": "10am–10pm Tue–Sun · Closed Mondays",
}

# Sections rendered in the compact (2-col, text-focused) layout
COMPACT_SECTIONS = {"Sides", "Drinks", "Sharbat", "Wrap Upgrades", "Kids Meals", "Baklava"}


def slug(text: str) -> str:
    """Filesystem-safe photo filename from an item key."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    keep = [c.lower() if c.isalnum() else "-" for c in text]
    return "-".join(filter(None, "".join(keep).split("-")))


def load_photo_map() -> tuple[Path, dict]:
    cfg = json.loads(PHOTO_MAP.read_text())
    return Path(cfg["photo_lib"]), cfg["map"]


def sync_photos(photo_lib: Path, mapping: dict) -> dict:
    """Copy mapped photos into photos/, downscaled for fast HTML/print.
    Returns {map_key: local_filename}. OneDrive source reads are slow, so
    we cache by mtime and store web-weight JPEGs (max 1200px)."""
    from PIL import Image
    local = {}
    missing = []
    for key, rel in mapping.items():
        src = photo_lib / rel
        if not src.is_file():
            missing.append(f"{key} -> {rel}")
            continue
        dest_name = f"{slug(key)}.jpg"
        dest = PHOTOS_DIR / dest_name
        if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)  # honor camera rotation
                im = im.convert("RGB")
                im.thumbnail((1200, 1200), Image.LANCZOS)
                im.save(dest, "JPEG", quality=84, optimize=True)
        local[key] = dest_name
    if missing:
        print("WARN missing photo files:")
        for m in missing:
            print(f"  {m}")
    return local


def build_sections(local_photos: dict) -> list[dict]:
    menu = json.loads(MENU_JSON.read_text())
    sections = []
    for sec in menu["sections"]:
        items = []
        for it in sec["items"]:
            key = f"{sec['name']} > {it['name']}"
            notes = list(it.get("notes", []))
            if it.get("note"):
                notes.append(it["note"])
            items.append({
                "name": it["name"],
                "price": it["price"],
                "all_notes": notes,
                "photo": local_photos.get(key),
            })
        sections.append({
            "name": sec["name"],
            "subtitle": sec.get("subtitle"),
            "items": items,
            "compact": sec["name"] in COMPACT_SECTIONS,
        })
    return sections


# ---------------------------------------------------------------------------
# TV screens (1920x1080) — groupings/cards from tv-screens.json, text from
# menu.json, photos from photo-map.json. Change data in menu.json, re-run,
# re-screenshot. No image generation involved.
# ---------------------------------------------------------------------------

TV_CONFIG = HERE / "tv-screens.json"


def _menu_index(local_photos: dict) -> tuple[dict, dict]:
    """Returns (item_index, section_index).
    item_index: {(section, item): resolved item dict}
    section_index: {section_name: {"name", "subtitle", "items": [refs]}}"""
    menu = json.loads(MENU_JSON.read_text())
    item_index, section_index = {}, {}
    for sec in menu["sections"]:
        refs = []
        for it in sec["items"]:
            notes = list(it.get("notes", []))
            if it.get("note"):
                notes.append(it["note"])
            key = f"{sec['name']} > {it['name']}"
            item_index[(sec["name"], it["name"])] = {
                "name": it["name"],
                "price": it["price"].replace("$", ""),  # TV style: no $ sign
                "all_notes": notes,
                "first_note": notes[0] if notes else "",
                "photo": local_photos.get(key),
            }
            refs.append((sec["name"], it["name"]))
        section_index[sec["name"]] = {
            "name": sec["name"],
            "subtitle": sec.get("subtitle"),
            "_refs": refs,
        }
    return item_index, section_index


def _resolve_node(node, item_index, section_index):
    """Recursively resolve tv-screens.json nodes:
    - {"section": "Name"}            -> section dict with resolved items
    - ["Section", "Item"] (2-str)    -> resolved item dict
    - anything else                  -> resolved recursively / as-is"""
    if isinstance(node, dict):
        if set(node.keys()) == {"section"} and isinstance(node["section"], str):
            sec = section_index[node["section"]]
            return {
                "name": sec["name"],
                "subtitle": sec["subtitle"],
                "items": [item_index[r] for r in sec["_refs"]],
            }
        return {k: _resolve_node(v, item_index, section_index) for k, v in node.items()}
    if isinstance(node, (list, tuple)):
        if (
            len(node) == 2
            and all(isinstance(x, str) for x in node)
            and (node[0], node[1]) in item_index
        ):
            return item_index[(node[0], node[1])]
        return [_resolve_node(v, item_index, section_index) for v in node]
    return node


def build_tv(env: Environment, local_photos: dict) -> None:
    cfg = json.loads(TV_CONFIG.read_text())
    item_index, section_index = _menu_index(local_photos)
    for screen in cfg["screens"]:
        resolved = _resolve_node(
            {k: v for k, v in screen.items() if k not in ("id", "template")},
            item_index, section_index,
        )
        tpl = env.get_template(screen["template"])
        html = tpl.render(brand=BRAND, s=resolved)
        out_file = OUT_DIR / f"{screen['id']}.html"
        out_file.write_text(html)
        print(f"wrote {out_file}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", help="render only this template (name without .html)")
    ap.add_argument("--sync-photos", action="store_true", help="force re-copy photos")
    ap.add_argument("--tv-only", action="store_true", help="render only the TV screens")
    ap.add_argument("--no-tv", action="store_true", help="skip the TV screens")
    args = ap.parse_args()

    if args.sync_photos and PHOTOS_DIR.exists():
        shutil.rmtree(PHOTOS_DIR)
    PHOTOS_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    photo_lib, mapping = load_photo_map()
    local_photos = sync_photos(photo_lib, mapping)
    sections = build_sections(local_photos)

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )

    templates = [TEMPLATE_DIR / f"{args.template}.html"] if args.template else sorted(TEMPLATE_DIR.glob("*.html"))
    if not args.tv_only:
        for tpl_path in templates:
            if tpl_path.name.startswith("tv-") and not args.template:
                continue  # TV templates need screen context — handled by build_tv
            tpl = env.get_template(tpl_path.name)
            html = tpl.render(brand=BRAND, sections=sections)
            out_file = OUT_DIR / tpl_path.name
            out_file.write_text(html)
            print(f"wrote {out_file}")

    if not args.no_tv and not args.template:
        build_tv(env, local_photos)

    n_photos = sum(1 for s in sections for i in s["items"] if i["photo"])
    n_items = sum(len(s["items"]) for s in sections)
    print(f"{n_items} items, {n_photos} with photos, {len(sections)} sections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
