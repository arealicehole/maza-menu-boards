# Maza Menu Boards

Version-controlled menu board assets for Maza Mediterranean Cuisine.

## Structure

```
base/
  screen1/     Approved source images for i2i generation (TV screen 1)
  screen2/     Approved source images for i2i generation (TV screen 2)
generated/
  screen1/     Maza bot i2i outputs for screen 1
  screen2/     Maza bot i2i outputs for screen 2
```

## Naming Convention

`screen{N}-v{VERSION}.png` — e.g. `screen1-v7.png`, `screen2-v10.png`

**Never overwrite.** Each version is a new file. Commit log = full history.

## Workflow

### Adding a new base image
1. Upload the approved image to `base/screen{N}/` via GitHub UI or `gh`
2. File name should include version number
3. Commit message: `base: add screen{N}-v{VERSION}.png`

### Generating a new menu board (Maza bot)
1. `git pull` to get latest base images
2. Load `base/screen{N}/` — use the highest version (sort by name descending)
3. Run i2i generation against the base image with the updated menu data
4. Save output to `generated/screen{N}/` as a new version
5. Commit: `generated: screen{N}-v{VERSION} — <what changed>`
6. Push

### If base image is missing
Tell Frank to upload one to `base/screen{N}/` in this repo.

## Menu Board USB Sync Utility

This repository includes a utility to automatically sync the latest menu images to connected USB drives labeled `SCREEN-1` and `SCREEN-2`, while archiving older menus.

### How to Use

1. Plug in your USB drive(s) (`SCREEN-1` and/or `SCREEN-2`).
2. Double-click the [Sync-Menus.bat](file:///C:/Users/figon/.gemini/antigravity/scratch/maza-menu-boards/Sync-Menus.bat) file in the root of the repository.
3. The script will:
   - Run `git pull` automatically to ensure it has the newest images.
   - Detect the drive letter for `SCREEN-1` and `SCREEN-2`.
   - Find the highest version menu file (e.g. `screen1-v11.png`).
   - Move any old menu files in the USB drive root to the `archive/` folder on that drive.
   - Copy the newest file to the USB drive root.

### Creating a Desktop Shortcut

To make running this utility even easier:
1. Right-click [Sync-Menus.bat](file:///C:/Users/figon/.gemini/antigravity/scratch/maza-menu-boards/Sync-Menus.bat).
2. Select **Show more options** (if on Windows 11) -> **Send to** -> **Desktop (create shortcut)**.
3. Rename the shortcut on your Desktop to `Sync Restaurant Menus`.
4. Double-click it anytime you plug in the USB drives to run the update.

