#!/usr/bin/env python3
"""
steam_refresh.py – Updates Steam data in a Coop Games Tracker Gist
-------------------------------------------------------------------
Fetches the Gist, iterates over all watchlist games with a Steam AppID,
pulls current price / review score / release status from Steam, and
writes the updated data back to the Gist.

Requirements: Python 3.10+, requests
  pip install requests

Usage:
  python steam_refresh.py --gist-id <GIST_ID> --pat <GITHUB_PAT>

  Or via environment variables:
  GIST_ID=... GITHUB_PAT=... python steam_refresh.py

  Dry run (fetch + print, no write):
  python steam_refresh.py --dry-run
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("requests nicht installiert. Bitte: pip install requests")
    sys.exit(1)


GIST_API     = "https://api.github.com/gists/{gist_id}"
DETAILS_URL  = "https://store.steampowered.com/api/appdetails"
REVIEWS_URL  = "https://store.steampowered.com/appreviews/{appid}"
GIST_FILE    = "coop_games_data.json"
REQUEST_DELAY = 1.2  # seconds between Steam requests


# ---------------------------------------------------------------------------
# GitHub Gist
# ---------------------------------------------------------------------------

def gist_get(gist_id: str, pat: str) -> dict:
    resp = requests.get(
        GIST_API.format(gist_id=gist_id),
        headers={"Authorization": f"token {pat}", "Accept": "application/vnd.github+json"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def gist_patch(gist_id: str, pat: str, content: str):
    payload = {"files": {GIST_FILE: {"content": content}}}
    resp = requests.patch(
        GIST_API.format(gist_id=gist_id),
        headers={"Authorization": f"token {pat}", "Accept": "application/vnd.github+json"},
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Steam API
# ---------------------------------------------------------------------------

def steam_details(appid: int) -> dict | None:
    try:
        resp = requests.get(
            DETAILS_URL,
            params={"appids": appid, "cc": "DE", "l": "english"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        entry = data.get(str(appid), {})
        return entry.get("data") if entry.get("success") else None
    except Exception as e:
        print(f"    ⚠ Details fehlgeschlagen: {e}", file=sys.stderr)
        return None


def steam_reviews(appid: int) -> dict | None:
    try:
        resp = requests.get(
            REVIEWS_URL.format(appid=appid),
            params={"json": 1, "language": "all", "purchase_type": "all", "num_per_page": 0},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("query_summary") if data.get("success") == 1 else None
    except Exception as e:
        print(f"    ⚠ Reviews fehlgeschlagen: {e}", file=sys.stderr)
        return None


def fetch_steam_data(appid: int) -> dict:
    """Returns dict with steam_status, price, review_pct, review_count."""
    result = {"steam_status": "unknown", "price": None, "review_pct": None, "review_count": None}

    details = steam_details(appid)
    time.sleep(REQUEST_DELAY)

    if not details:
        return result

    genres = details.get("genres", [])
    is_ea = any(g["description"] == "Early Access" for g in genres)
    rd = details.get("release_date", {})
    coming_soon = rd.get("coming_soon", True)

    if coming_soon:
        result["steam_status"] = "unreleased"
    elif is_ea:
        result["steam_status"] = "ea"
    else:
        result["steam_status"] = "released"

    price_info = details.get("price_overview")
    if price_info:
        result["price"] = price_info.get("final_formatted", "")
    elif details.get("is_free"):
        result["price"] = "Free to Play"

    reviews = steam_reviews(appid)
    time.sleep(REQUEST_DELAY)

    if reviews:
        total = reviews.get("total_positive", 0) + reviews.get("total_negative", 0)
        result["review_count"] = total
        if total > 0:
            result["review_pct"] = round(reviews["total_positive"] / total * 100)

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global REQUEST_DELAY

    parser = argparse.ArgumentParser(description="Steam-Daten im Coop Games Gist aktualisieren")
    parser.add_argument("--gist-id", default=os.environ.get("GIST_ID"), help="GitHub Gist ID")
    parser.add_argument("--pat",     default=os.environ.get("GITHUB_PAT"), help="GitHub Personal Access Token (gist scope)")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht schreiben")
    parser.add_argument("--delay",   type=float, default=REQUEST_DELAY, help="Sekunden zwischen Steam-Requests")
    args = parser.parse_args()

    REQUEST_DELAY = args.delay

    if not args.gist_id or not args.pat:
        print("Fehler: --gist-id und --pat (oder GIST_ID / GITHUB_PAT Umgebungsvariablen) erforderlich.")
        sys.exit(1)

    # --- Gist holen ---
    print(f"Hole Gist {args.gist_id}...")
    gist = gist_get(args.gist_id, args.pat)
    raw = gist.get("files", {}).get(GIST_FILE, {}).get("content")
    if not raw:
        print(f"Fehler: '{GIST_FILE}' nicht im Gist gefunden.")
        sys.exit(1)

    data = json.loads(raw)
    watchlist = data.get("watchlist", [])

    games_with_appid = [g for g in watchlist if g.get("appid")]
    print(f"{len(watchlist)} Spiele im Gist, {len(games_with_appid)} mit Steam AppID.\n")

    # --- Steam-Daten abrufen ---
    updated = 0
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for i, game in enumerate(watchlist, 1):
        appid = game.get("appid")
        if not appid:
            print(f"[{i}/{len(watchlist)}] {game.get('name', '?')} – kein AppID, übersprungen")
            continue

        print(f"[{i}/{len(watchlist)}] {game['name']} (AppID {appid})...", end=" ", flush=True)

        steam = fetch_steam_data(int(appid))

        changes = []
        for key in ("steam_status", "price", "review_pct", "review_count"):
            if steam[key] is not None and game.get(key) != steam[key]:
                game[key] = steam[key]
                changes.append(key)

        game["steam_updated"] = timestamp
        updated += 1

        status_str = steam["steam_status"]
        review_str = f"{steam['review_pct']}%" if steam["review_pct"] else "—"
        price_str  = steam["price"] or "—"
        print(f"{status_str} | {price_str} | {review_str}" + (f" ({', '.join(changes)} geändert)" if changes else ""))

    print(f"\n{updated} Spiele abgefragt.")

    if args.dry_run:
        print("Dry-run: Gist wird nicht aktualisiert.")
        return

    # --- Metadaten aktualisieren ---
    data["lastModified"]   = timestamp
    data["lastModifiedBy"] = "steam_refresh"

    # --- Gist aktualisieren ---
    print("Schreibe Gist...")
    gist_patch(args.gist_id, args.pat, json.dumps(data, ensure_ascii=False, indent=2))
    print(f"✅ Gist aktualisiert ({timestamp})")


if __name__ == "__main__":
    main()
