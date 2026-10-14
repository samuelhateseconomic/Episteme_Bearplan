#!/usr/bin/env python3
"""Temporary M0 diagnostic: does this Mac's sleep look different from a hidden browser tab?

Not product code. It exists to produce the sleep/wake evidence the M0 gate requires
(BearPlans_Build_Review_Plan.md, "M0 - Foundation and timer/sleep experiment") and to
choose a timer policy before any timer is built. Delete it once M2 has its own tests.

Run:  python3 tools/sleep_probe.py            (then open http://127.0.0.1:8799/)
      python3 tools/sleep_probe.py --report FILE   (re-analyse an existing log)

It records two independent streams into one JSONL log:

  service  a 1 s sampler in this process, reading three clocks
  browser  1 s ticks posted by the diagnostic page, buffered locally and flushed on wake

The three clocks are what make sleep legible, on macOS specifically:

  wall    time.time()                          real time; an NTP step can move it
  awake   time.monotonic()                     mach_absolute_time: STOPS while asleep
  cont    time.clock_gettime(CLOCK_MONOTONIC)  tracks wall time since boot, sleep included

So across any interval:

  slept  = d_cont  - d_awake     time the machine was suspended
  stall  = d_awake - interval    time the process was awake but not scheduled
  shift  = d_wall  - d_cont      the real-time clock was adjusted

Only `cont` and `awake` are trusted for durations; `wall` is reported but never
differenced for credit, because it is adjustable.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
import time
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
DEFAULT_PORT = 8799
INTERVAL = 1.0
# Below this, a gap is ordinary scheduler jitter rather than something to report.
GAP_THRESHOLD = 2.0

HAS_CONT = hasattr(time, "CLOCK_MONOTONIC")


def clocks() -> dict[str, float]:
    reading = {"wall": time.time(), "awake": time.monotonic()}
    # On Linux CLOCK_MONOTONIC excludes suspend and CLOCK_BOOTTIME includes it; on macOS
    # CLOCK_MONOTONIC is the sleep-inclusive one. Prefer BOOTTIME where it exists.
    cont = getattr(time, "CLOCK_BOOTTIME", None) or (time.CLOCK_MONOTONIC if HAS_CONT else None)
    if cont is not None:
        reading["cont"] = time.clock_gettime(cont)
    return reading


def utc_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class Log:
    """Append-only JSONL, flushed per record so a hard power loss still leaves evidence."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._handle = path.open("a", encoding="utf-8")

    def write(self, record: dict) -> None:
        with self._lock:
            self._handle.write(json.dumps(record) + "\n")
            self._handle.flush()

    def close(self) -> None:
        with self._lock:
            self._handle.close()


def sampler(log: Log, stop: threading.Event) -> None:
    """Sample the clocks every INTERVAL seconds until asked to stop."""
    while not stop.is_set():
        log.write({"stream": "service", "at": utc_iso(), **clocks()})
        # Wait on the event rather than sleeping, so Ctrl+C stops us promptly.
        stop.wait(INTERVAL)


# --------------------------------------------------------------------------- analysis


def analyse(path: Path) -> dict:
    service, browser, markers = [], [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        {"service": service, "browser": browser, "marker": markers}.get(record.get("stream"), []).append(record)

    events = []
    for before, after in zip(service, service[1:]):
        if "cont" not in before or "cont" not in after:
            continue
        d_cont = after["cont"] - before["cont"]
        if d_cont < INTERVAL + GAP_THRESHOLD:
            continue
        d_awake = after["awake"] - before["awake"]
        d_wall = after["wall"] - before["wall"]
        slept = d_cont - d_awake
        stall = d_awake - INTERVAL
        events.append(
            {
                "from": before["at"],
                "to": after["at"],
                "gap_s": round(d_cont, 3),
                "slept_s": round(slept, 3),
                "stalled_s": round(max(stall, 0.0), 3),
                "clock_shift_s": round(d_wall - d_cont, 3),
                # A suspend freezes the process, so nearly the whole gap shows as sleep.
                "verdict": "machine slept" if slept > 0.5 * d_cont else "process stalled while awake",
            }
        )

    # The browser stream is only ever corroborating evidence: a hidden tab is throttled
    # even though nothing slept, which is exactly the confusion this probe has to resolve.
    browser_gaps = []
    for before, after in zip(browser, browser[1:]):
        d = (after["perf_ms"] - before["perf_ms"]) / 1000.0
        if d >= INTERVAL + GAP_THRESHOLD:
            browser_gaps.append(
                {
                    "from": before["at"],
                    "to": after["at"],
                    "gap_s": round(d, 3),
                    "visibility": before.get("visibility"),
                }
            )

    return {
        "log": str(path),
        "service_samples": len(service),
        "browser_samples": len(browser),
        "span_s": round(service[-1]["cont"] - service[0]["cont"], 1) if len(service) > 1 and "cont" in service[0] and "cont" in service[-1] else 0.0,
        "markers": markers,
        "sleep_events": events,
        "browser_gaps": browser_gaps,
    }


def print_report(report: dict) -> None:
    print()
    print("=" * 72)
    print("BearPlans M0 sleep/wake probe -- report")
    print("=" * 72)
    print(f"log             : {report['log']}")
    print(f"service samples : {report['service_samples']}  over {report['span_s']} s")
    print(f"browser samples : {report['browser_samples']}")

    if report["markers"]:
        print("\nMarkers you recorded:")
        for m in report["markers"]:
            print(f"  {m['at']}  {m.get('label', '')}")

    print("\nService-side gaps (the authoritative stream):")
    if not report["sleep_events"]:
        print("  none -- the sampler ran continuously; nothing slept and nothing stalled.")
    for e in report["sleep_events"]:
        print(f"  {e['from']} -> {e['to']}")
        print(f"    total gap {e['gap_s']} s | slept {e['slept_s']} s | stalled {e['stalled_s']} s")
        print(f"    real-time clock shift vs continuous clock: {e['clock_shift_s']} s")
        print(f"    verdict: {e['verdict']}")

    print("\nBrowser-side gaps (corroborating only):")
    if not report["browser_gaps"]:
        print("  none.")
    for g in report["browser_gaps"]:
        print(f"  {g['from']} -> {g['to']}  gap {g['gap_s']} s  (tab was {g['visibility']})")

    slept = [e for e in report["sleep_events"] if e["verdict"] == "machine slept"]
    stalled = [e for e in report["sleep_events"] if e["verdict"] != "machine slept"]
    print("\nReading of this run:")
    if slept and report["browser_gaps"]:
        print("  Both streams gapped and the awake clock stood still -> the machine slept.")
    elif slept:
        print("  The service measured sleep even without browser corroboration.")
    elif report["browser_gaps"]:
        print("  The browser gapped while the service kept sampling and neither clock lost time")
        print("  -> a throttled hidden tab, NOT sleep. This is exactly the case a visibility")
        print("  event cannot tell apart on its own.")
    elif stalled:
        print("  The sampler was delayed while the machine stayed awake (no time was lost to")
        print("  sleep). Treat this as a stall, not sleep.")
    else:
        print("  No gap in either stream.")
    if slept and stalled:
        print("  Note: this run also contains awake stalls; they are listed separately above.")
    print("=" * 72)
    print()


# --------------------------------------------------------------------------- web

PAGE = """<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BearPlans sleep probe</title>
<style>
 :root{color-scheme:light dark;--fg:#1a1a1a;--bg:#fff;--mut:#666;--line:#ddd;--ok:#0a7d32;--warn:#b35b00}
 @media (prefers-color-scheme:dark){:root{--fg:#eee;--bg:#161616;--mut:#aaa;--line:#333;--ok:#4ad07a;--warn:#ffa94d}}
 *{box-sizing:border-box}
 body{margin:0;padding:24px 16px;font:15px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif;color:var(--fg);background:var(--bg)}
 main{max-width:760px;margin:0 auto}
 h1{font-size:20px;margin:0 0 4px} p.sub{color:var(--mut);margin:0 0 20px}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:18px 0}
 .card{border:1px solid var(--line);border-radius:10px;padding:12px}
 .k{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut)}
 .v{font-size:22px;font-variant-numeric:tabular-nums;margin-top:3px}
 button{font:inherit;padding:9px 14px;margin:0 8px 8px 0;border:1px solid var(--line);
        border-radius:8px;background:transparent;color:inherit;cursor:pointer}
 button:hover{border-color:var(--mut)} button:focus-visible{outline:2px solid currentColor;outline-offset:2px}
 ol{padding-left:20px} li{margin:7px 0} code{background:color-mix(in srgb,currentColor 10%,transparent);padding:1px 5px;border-radius:4px}
 .status{color:var(--ok)} .status.bad{color:var(--warn)}
</style>
<main>
<h1>BearPlans sleep probe</h1>
<p class="sub">Leave this tab open. The service samples independently &mdash; this page only corroborates.</p>

<div class="grid">
  <div class="card"><div class="k">Page ticks</div><div class="v" id="ticks">0</div></div>
  <div class="card"><div class="k">Tab state</div><div class="v" id="vis">visible</div></div>
  <div class="card"><div class="k">Largest page gap</div><div class="v" id="gap">0.0 s</div></div>
  <div class="card"><div class="k">Posted to service</div><div class="v" id="sent">0</div></div>
</div>

<p><strong>Mark what you are about to do</strong>, so the log explains itself:</p>
<button onclick="mark('ABOUT TO hide this tab')">Hiding the tab</button>
<button onclick="mark('ABOUT TO sleep the Mac (lid close)')">Sleeping the Mac</button>
<button onclick="mark('BACK -- awake again')">I am back</button>
<p class="status" id="status">connected</p>

<ol>
  <li><strong>Baseline.</strong> Leave it alone for ~30 s.</li>
  <li><strong>Hidden tab.</strong> Press <em>Hiding the tab</em>, switch to another app or tab for ~60 s, come back, press <em>I am back</em>.</li>
  <li><strong>Real sleep.</strong> Press <em>Sleeping the Mac</em>, close the lid, wait <strong>at least 60 s</strong>, reopen, press <em>I am back</em>.</li>
  <li>Return to the terminal and press <code>Ctrl+C</code> for the report.</li>
</ol>
</main>
<script>
// Buffer locally: while the machine sleeps nothing can be posted, so ticks are
// flushed on the next wake rather than lost.
let ticks=0,sent=0,maxGap=0,buf=[],last=performance.now();
const $=id=>document.getElementById(id);

setInterval(()=>{
  const now=performance.now(), gap=(now-last)/1000; last=now; ticks++;
  if(gap>maxGap){maxGap=gap; $('gap').textContent=gap.toFixed(1)+' s';}
  buf.push({stream:'browser',at:new Date().toISOString(),perf_ms:now,
            wall_ms:Date.now(),visibility:document.visibilityState});
  $('ticks').textContent=ticks;
},1000);

document.addEventListener('visibilitychange',()=>{
  $('vis').textContent=document.visibilityState;
  // A visibility event fires for a hidden tab AND after wake, which is precisely
  // why it cannot be used on its own to decide that the machine slept.
  buf.push({stream:'browser',at:new Date().toISOString(),perf_ms:performance.now(),
            wall_ms:Date.now(),visibility:document.visibilityState,event:'visibilitychange'});
});

async function flush(){
  if(!buf.length) return;
  const batch=buf; buf=[];
  try{
    await fetch('/samples',{method:'POST',headers:{'Content-Type':'application/json'},
                            body:JSON.stringify(batch)});
    sent+=batch.length; $('sent').textContent=sent;
    $('status').textContent='connected'; $('status').classList.remove('bad');
  }catch(e){
    buf=batch.concat(buf);            // keep them for the next attempt
    $('status').textContent='service unreachable - buffering'; $('status').classList.add('bad');
  }
}
setInterval(flush,2000);

async function mark(label){
  try{ await fetch('/mark',{method:'POST',headers:{'Content-Type':'application/json'},
                            body:JSON.stringify({label})});
       $('status').textContent='marked: '+label; $('status').classList.remove('bad');
  }catch(e){ $('status').textContent='could not record marker'; $('status').classList.add('bad'); }
}
</script>
"""


def make_handler(log: Log):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:  # keep the console readable
            pass

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/":
                self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/report":
                body = json.dumps(analyse(log.path), indent=2).encode("utf-8")
                self._send(200, body, "application/json")
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            try:
                payload = json.loads(self.rfile.read(length) or b"null")
            except ValueError:
                self._send(400, b'{"error":"bad json"}', "application/json")
                return
            if self.path == "/samples" and isinstance(payload, list):
                for record in payload:
                    if isinstance(record, dict):
                        log.write({**record, "stream": "browser"})
            elif self.path == "/mark" and isinstance(payload, dict):
                log.write({"stream": "marker", "at": utc_iso(), "label": str(payload.get("label", ""))[:200], **clocks()})
            else:
                self._send(404, b'{"error":"not found"}', "application/json")
                return
            self._send(200, b'{"ok":true}', "application/json")

    return Handler


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="M0 Mac sleep/wake diagnostic.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--log", type=Path, help="where to append samples (default: ./sleep-probe-<stamp>.jsonl)")
    parser.add_argument("--report", type=Path, help="analyse an existing log and exit")
    args = parser.parse_args(argv)

    if args.report:
        if not args.report.is_file():
            print(f"No such log: {args.report}", file=sys.stderr)
            return 1
        print_report(analyse(args.report))
        return 0

    if not HAS_CONT:
        print("This platform exposes no sleep-inclusive clock; the probe cannot measure sleep.", file=sys.stderr)
        return 1

    path = args.log or Path.cwd() / f"sleep-probe-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
    log = Log(path)
    stop = threading.Event()

    reading = clocks()
    log.write({"stream": "start", "at": utc_iso(), "platform": sys.platform, **reading})

    print("BearPlans M0 sleep/wake probe")
    print(f"  log:    {path}")
    print(f"  open:   http://{HOST}:{args.port}/   (Ctrl+C to stop and print the report)")
    print(f"  clocks: awake={reading['awake']:,.0f}s  continuous={reading.get('cont', 0):,.0f}s")
    print(f"          this machine has slept about {(reading.get('cont', 0) - reading['awake']) / 86400:.2f} days since boot")
    print()

    threading.Thread(target=sampler, args=(log, stop), daemon=True).start()
    server = ThreadingHTTPServer((HOST, args.port), make_handler(log))
    server.daemon_threads = True

    # Serve on a worker and wait here, so Ctrl+C (and SIGTERM, e.g. from an editor
    # stopping the task) always reaches us and always prints the report.
    def on_stop(*_: object) -> None:
        stop.set()

    for name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, name, None)
        if sig is not None:
            signal.signal(sig, on_stop)

    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True).start()
    try:
        while not stop.wait(0.2):
            pass
    except KeyboardInterrupt:
        stop.set()
    finally:
        server.shutdown()
        server.server_close()
        log.write({"stream": "stop", "at": utc_iso(), **clocks()})
        log.close()
    print_report(analyse(path))
    print(f"Re-read this later with:  python3 tools/sleep_probe.py --report {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
