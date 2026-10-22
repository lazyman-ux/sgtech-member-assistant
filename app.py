"""SGTech Member Community Assistant — Flask MVP.

Run:
    python3 app.py
Then open http://localhost:5000
"""
from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import data_loader
import matcher

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
LOG_PATH = os.environ.get("TEST_LOG") or os.path.join(DATA_DIR, "request_log.json")
OPP_PATH = os.path.join(DATA_DIR, "opportunities.json")

app = Flask(__name__)
app.secret_key = "sgtech-hackathon-demo-key"  # demo only

# A curated shortlist of well-profiled sample companies for the mock login,
# so the demo always starts from a member with rich data.
SAMPLE_LOGIN_HINTS = [
    "1-Net Singapore Pte Ltd",
    "2Stallions Pte. Ltd.",
    "8C8 Cloud",
]


# --------------------------------------------------------------------------- #
# Opportunities + request log helpers
# --------------------------------------------------------------------------- #
def load_opportunities():
    with open(OPP_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _read_log():
    if not os.path.exists(LOG_PATH):
        return []
    try:
        with open(LOG_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []


def _write_log(entries):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2)


def add_log_entry(entry: dict) -> dict:
    entries = _read_log()
    entry["id"] = (max((e["id"] for e in entries), default=0) + 1)
    entry["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entries.append(entry)
    _write_log(entries)
    return entry


# --------------------------------------------------------------------------- #
# Session / current member
# --------------------------------------------------------------------------- #
def current_member():
    mid = session.get("member_id")
    if mid is None:
        return None
    return data_loader.get_member(mid)


@app.context_processor
def inject_globals():
    return {"me": current_member(), "stats": data_loader.directory_stats()}


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    members = data_loader.load_members()
    # Suggested sample logins (prefer the curated, data-rich ones).
    suggested = []
    for name in SAMPLE_LOGIN_HINTS:
        m = data_loader.find_member_by_name(name)
        if m:
            suggested.append(m)
    # Top up with a few random well-populated members.
    rich = [m for m in members if m["expertise"] and m["sectors"]]
    random.seed(42)
    for m in random.sample(rich, min(6, len(rich))):
        if m not in suggested:
            suggested.append(m)
    return render_template("index.html", suggested=suggested[:8])


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("company", "").strip()
    m = data_loader.find_member_by_name(name)
    if not m:
        # fall back to a contains-search so partial names still work
        for cand in data_loader.load_members():
            if name.lower() and name.lower() in cand["name"].lower():
                m = cand
                break
    if not m:
        return redirect(url_for("index"))
    session["member_id"] = m["id"]
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    me = current_member()
    if not me:
        return redirect(url_for("index"))
    return render_template("dashboard.html")


@app.route("/find", methods=["GET", "POST"])
def find():
    me = current_member()
    if not me:
        return redirect(url_for("index"))
    results, terms, need = [], [], ""
    if request.method == "POST":
        need = request.form.get("need", "").strip()
        if need:
            members = data_loader.load_members()
            results, terms = matcher.find_partners(need, members, exclude_id=me["id"])
    return render_template("find.html", results=results, terms=terms, need=need)


@app.route("/request-meeting", methods=["POST"])
def request_meeting():
    me = current_member()
    if not me:
        return redirect(url_for("index"))
    target = data_loader.get_member(int(request.form["target_id"]))
    need = request.form.get("need", "")
    draft = matcher.draft_meeting_message(me, target, need)
    return render_template(
        "request_meeting.html", target=target, need=need, draft=draft
    )


@app.route("/send-request", methods=["POST"])
def send_request():
    me = current_member()
    if not me:
        return redirect(url_for("index"))
    target = data_loader.get_member(int(request.form["target_id"]))
    message = request.form.get("message", "")
    entry = add_log_entry(
        {
            "kind": "meeting_request",
            "requester": me["name"],
            "requester_id": me["id"],
            "target": target["name"],
            "target_id": target["id"],
            "need": request.form.get("need", ""),
            "message": message,
            "status": "sent",
        }
    )
    return render_template("confirmation.html", entry=entry, kind="meeting")


@app.route("/contribute")
def contribute():
    me = current_member()
    if not me:
        return redirect(url_for("index"))
    opportunities = load_opportunities()
    suggestions = matcher.find_contributions(me, opportunities)
    return render_template("contribute.html", suggestions=suggestions)


@app.route("/express-interest", methods=["POST"])
def express_interest():
    me = current_member()
    if not me:
        return redirect(url_for("index"))
    opportunities = {o["id"]: o for o in load_opportunities()}
    opp = opportunities.get(request.form["opportunity_id"])
    entry = add_log_entry(
        {
            "kind": "sponsorship_lead",
            "requester": me["name"],
            "requester_id": me["id"],
            "target": opp["name"],
            "opportunity_id": opp["id"],
            "opportunity_type": opp["type"],
            "owner": opp.get("owner", ""),
            "status": "lead",
        }
    )
    return render_template("confirmation.html", entry=entry, kind="contribution", opp=opp)


@app.route("/update-status", methods=["POST"])
def update_status():
    """Admin can advance a meeting request toward 'meeting held' (success metric)."""
    entries = _read_log()
    target_id = int(request.form["entry_id"])
    new_status = request.form["status"]
    for e in entries:
        if e["id"] == target_id:
            e["status"] = new_status
            break
    _write_log(entries)
    return redirect(url_for("admin"))


@app.route("/admin")
def admin():
    entries = _read_log()
    meeting_requests = [e for e in entries if e["kind"] == "meeting_request"]
    sponsorship_leads = [e for e in entries if e["kind"] == "sponsorship_lead"]
    # Success metric 1: matches that were accepted or where a meeting was held.
    successful_matches = [
        e for e in meeting_requests if e["status"] in ("accepted", "meeting_held")
    ]
    metrics = {
        "total_requests": len(meeting_requests),
        "successful_matches": len(successful_matches),
        "sponsorship_leads": len(sponsorship_leads),
    }
    return render_template(
        "admin.html",
        meeting_requests=sorted(meeting_requests, key=lambda e: e["id"], reverse=True),
        sponsorship_leads=sorted(sponsorship_leads, key=lambda e: e["id"], reverse=True),
        metrics=metrics,
    )


if __name__ == "__main__":
    import os as _os

    print("Loading SGTech member directory...")
    stats = data_loader.directory_stats()
    print(f"  {stats['total_members']} members loaded.")
    port = int(_os.environ.get("PORT", "5000"))
    # DEBUG=1 enables the auto-reloader for local development.
    debug = _os.environ.get("DEBUG") == "1"
    print(f"Open http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=debug)
