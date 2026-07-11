---
name: spotify-cli
description: Use the standalone spotify-cli JSON CLI for Spotify authentication, search, playback, devices, queue, playlists, saved library items, followed artists, podcast shows and episodes, and music discovery or curation. Trigger when spotify-cli is installed or the user identifies its checkout or virtualenv.
---

# Spotify CLI

Use `spotify-cli` as the account-level Spotify control surface. Prefer compact JSON
and the fewest commands that safely answer or perform the request.

## Locate the tool

Check before planning a command sequence:

1. `command -v spotify-cli`
2. a user-provided checkout's `.venv/bin/spotify-cli` or `venv/bin/spotify-cli`
3. `python -m spotify_cli` when that module is already available

If none exists, state exactly what was checked. Do not invent playback, search, or
library results. Only discuss installation when the user asks for setup help.

## Default invocation

Use compact JSON for agent work:

```bash
spotify-cli --compact COMMAND
```

Inspect `spotify-cli COMMAND --help` rather than guessing an option when a workflow
is not covered below.

## Choose the shortest path

| User intent | Command |
|---|---|
| What is playing? | `playback current` |
| Pause, resume, skip, change volume | `playback pause/play/next/previous/volume` |
| Find and immediately play a likely result | `search-and-play` |
| Inspect candidates without playing | `search` or `search-and-play --dry-run` |
| Select a Spotify Connect device | `devices list`, then `devices transfer` |
| Inspect or add to the queue | `queue get` or `queue add` |
| Manage playlists | `playlists ...` |
| Manage saved tracks, albums, shows, or episodes | `library ...` |
| Manage followed artists | `artists list-followed/follow/unfollow` |
| Inspect a podcast | `search --type show`, then `shows episodes` |

## Authentication

Start diagnosis with:

```bash
spotify-cli doctor
spotify-cli auth status
```

Normal login is `spotify-cli auth login`. If an older cached token lacks scopes
introduced by a CLI upgrade, use:

```bash
spotify-cli auth login --force
```

The durable config is normally
`${XDG_CONFIG_HOME:-~/.config}/spotify-cli/spotify-cli.conf`. Useful helpers are:

```bash
spotify-cli config init --client-id "your-client-id"
spotify-cli config show
```

Read `references/headless-auth.md` only for remote/headless login.

## Playback and search

Direct transport actions need no read-before-write preflight:

```bash
spotify-cli --compact playback current
spotify-cli --compact playback pause
spotify-cli --compact playback play
spotify-cli --compact playback next
spotify-cli --compact playback volume 50
```

Prefer `search-and-play` for a straightforward request:

```bash
spotify-cli --compact search-and-play "take five"
spotify-cli --compact search-and-play --type artist "Lyle Lovett"
spotify-cli --compact search-and-play --type album "The Road to Ensenada"
spotify-cli --compact search-and-play --type playlist "Bossa Nova"
```

Use `--dry-run` or explicit search when title ambiguity matters:

```bash
spotify-cli --compact search-and-play "take five" --dry-run
spotify-cli --compact search "kind of blue" --type track --limit 5
spotify-cli --compact playback play --uri spotify:track:...
```

For an album, playlist, or artist context:

```bash
spotify-cli --compact playback play --context-uri spotify:album:...
```

For an episode or one or more tracks, repeat `--uri` as needed:

```bash
spotify-cli --compact playback play --uri spotify:episode:...
```

## Devices and queue

```bash
spotify-cli --compact devices list
spotify-cli --compact devices transfer DEVICE_ID --play
spotify-cli --compact queue get
spotify-cli --compact queue add spotify:track:...
```

Playback mutations generally require Premium and an active Spotify Connect device.
If no device is active, ask the user to open Spotify somewhere or transfer to a
device returned by `devices list`.

## Playlists and library

Resolve exact item and playlist identifiers before mutation:

```bash
spotify-cli --compact playlists list --limit 50
spotify-cli --compact playlists add-items PLAYLIST_ID spotify:track:...
spotify-cli --compact playlists remove-items PLAYLIST_ID spotify:track:...
```

Saved items use the `library` family:

```bash
spotify-cli --compact library tracks save spotify:track:...
spotify-cli --compact library albums remove spotify:album:...
spotify-cli --compact library shows save spotify:show:...
spotify-cli --compact library episodes save spotify:episode:...
```

Artist following is separate from saved-library items:

```bash
spotify-cli --compact artists list-followed --limit 10
spotify-cli --compact artists follow spotify:artist:...
spotify-cli --compact artists unfollow spotify:artist:...
```

## Podcasts

Spotify models podcasts as shows containing episodes:

```bash
spotify-cli --compact search "No Hay Tos" --type show --limit 5
spotify-cli --compact shows get spotify:show:...
spotify-cli --compact shows episodes spotify:show:... --limit 10
spotify-cli --compact episodes get spotify:episode:...
```

Use the first returned episode as the latest visible result only after confirming
the response order. Account visibility can include private or linked feeds.

The CLI can expose Spotify state, but it is not a durable listening journal or
want-to-listen tracker. Do not invent local tracking files or schemas as part of
this skill; that belongs to a separate user-owned application.

## Discovery and curation

For mood-based discovery or playlist construction, read
`references/curation-patterns.md`. Search results are candidates, not verdicts:
form a thesis, choose anchors, widen carefully, sequence coherently, then iterate.

## Failure handling

Read `references/failure-modes.md` when a command fails. Key rules:

- Empty `playback current` output can validly mean nothing is playing.
- Do not retry mutations blindly after an ambiguous network/API failure; inspect
  state first to avoid duplicate playlist or queue changes.
- Smart Shuffle cannot reliably be restored through the current Web API after a
  shuffle mutation.
- Reauthorize with `auth login --force` after adding scopes to an existing setup.
- Spotify's removed recommendations endpoints are not a usable fallback for
  discovery.

Prefer Spotify URIs from command output. The CLI also accepts supported Spotify
URLs and bare IDs, but URIs preserve the item type explicitly.
