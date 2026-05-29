# Coop Games Tracker

A simple single-page app for tracking a shared co-op games watchlist.

## Features

- Watchlist with Steam status, prices and review scores
- Play history (Coop Weekly)
- Gaming weekend log (Coop Weekends)
- Search, filter, sort
- JSON export / import

## Setup

1. Create a **private GitHub Gist** containing a file named `coop_games_data.json` with the following content:
   ```json
   { "watchlist": [], "weekly": [], "weekends": [] }
   ```

2. Create a **Personal Access Token** (PAT) at [github.com/settings/tokens](https://github.com/settings/tokens) with `gist` scope.

3. Open the app, click ⚙️ and enter your Gist ID and PAT.

## Data & Privacy

All game data is stored in a private GitHub Gist — not in this repository. The app itself contains no personal data. Without a valid PAT and Gist ID the app shows an empty state.

## Steam data

Steam data (prices, reviews, release status) can be refreshed via an optional proxy URL. Without a proxy the app works offline with cached data.
