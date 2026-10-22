# SGTech Member Community Assistant (Hackathon MVP)

**SGTech × AWS "Build with AI" Hackathon — 22 October 2026**

An AI-powered Member Community Assistant that lets SGTech member companies
self-serve instead of emailing the secretariat:

1. **Mock login** as a sample member company.
2. **Find partners** — type a need in plain language (e.g. *"cybersecurity firms
   with healthcare clients"*) and get the **top 5 matching members**, each with a
   short **"why this match"** explanation.
3. **Request a meeting** — one click drafts a personalised meeting/collab message
   you can review and send. It's saved to a **request log** with a status.
4. **Find where to contribute** — ask *"Where can my company contribute?"* and get
   **3 suggested chapters / sponsorship opportunities** matched to your profile;
   click **Express interest** to log a **sponsorship lead**.
5. **Admin counter** — a staff dashboard showing the two success metrics:
   **# successful matches** and **# sponsorship leads**.

Built around the real **SGTech member directory** (2,080 companies) in
`input/members.csv`. No real CRM, auth, or email integration — everything is
logged in-app, matching the hackathon scope.

---

## Screenshots

> Previews of each screen, rendered from the **real member data and the actual
> matching-engine output**. (See `docs/screenshots/` for full-size images.)

**Home / mock login**
![Home](docs/screenshots/01-home-login.png)

**Member dashboard**
![Dashboard](docs/screenshots/02-dashboard.png)

**Find partners — ranked matches with "why this match"**
![Find results](docs/screenshots/04-find-results.png)

**Find where to contribute**
![Contribute](docs/screenshots/06-contribute.png)

**Staff dashboard — the two success metrics**
![Admin](docs/screenshots/07-admin-dashboard.png)

---

## Quick start

```bash
cd /projects/sandbox
python3 -m venv .venv          # one-time: isolate dependencies
./.venv/bin/python -m pip install -r requirements.txt   # Flask only
./.venv/bin/python app.py
```

Then open **http://localhost:5000**.

> A virtualenv is used because the base Python's user/site directories are
> read-only in this environment. If your Python can install packages globally,
> `pip install -r requirements.txt && python3 app.py` works too.

The request/lead log is written to `data/request_log.json` (created on first use).

---

## How the matching works (explainable, no API keys)

The matching engine (`matcher.py`) is a transparent, keyword- and token-based
scorer — deliberately chosen so it runs offline with zero credentials and so every
result can be **explained** to the user (judges love this):

- The member's free-text need is tokenised and expanded with a small synonym map
  (e.g. *cyber → cybersecurity, security*; *fintech → financial services*).
- Each candidate company is scored on overlap with its `AreaOfExpertise`,
  `BusinessSector`, `CountriesWithPresence` and name, with weights.
- The top 5 are returned with a human-readable **"why this match"** string listing
  the specific overlapping signals.

The same engine powers the **contribution finder**, matching a member's profile to
SGTech chapters and sponsorship packages defined in `data/opportunities.json`.

---

## Project layout

```
app.py                  Flask web app (routes, session, admin dashboard)
matcher.py              Explainable matching engine (partners + contributions)
data_loader.py          Loads & normalises input/members.csv
data/opportunities.json Chapters, committees & sponsorship packages (dummy)
templates/              HTML pages
static/                 CSS
input/members.csv       Recovered SGTech member directory (2,080 companies)
```

## Scope / out of scope (per the worksheet)

- CSV dummy/real data only — **no live CRM** integration.
- **Mock login**, no SSO.
- Requests & leads are **logged in-app** — no real email/calendar sending.
- PDPA note: in production only opted-in members would be discoverable and contact
  details shown only after acceptance. Modelled as a flag, not enforced here.
