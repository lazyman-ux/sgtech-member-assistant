# Hosting the Member Community Assistant locally

This app is a small **Flask** web server. "Hosting it locally" means running that
server on your own computer and opening it in your browser. It needs only Python 3
and Flask — no database, no API keys, no internet.

---

## 0. Prerequisites

- **Python 3.9+** installed. Check with:
  ```bash
  python3 --version      # macOS / Linux
  python --version       # Windows
  ```
  If missing, install from https://www.python.org/downloads/ (on Windows, tick
  **"Add Python to PATH"** during install).

## 1. Get the code

```bash
git clone https://github.com/lazyman-ux/sgtech-member-assistant.git
cd sgtech-member-assistant
git checkout add-member-assistant      # until the PR is merged into main
```

*(Or download the ZIP from the repo's green **Code → Download ZIP** button and unzip it.)*

## 2. Start it (one command)

**macOS / Linux**
```bash
bash run.sh
```

**Windows** (double-click `run.bat`, or in cmd/PowerShell)
```bat
run.bat
```

Either script creates an isolated virtualenv, installs Flask, and starts the server.
The first run takes ~20 seconds to install dependencies; later runs are instant.

## 3. Open it

Go to **http://localhost:5000** in your browser.

You should see the **SGTech Member Community Assistant** home page with a mock-login list.

---

## Manual steps (if you prefer, or the script fails)

```bash
python3 -m venv .venv                       # create virtualenv
source .venv/bin/activate                   # macOS/Linux  (Windows: .venv\Scripts\activate)
pip install -r requirements.txt             # install Flask
python app.py                               # start server -> http://localhost:5000
```

## Options

| Want | How |
|------|-----|
| Different port | `PORT=8080 bash run.sh` (macOS/Linux) · `set PORT=8080 && run.bat` (Windows) |
| Auto-reload while editing | `DEBUG=1 bash run.sh` |
| Reach it from another device on your Wi-Fi | It already binds `0.0.0.0`; visit `http://<your-computer-ip>:5000` from the other device (same network) |
| Stop the server | Press **Ctrl+C** in the terminal |

## Verify it works without a browser

```bash
python3 test_app.py        # 18 end-to-end checks; expect "18 passed, 0 failed"
```

## Try the demo

1. **Mock login** — click a sample company (e.g. *1-Net Singapore Pte Ltd*).
2. **Find partners** — type a need, e.g. `cybersecurity firms with healthcare clients in Malaysia`.
3. **Request meeting** — review the drafted message, send.
4. **Contribute** — see matched chapters/sponsorships, express interest.
5. **Staff view** — watch the two success metrics (matches, sponsorship leads) update.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `python3: command not found` | Use `python` instead (Windows), or install Python 3. |
| `Address already in use` / port 5000 busy | Run on another port: `PORT=8080 bash run.sh`. On macOS, port 5000 can be used by AirPlay Receiver — turn it off in System Settings → General → AirDrop & Handoff, or just use another port. |
| `pip install` fails on a read-only path | The scripts use a local `.venv`, which avoids this. Make sure you ran `run.sh`/`run.bat`, not a global `pip`. |
| Page doesn't load | Confirm the terminal shows `Running on http://127.0.0.1:5000` and you opened **http://localhost:5000** (not https). |
