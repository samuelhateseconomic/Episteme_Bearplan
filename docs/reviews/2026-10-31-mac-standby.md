# Distinct standby inspection and cancelled observation — October 31, 2026

**Distinct standby/hibernate: unverified; further hardware testing skipped at the
user's request.** The user explicitly said, "go ahead and go for next module,
skip these test". This authorizes starting M4 before this remaining hardware gate;
it does not turn unobserved states into passes. No further sleep action is pending.

Actual Mac15,9, macOS 26.6.2 (25G83), arm64, runtime build `d9b5f90`. Read current
power settings and retained October 31 sleep-state logs with `pmset -g batt`,
`pmset -g cap`, `pmset -g custom`, `pmset -g log`. Retained only timestamped
Sleep/Wake/DarkWake/HibernateStats categories. Inspection at **23:17:50 PDT**:
380 category entries, 281 excluding HibernateStats, 99 logged wakes from Deep
Idle, zero named standby/hibernate transition lines. These are log-event counts,
not a claim of 99 distinct suspend intervals. Evidence:
`.evidence/mac-verification-20261031/standby-inspection/`.

Apple's [power-management definitions](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/IOKit/pwr_mgt/IOPMPrivate.h)
distinguish Standby, Hibernate and Deep Idle sleep types. The retained Deep Idle
labels and mode-3 configuration therefore do not independently establish a
distinct standby/hibernate recovery. This source interpretation does not claim
that all named types must be entered on this particular hardware.

## Preparation and cleanup

Prepared an observer based on the completed extended-sleep instrument; syntax
checked with `ast.parse`. Removed its post-completion cleanup timeout so late
inspection could retain the owned service. No unfinished/paused timeout, power
setting change or keep-awake assertion. Initial proposed battery root:
`/private/tmp/bearplans-mac-standby-20261031-7_m6mhlg/`.
Service port 52562, backend PID 21606, observer exec 55826. User reported battery,
but two host reads still showed AC attached, `ExternalConnected = Yes`, 80%, not
charging. No countdown started. User then selected **"I can only test on AC"**.
Stopped that owned observer/backend with Ctrl+C and closed its test tab.

Fresh AC-specific root:
`/private/tmp/bearplans-mac-standby-ac-20261031-nn0i7i7a/`.
Command:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-standby-ac-20261031-nn0i7i7a/observe.py /private/tmp/bearplans-mac-standby-ac-20261031-nn0i7i7a
```

Owned port **52683**, backend PID **21642**, observer exec **96567**. Agent
selected the synthetic incomplete leaf, 180 minutes and Pine in the UI, then
started **23:20:03.386555 PDT**. SQLite/UI confirmed Running, session
`beef0bac-7314-4679-bc0f-188ed5d8ebf8`, original Pine
`7ead8399-4c57-461f-868d-606f2d3ee779`. Duration provided sleep headroom; it was
not a three-hour precision test. User could not leave the Mac asleep, then
explicitly requested skipping the tests and moving to the next module.

Agent used UI Finish early at **23:20:42 PDT**: saved **38,676,244 µs**, original
unfinished Pine and zero coins. This is cleanup of a synthetic countdown, not
standby evidence. Saved screenshot `cancelled-saved.png`; stopped only owned
observer/backend with Ctrl+C, exec 96567 exited, and closed its test tab. Both
preparations retain sanitized source/JSON/screenshots/manifests in their matching
folders under `.evidence/mac-verification-20261031/`; databases stay outside the
checkout. Normal service/data, existing user edits/index/stashes preserved.
No application source changed during this cancelled hardware observation.

M2/M3's remaining hardware acceptance stays unverified. M4 backup/restore work
is now separately authorized. No additional overnight test or unplug prompt
should be issued unless the user asks to resume hardware testing.
