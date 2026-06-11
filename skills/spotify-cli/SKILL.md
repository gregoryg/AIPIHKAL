---
name: spotify-cli
description: "Use the standalone spotify-cli command-line tool to authenticate with Spotify, inspect playback, control devices and playback, search the catalog, manage playlists, inspect albums, navigate podcast shows and episodes, and save or remove library items. Trigger this skill when a local machine has spotify-cli installed or when the user points you at a repo or virtualenv containing it. The skill includes guidance for locating the binary, handling headless auth, curating vibe-based playlists, navigating podcasts, and declining clearly if spotify-cli is not available."
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

Preferred durable setup: use the local config file:
- `${XDG_CONFIG_HOME:-~/.config}/spotify-cli/spotify-cli.conf`

Example:

```ini
[spotify]
client_id = your-client-id
redirect_uri = http://127.0.0.1:43827/spotify/callback
cache_path = ~/.cache/spotify-cli/token.json
```

Useful setup/inspection commands:

```bash
spotify-cli config init --client-id "your-client-id"
spotify-cli config show
spotify-cli doctor
```

Environment variables still override config-file values when needed:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_REDIRECT_URI`
- `SPOTIFY_CACHE_PATH`
- `SPOTIFY_CONFIG_FILE`

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

If a cached token exists but auth still looks broken, suspect missing client-id configuration before assuming the token itself is dead. With a valid configured client id, stale-token refresh should usually happen automatically through Spotipy.

## Command families

- `auth` — login, logout, status
- `devices` — list and transfer playback
- `playback` — state, current, play, pause, next, previous, seek, repeat, shuffle, volume, recently-played
- `queue` — get and add
- `search` — catalog search
- `search-and-play` — convenience command for finding a likely track, artist, album, or playlist match and starting playback immediately
- `playlists` — list, get, create, add-items, remove-items, update
- `albums` — get, tracks
- `shows` — get, episodes
- `episodes` — get
- `library tracks` — list, save, remove
- `library albums` — list, save, remove
- `library shows` — list, save, remove
- `library episodes` — list, save, remove

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

For direct episode playback:

```bash
spotify-cli --compact playback play --uri spotify:episode:...
```

### Play a specific track

Prefer the convenience command when it is sufficient:

```bash
spotify-cli --compact search-and-play "take five"
```

For inspection without mutation:

```bash
spotify-cli --compact search-and-play "take five" --dry-run
```

If you need manual control over the selected result, use the explicit two-step flow:

```bash
spotify-cli --compact search "kind of blue" --type track --limit 5
spotify-cli --compact playback play --uri spotify:track:...
```

### Play a specific artist, album, or playlist result

`search-and-play` accepts one explicit type for non-track playback targets:

```bash
spotify-cli --compact search-and-play --type artist "Lyle Lovett"
spotify-cli --compact search-and-play --type album "The Road to Ensenada"
spotify-cli --compact search-and-play --type playlist "Bossa Nova"
```

Allowed `search-and-play --type` values are:
- `track` (default)
- `artist`
- `album`
- `playlist`

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
spotify-cli --compact library shows save <show-id-or-uri>
spotify-cli --compact library shows remove <show-id-or-uri>
spotify-cli --compact library episodes save <episode-id-or-uri>
spotify-cli --compact library episodes remove <episode-id-or-uri>
```

### Find recent podcast episodes

Podcasts are navigated as `show -> episodes`, not as tracks.

Typical flow:
1. search for the podcast as a show
2. inspect the top show hit
3. fetch that show's episodes
4. treat the first returned episode as the most recent visible result unless you have reason to think otherwise

```bash
spotify-cli --compact search "No Hay Tos" --type show --limit 5
spotify-cli --compact shows get spotify:show:...
spotify-cli --compact shows episodes spotify:show:... --limit 10
spotify-cli --compact episodes get spotify:episode:...
```

If the user asks for "the latest episode" of a podcast, this is the path to use.

## Discovery and vibe-based curation

When the user wants a mood, lane, or side-door discovery path rather than exact title matching, do not just parrot the first search hit.

Read `references/curation-patterns.md` for the fuller pattern. Short version:
- infer the lane from the user's wording and examples
- prefer a coherent sequence over a heap of plausible tracks
- build a playlist seed that Spotify can then extend with its own shuffle or Smart Shuffle behavior

For iterative playlist building, use a curation-first loop:
1. infer the thesis
2. choose a few strong anchor tracks or artists
3. run targeted searches against the Spotify catalog
4. widen carefully from the good hits
5. build a coherent seed playlist
6. iterate by pruning and adding, rather than assuming the first pass is done

This is especially relevant now that Spotify's old recommendations endpoints are gone. The workflow still works; it just depends on search, inspection, and taste rather than a recommendation API that no longer exists.

## Failure modes and caveats

Before digging too far, prefer:

```bash
spotify-cli doctor
spotify-cli auth status
```

They should tell you whether the config file was found, whether the client id came from config or env, whether the cache exists, and whether the token is currently usable.


Read `references/failure-modes.md` when commands fail or when playback behavior seems inconsistent.

Important short list:
- no active device: playback mutation will fail until Spotify is active somewhere
- Premium is usually required for playback mutation
- `playback current` returning 204-style empty output just means nothing is playing
- shuffle mutation is lossy when Smart Shuffle is active; plain shuffle can be restored, Smart Shuffle generally cannot through the current Web API surface
- show/episode visibility may reflect the authenticated user's account view, including linked premium/supporter feeds such as Patreon-connected podcast variants
- Spotify's old recommendations endpoints have been removed from the Web API; Spotipy still exposes deprecated wrappers, but live calls now return 404

## URI, URL, and ID inputs

The CLI accepts Spotify items in three common forms:
- URI: `spotify:track:...`, `spotify:show:...`, `spotify:episode:...`
- URL: `https://open.spotify.com/track/...`, `https://open.spotify.com/show/...`, `https://open.spotify.com/episode/...`
- bare ID: `...`

Use full URIs when possible. Search results already return them.
