# Headless spotify-cli auth

Use this when `spotify-cli auth login` must run on a remote or headless machine but the browser lives elsewhere.

## Standard pattern: SSH reverse tunnel

From the local machine that has the browser:

```bash
ssh -R 43827:localhost:43827 user@remote-host
```

Then on the remote host:

```bash
spotify-cli auth login --no-browser
```

Open the printed authorization URL in the local browser. Spotify redirects to the loopback URI on the local machine, and the reverse tunnel carries that callback back to the remote listener.

## Redirect URI requirements

Spotify requires an exact redirect URI match in the developer app settings.

Common value:

```text
http://127.0.0.1:43827/spotify/callback
```

If the app uses a different port or path, the CLI environment and the Spotify app settings must match exactly.

## Common pitfalls

- Start the SSH reverse tunnel before starting login.
- If the callback port is already in use, stop the stray listener or choose a different redirect URI and register it in the Spotify app settings.
- If the browser finishes auth but the CLI never completes, suspect a tunnel or redirect mismatch first.
