"""End-to-end smoke test for the SGTech Member Community Assistant.

Runs the Flask app in-process (via Flask's test client) and walks the whole
member journey, asserting on the behaviour the hackathon MVP promises:

    mock login -> find partners (ranked + reasons) -> request meeting
    -> send (logged) -> contribute -> express interest (lead logged)
    -> admin dashboard metrics -> advance status to "meeting held"

No server, port, or browser needed. Run:

    ./.venv/bin/python test_app.py          # or: python3 test_app.py
"""
import os
import sys
import tempfile

# Use a throwaway request log so testing never touches your real demo data.
os.environ["TEST_LOG"] = tempfile.mkstemp(suffix="_log.json")[1]

import app as flask_app  # noqa: E402
import data_loader       # noqa: E402

# Point the app at the temporary log file.
flask_app.LOG_PATH = os.environ["TEST_LOG"]

PASS, FAIL = 0, 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  \u2705 {label}")
    else:
        FAIL += 1
        print(f"  \u274c {label}")


def main():
    flask_app.app.config["TESTING"] = True
    client = flask_app.app.test_client()

    print("1. Directory loads")
    stats = data_loader.directory_stats()
    check(f"{stats['total_members']} members loaded (>2000)", stats["total_members"] > 2000)

    print("2. Home page")
    r = client.get("/")
    check("home returns 200", r.status_code == 200)
    check("home shows member count", str(stats["total_members"]).encode() in r.data)

    print("3. Mock login")
    r = client.post("/login", data={"company": "1-Net Singapore Pte Ltd"},
                    follow_redirects=True)
    check("login lands on dashboard", b"Signed in as" in r.data or b"1-Net" in r.data)

    print("4. Find partners (plain-language need)")
    r = client.post("/find", data={"need": "cybersecurity firms with healthcare clients in malaysia"})
    check("returns a ranked match list", b"Top" in r.data and b"matches" in r.data)
    check("each match has a 'why this match' reason", b"Why this match" in r.data)
    check("shows interpreted query terms", b"Interpreted your need" in r.data)

    # grab a target id from the results page
    import re
    m = re.search(rb'name="target_id" value="(\d+)"', r.data)
    check("found a target company to contact", m is not None)
    target_id = m.group(1).decode() if m else "0"

    print("5. Draft + send meeting request")
    r = client.post("/request-meeting",
                    data={"target_id": target_id, "need": "cybersecurity healthcare"})
    check("meeting draft is generated and editable", b"AI-drafted" in r.data)
    r = client.post("/send-request",
                    data={"target_id": target_id, "need": "cyber", "message": "Hello"})
    check("request is logged (confirmation shown)", b"Meeting request logged" in r.data)

    print("6. Find where to contribute")
    r = client.get("/contribute")
    check("suggests opportunities with reasons", b"Why this fits" in r.data)
    check("offers 'Express interest'", b"Express interest" in r.data)

    print("7. Express interest -> sponsorship lead")
    r = client.post("/express-interest", data={"opportunity_id": "aicdc"})
    check("lead is logged (confirmation shown)", b"Sponsorship lead logged" in r.data)

    print("8. Admin dashboard metrics")
    r = client.get("/admin")
    check("admin page renders", r.status_code == 200)
    check("shows 1 sponsorship lead", b'metricbig gold">1' in r.data)
    check("shows 0 successful matches initially", b'metricbig green">0' in r.data)

    print("9. Advance request to 'meeting held' (success metric)")
    m = re.search(rb'name="entry_id" value="(\d+)"', r.data)
    entry_id = m.group(1).decode() if m else "1"
    client.post("/update-status", data={"entry_id": entry_id, "status": "meeting_held"},
                follow_redirects=True)
    r = client.get("/admin")
    check("successful matches now 1", b'metricbig green">1' in r.data)

    print("10. Auth guard")
    client.get("/logout")
    r = client.get("/find", follow_redirects=False)
    check("protected route redirects when logged out", r.status_code in (301, 302))

    print(f"\nRESULT: {PASS} passed, {FAIL} failed")
    # cleanup temp log
    try:
        os.remove(os.environ["TEST_LOG"])
    except OSError:
        pass
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
