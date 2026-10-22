# Screenshots

The PNGs in `screenshots/` are previews of each application screen.

They are rendered from the **real member directory** (`input/members.csv`) and the
**actual matching-engine output** (`matcher.py`), so the content — ranked matches,
"why this match" reasons, tags, and the admin metrics — is genuine, not mocked.

To regenerate them:

```bash
python3 -m pip install Pillow
python3 docs/render_screenshots.py
```

For true pixel-perfect browser captures, run the app locally (`bash run.sh`) and
screenshot it in your browser — see `../LOCAL_HOSTING.md`.
