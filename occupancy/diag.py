#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose fuer die Kamera-Personenzaehlung.

Nimmt ein Bild auf, misst Helligkeit/Aufloesung, testet Gesichts- und
Oberkoerper-Erkennung und speichert ein sichtbares Debug-Bild mit Markierungen
unter ~/occ_debug.jpg (zum Anschauen via Pi Connect Dateimanager).

Aufruf:  python3 occupancy/diag.py
"""
import os
import subprocess
import sys

import cv2

from occupancy_counter import cascade_dir

OUT = os.path.expanduser("~/occ_debug.jpg")


def capture(path, t_ms):
    cmd = ["rpicam-still", "-n", "--immediate", "-t", str(t_ms),
           "--width", "640", "--height", "480", "-o", path]
    print(f"  rpicam-still -t {t_ms} ...", flush=True)
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30)
    if r.returncode != 0:
        print("  FEHLER rpicam-still:", r.stderr.decode()[:300])
        return False
    return True


def main():
    tmp = "/tmp/occ_diag.jpg"
    # Laengere Belichtungszeit, damit die Auto-Belichtung einschwingt
    for t_ms in (2000,):
        ok = capture(tmp, t_ms)
        if not ok:
            print("=> Kamera-Aufnahme fehlgeschlagen. Kamera angeschlossen/aktiviert?")
            sys.exit(1)

    img = cv2.imread(tmp)
    if img is None:
        print("=> Bild konnte nicht gelesen werden (Datei leer?).")
        sys.exit(1)

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean, mn, mx = float(gray.mean()), int(gray.min()), int(gray.max())
    print(f"\nBILD: {w}x{h}  | Helligkeit Mittel={mean:.1f}  min={mn}  max={mx}")
    if mean < 25:
        print("  ⚠ SEHR DUNKEL — Bild fast schwarz. Licht/Belichtung ist das Problem,")
        print("    nicht die Erkennung. (Linse abgedeckt? Raum zu dunkel?)")
    elif mean < 60:
        print("  ⚠ eher dunkel — Erkennung evtl. erschwert.")
    else:
        print("  ✓ Helligkeit ok.")

    base = cascade_dir()
    print(f"Cascade-Verzeichnis: {base}")
    face = cv2.CascadeClassifier(os.path.join(base, "haarcascade_frontalface_default.xml"))
    upper = cv2.CascadeClassifier(os.path.join(base, "haarcascade_upperbody.xml"))
    g = cv2.equalizeHist(gray)
    faces = face.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
    ups = upper.detectMultiScale(g, 1.1, 3, minSize=(60, 60))
    print(f"\nERKENNUNG: Gesichter={len(faces)}  Oberkoerper={len(ups)}  -> Zaehlung={max(len(faces), len(ups))}")

    # Markierungen ins Debug-Bild zeichnen
    for (x, y, ww, hh) in faces:
        cv2.rectangle(img, (x, y), (x + ww, y + hh), (0, 255, 0), 2)
        cv2.putText(img, "Gesicht", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    for (x, y, ww, hh) in ups:
        cv2.rectangle(img, (x, y), (x + ww, y + hh), (255, 0, 0), 2)
    cv2.imwrite(OUT, img)
    print(f"\nDebug-Bild gespeichert: {OUT}")
    print("=> In Pi Connect den Dateimanager oeffnen und das Bild anschauen,")
    print("   um zu sehen, was die Kamera tatsaechlich sieht.")


if __name__ == "__main__":
    main()
