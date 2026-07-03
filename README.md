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
