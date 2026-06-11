# Curation patterns for spotify-cli

Use this when the user's real goal is discovery, mood-shaping, or playlist building rather than exact playback control.

## Default stance

Treat Spotify search results as ingredients, not verdicts.

A good agent flow is:
1. infer the lane
2. gather a few strong anchors
3. widen carefully
4. shape a sequence
5. materialize it as a playlist or a play context

## Infer the lane

Pay attention to signals like:
- smoky
- punchy
- side doors
- late-night
- less slick
- more rhythmic
- songwriter-heavy
- regional specificity

These words are more useful than broad genre labels.

## Build in buckets

Use three buckets:
1. anchors — obvious but strong fits
2. adjacent — genre cousins and near-neighbors
3. tasteful left turns — a few widening moves that preserve the thesis

Do not let the left turns take over. One surprise is charm; five surprises is sabotage.

## Sequence matters

For a playlist seed, prefer an arc instead of a pile:
- open with a thesis track
- reinforce the lane
- widen a little
- return to the lane
- end with something memorable but still coherent

## Smart Shuffle relationship

For standard playlists, a useful pattern is:
- build a clean, coherent seed playlist
- let the user enable Spotify Smart Shuffle in their client afterward

That tends to work better than trying to fake radio endlessly from the CLI alone.
