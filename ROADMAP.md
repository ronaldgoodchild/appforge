# Roadmap / ideas

Comment on (or open) an issue first so we don't duplicate work.

## Good first issues
- [x] Add screenshots to the README
- [ ] Split the 1,600-line `appforge.py` into modules (theme, winget, choco, setup)
- [x] Add keyboard shortcuts (Ctrl+F to search, F5 to refresh) - thanks @fatihcvs
- [ ] Add a light theme

## Features
- [ ] **Bundles**: save/load a list of apps and install them all on a new PC (import/export winget JSON)
- [ ] Scoop support
- [ ] Silent/unattended install mode with a log file
- [ ] Show package details (publisher, homepage, license) before installing
- [ ] Scheduled "update everything" task
- [ ] Unit tests for the output parsers (winget/choco text parsing is the most fragile part)
- [ ] GitHub Actions: build and attach `AppForge.exe` to each release
