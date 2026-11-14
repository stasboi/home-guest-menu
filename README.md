# おうちごはん — お品書き

An illustrated Japanese-language menu for guests visiting home, featuring 37 dishes. Guests can browse, filter, select meals, and copy/share their wish list without a backend.

## Published site
https://stasboi.github.io/home-guest-menu/

## Photos
**All dish photos are hosted locally in this repository** under `images/`, not loaded from external photo sites at page-view time.

- 34 user-selected reference photographs were downloaded from their pinned original sources and converted to WebP by GitHub Actions.
- 2 photos supplied in chat (Guizhou hot pot dipping sauce and Dijon mustard chicken) are also saved as `images/09.webp` and `images/12.webp`.
- `#20 無調整豆乳＋ミロ` deliberately has no photo.
- Sources for the reference photographs are recorded in `photo-sources.json`. Each dish with a sourced photo links to its reference page. Photographs are illustrative, not pictures of home-prepared dishes.
- A download success/failure report is at `images/download-report.json`.

To replace a photo, upload a new correctly named WebP file to `images/` and update its attribution/reference as needed.

## How to update
Edit `index.html` for the menu, or `photo-sources.json` for pinned original URLs. GitHub Pages publishes the `main` branch root. The photo-caching GitHub Action reruns whenever its source manifest/script/workflow is updated.
