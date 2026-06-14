# Failure modes and operational caveats

## spotify-cli not found

If `spotify-cli` is not on `PATH` and no obvious repo-local venv binary exists, say so plainly.

Good response shape:
- say what you checked
- say that you cannot run the requested Spotify action from this machine yet
- ask the user for the checkout path or an activated environment
- optionally suggest the standard install flow if they want setup help

Do not fabricate search results, playlist state, or playback state when the CLI is unavailable.

## No active device

Playback mutation often requires an active Spotify Connect session.

Symptoms:
- play/pause/next/previous/seek/volume fail
- Spotify reports no active device or no active playback session

Usual fix:
- open Spotify on a phone, desktop, TV, or web player
- start playback briefly
- retry or transfer playback to the desired device

## Premium limitations

Playback mutation generally requires Spotify Premium.

Reads usually still work:
- search
- playlists list/get
- albums get/tracks
- library list
- recently played

## Empty playback is not a failure

If `playback current` or `playback state` returns the CLI's friendly empty result, treat that as valid state rather than a broken command.

## Smart Shuffle caveat

The CLI can read `smart_shuffle` when Spotify exposes it, but using the Web API shuffle mutation usually drops playback back to ordinary shuffle. Re-enabling shuffle through the API restores plain shuffle, not Smart Shuffle.

Treat shuffle mutation as lossy when Smart Shuffle is active.

## Missing scopes after a local upgrade

If a command that mutates followed artists starts failing with 403 after the CLI was upgraded, suspect an old cached token that predates the new follow scopes.

Usual fix:

```bash
spotify-cli auth login --force
```

The CLI may now ask for additional Spotify permissions such as artist follow read/modify.

## Search result weirdness

Spotify search sometimes returns musically adjacent but semantically wrong top hits. If the user asks for a phrase that could be a song, album, mood, or canonical jazz object lesson, inspect the first result before assuming it is correct.

For curated workflows, use search as a candidate generator rather than as a truth oracle.
