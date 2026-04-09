# Changelog

## [v3.0.0] - 2026-04-09

### Added
- **Virtual Folders** — create tree-structured virtual folders to organize
  indexed files without moving them on disk. Files can belong to multiple
  folders. Full CRUD with icon/color picker.
- **Search: folder path filter** — filter results by directory path,
  supports `*` wildcards (e.g. `*Work*`, `Documents*`).
- **Search: content toggle** — checkbox to include extracted file text
  in search (off by default for performance).
- **Search: metadata matching** — queries now match against title, artist,
  album, camera model in addition to filename and path.
- **Search: wildcard mode** — any query containing `*` switches from FTS
  to SQLite GLOB automatically.
- **Add to Virtual Folder** — `+ VF` button in search preview panel to
  add any file to a virtual folder without leaving the search view.
- **FX toggle button** — enable/disable all animations and blur effects
  from the topbar. State persisted to localStorage.

### Fixed
- **Double-indexing bug** — adding a parent folder after a subfolder (or
  vice versa) no longer re-indexes already-covered files. Exclusion logic
  uses `os.path.normcase` + trailing separator for correctness on Windows,
  Linux, and macOS.
- **Search render lag** — virtual list now renders only ~15 visible rows
  instead of all 100 results at once.
- **Dashboard polling** — adaptive interval: 3 s when jobs are active,
  15 s when idle (was fixed 5 s).