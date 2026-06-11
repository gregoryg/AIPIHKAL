---
name: spotify-cli
description: "Use the standalone spotify-cli command-line tool to authenticate with Spotify, inspect playback, control devices and playback, search the catalog, manage playlists, inspect albums, and save or remove library items. Trigger this skill when a local machine has spotify-cli installed or when the user points you at a repo or virtualenv containing it. The skill includes guidance for locating the binary, handling headless auth, curating vibe-based playlists, and declining clearly if spotify-cli is not available."
---

# spotify-cli

Use the standalone `spotify-cli` tool as a JSON-first control surface for Spotify.

## Find the binary first

Check for `spotify-cli` before planning any command sequence.

Preferred lookup order:
1. `command -v spotify-cli`
2. If the user pointed to a project checkout, check likely local venv paths such as:
   - `./.venv/bin/spotify-cli`
   - `./venv/bin/spotify-cli`
3. If a Python environment is already active and `spotify_cli` is importable, `python -m spotify_cli` is an acceptable fallback.

If the tool is not found, do not bluff and do not invent Spotify results from thin air.

Respond plainly with what you checked and what the user can do next. Example shape:

- `spotify-cli` is not on `PATH`
- no obvious repo-local venv binary was found
- if you have this tool in a checkout, point me at that directory or activate the environment first

If the user wants setup help, suggest the usual developer path:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

## Prefer compact JSON

For tool-driven usage, prefer:

```bash
spotify-cli --compact ...
```

The CLI is JSON-first already; `--compact` just makes it less chatty on the wire.

## Auth workflow

Required environment variables are usually:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_REDIRECT_URI`

Optional:
- `SPOTIFY_CACHE_PATH`

Compatibility aliases may also work:
- `SPOTIPY_CLIENT_ID`
- `SPOTIPY_REDIRECT_URI`

Canonical auth commands:

```bash
spotify-cli auth status
spotify-cli auth login
spotify-cli auth logout
```

For headless or remote usage, read `references/headless-auth.md`.

## Command families

- `auth` — login, logout, status
- `devices` — list and transfer playback
- `playback` — state, current, play, pause, next, previous, seek, repeat, shuffle, volume, recently-played
- `queue` — get and add
- `search` — catalog search
- `playlists` — list, get, create, add-items, remove-items, update
- `albums` — get, tracks
- `library tracks` — list, save, remove
- `library albums` — list, save, remove

## Canonical patterns

### What is playing?

Use one call:

```bash
spotify-cli --compact playback current
```

Do not chain `playback state` unless you also need device/shuffle/repeat details.

### Pause, resume, skip, volume

Use direct actions; no preflight needed.

```bash
spotify-cli --compact playback pause
spotify-cli --compact playback play
spotify-cli --compact playback next
spotify-cli --compact playback previous
spotify-cli --compact playback volume 50
```

### Play a specific track

Search first, then play the resulting track URI.

```bash
spotify-cli --compact search "kind of blue" --type track --limit 1
spotify-cli --compact playback play --uri spotify:track:...
```

### Play an album, playlist, or artist context

Search for the context type, then pass its URI with `--context-uri`.

```bash
spotify-cli --compact search "miles davis kind of blue" --type album --limit 1
spotify-cli --compact playback play --context-uri spotify:album:...
```

For artist-context playback, Spotify handles the downstream sequencing.

### Transfer playback

```bash
spotify-cli --compact devices list
spotify-cli --compact devices transfer <device-id> --play
```

### Add an item to the queue

```bash
spotify-cli --compact queue add spotify:track:...
```

### Add a track to a playlist

Typical flow:
1. search for the track URI or use the currently playing track
2. locate the playlist id
3. add the item

```bash
spotify-cli --compact playlists list --limit 50
spotify-cli --compact playlists add-items <playlist-id> spotify:track:...
```

### Save or unsave library items

```bash
spotify-cli --compact library tracks save <track-id-or-uri>
spotify-cli --compact library tracks remove <track-id-or-uri>
spotify-cli --compact library albums save <album-id-or-uri>
spotify-cli --compact library albums remove <album-id-or-uri>
```

## Discovery and vibe-based curation

When the user wants a mood, lane, or side-door discovery path rather than exact title matching, do not just parrot the first search hit.

Read `references/curation-patterns.md` for the fuller pattern. Short version:
- infer the lane from the user's wording and examples
- prefer a coherent sequence over a heap of plausible tracks
- build a playlist seed that Spotify can then extend with its own shuffle or Smart Shuffle behavior

## Failure modes and caveats

Read `references/failure-modes.md` when commands fail or when playback behavior seems inconsistent.

Important short list:
- no active device: playback mutation will fail until Spotify is active somewhere
- Premium is usually required for playback mutation
- `playback current` returning 204-style empty output just means nothing is playing
- shuffle mutation is lossy when Smart Shuffle is active; plain shuffle can be restored, Smart Shuffle generally cannot through the current Web API surface

## URI, URL, and ID inputs

The CLI accepts Spotify items in three common forms:
- URI: `spotify:track:...`
- URL: `https://open.spotify.com/track/...`
- bare ID: `...`

Use full URIs when possible. Search results already return them.
