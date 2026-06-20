"""Flask Backend: Grenzwerte konfigurieren + CSV-Export + JSON-API fuer Node-RED."""
from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, redirect, render_template_string, request, url_for

DB_PATH = Path(__file__).resolve().parent.parent / "smartroom.db"

app = Flask(__name__)


INDEX_HTML = """
<!doctype html>
<title>SmartRoomMonitor</title>
<style>
body { font-family: -apple-system, sans-serif; max-width: 720px; margin: 2em auto; padding: 0 1em; }
h1 { font-size: 1.5em; }
form { display: grid; gap: 0.5em; max-width: 320px; }
input, button { padding: 0.5em; font-size: 1em; }
.muted { color: #666; font-size: 0.9em; }
</style>
<h1>SmartRoomMonitor</h1>
<h2>CO₂ Grenzwerte</h2>
<form method="post" action="{{ url_for('save_thresholds') }}">
  <label>Warnung ab (ppm) <input type="number" name="warn" value="{{ warn }}" min="400" max="2500"></label>
  <label>Kritisch ab (ppm) <input type="number" name="crit" value="{{ crit }}" min="500" max="3000"></label>
  <button type="submit">Speichern</button>
</form>
<p class="muted">Zuletzt geändert: {{ updated }}</p>
<h2>CSV-Export</h2>
<form method="get" action="{{ url_for('export_csv') }}">
  <label>Von <input type="date" name="from" required></label>
  <label>Bis <input type="date" name="to" required></label>
  <button type="submit">Download CSV</button>
</form>
"""


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index() -> str:
    with db() as conn:
        row = conn.execute("SELECT co2_warning, co2_critical, updated_at FROM thresholds WHERE id=1").fetchone()
    warn = row["co2_warning"] if row else 800
    crit = row["co2_critical"] if row else 1200
    updated = row["updated_at"] if row else "—"
    return render_template_string(INDEX_HTML, warn=warn, crit=crit, updated=updated)


@app.post("/thresholds")
def save_thresholds():
    warn = int(request.form["warn"])
    crit = int(request.form["crit"])
    if warn >= crit:
        return "Warnung muss kleiner als Kritisch sein", 400
    with db() as conn:
        conn.execute(
            "UPDATE thresholds SET co2_warning=?, co2_critical=?, updated_at=? WHERE id=1",
            (warn, crit, datetime.utcnow().isoformat(timespec="seconds")),
        )
    return redirect(url_for("index"))


@app.get("/api/latest")
def api_latest():
    """Letzter Messwert + Grenzwerte + Ampel-Status als JSON (fuer Node-RED)."""
    with db() as conn:
        m = conn.execute(
            "SELECT timestamp, co2_ppm, temperature, humidity "
            "FROM measurements ORDER BY id DESC LIMIT 1"
        ).fetchone()
        t = conn.execute("SELECT co2_warning, co2_critical FROM thresholds WHERE id=1").fetchone()
    if not m:
        return {"error": "no data"}, 404
    warn = t["co2_warning"] if t else 800
    crit = t["co2_critical"] if t else 1200
    co2 = m["co2_ppm"]
    status = "red" if co2 >= crit else "yellow" if co2 >= warn else "green"
    return {
        "timestamp": m["timestamp"],
        "co2_ppm": co2,
        "temperature": m["temperature"],
        "humidity": m["humidity"],
        "co2_warning": warn,
        "co2_critical": crit,
        "status": status,
    }


@app.get("/export.csv")
def export_csv():
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    if not (date_from and date_to):
        return "from und to erforderlich", 400
    with db() as conn:
        rows = conn.execute(
            "SELECT timestamp, co2_ppm, temperature, humidity FROM measurements "
            "WHERE date(timestamp) BETWEEN ? AND ? ORDER BY timestamp",
            (date_from, date_to),
        ).fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "co2_ppm", "temperature_c", "humidity_pct"])
    for r in rows:
        writer.writerow([r["timestamp"], r["co2_ppm"], r["temperature"], r["humidity"]])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="smartroom_{date_from}_{date_to}.csv"'},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
