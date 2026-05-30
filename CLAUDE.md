# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A zero-dependency single-page app for tracking a shared co-op games watchlist. All code lives in `index.html`. Data is stored in a private GitHub Gist — never in this repo. The app is hosted on GitHub Pages.

## Running locally

```bash
python -m http.server 3001
# open http://localhost:3001/index.html
```

The `.claude/launch.json` configures this for the FleetView preview server.

## Architecture

Everything is in `index.html` — no build step, no framework, no bundler. Vanilla JS + CSS + Bootstrap Icons (CDN).

**Persistence layer:**
- Primary store: private GitHub Gist (`coop_games_data.json`) via GitHub API (`GET`/`PATCH /gists/{id}`)
- Cache: `localStorage` — loaded instantly on startup, Gist syncs async on top
- PAT and Gist ID are stored in `localStorage` only, never in code

**Gist data shape:**
```json
{
  "watchlist": [{ "id", "name", "appid", "category", "status", "steam_status", "price", "review_pct", "review_count", "notes", "added", "steam_updated" }],
  "weekly":    [{ "id", "date", "title", "hours", "notes" }],
  "weekends":  [{ "id", "date", "dateLabel", "title", "location", "special" }],
  "lastModified": "<ISO timestamp>",
  "lastModifiedBy": "<username>"
}
```

**Key JS patterns:**
- `setSyncStatus(state, lastModified, user, error)` — updates both the header chip and the settings panel sync indicator
- `renderGames()` / `renderWeekly()` / `renderWeekends()` — full re-render from in-memory arrays; called on every filter/sort change
- `cycleStatus(id)` — cycles a watchlist game through `candidate → played → wait-ea → abandoned → obsolete → candidate`
- `switchView(view)` — toggles between `watchlist`, `weekly`, `weekends`
- `syncToGist()` / `loadFromGist()` — Gist I/O, debounced on save

**Status enums:**
- `steam_status`: `released` | `ea` | `unreleased` | `unknown`
- `user_status` (game.status): `candidate` | `played` | `wait-ea` | `abandoned` | `obsolete`

**CSS variables** are defined in `:root` — color scheme derived from a heraldic coat of arms (shield blue `#1a4268`, gold `#c89a18`, silver `#bcd0e0`). Responsive breakpoints at `768px` and `540px`.

## Coding conventions

- **Language:** All code, comments, documentation, and GitHub issues must be in **English**
- **No external dependencies** — no npm, no frameworks, no CDN additions beyond Bootstrap Icons
- **No build step** — `index.html` must remain self-contained and directly servable as a static file
- **Privacy:** The app must contain zero personal data. Without a valid PAT + Gist ID it shows only a lock screen
- Prefer editing CSS variables over hardcoded colors
- Test locally with the Python server before committing — keeps git history clean

## Steam data refresh

Steam data is updated via `steam_refresh.py` (CLI, not in-browser):

```bash
pip install requests
python steam_refresh.py --gist-id <GIST_ID> --pat <GITHUB_PAT> [--dry-run]
```

Updates `steam_status`, `price`, `review_pct`, `review_count`, `steam_updated`, `lastModified` in the Gist.

## Open issues

| # | Topic |
|---|---|
| [#1](https://github.com/uceumern/coop-games-app/issues/1) | i18n: English/German via browser language |
| [#2](https://github.com/uceumern/coop-games-app/issues/2) | Dark mode via `prefers-color-scheme` |
| [#3](https://github.com/uceumern/coop-games-app/issues/3) | Remove non-functional Steam Refresh button from UI |
| [#4](https://github.com/uceumern/coop-games-app/issues/4) | Mobile: larger touch targets for action buttons |
| [#5](https://github.com/uceumern/coop-games-app/issues/5) | Platform field per game (Steam, Xbox Game Pass, etc.) |
