# Local-core trial candidate preparation — November 1, 2026

**Preparation: Pass. Seven-day trial and full release: pending.** User requested
continuing after the final planner/readiness check. Selected the recommended local
personal trial scope and recorded the exact tested version before actual use.

Candidate: `bearplans-local-core-2026-11-01`, base commit
`d9b5f90e10579d8687c4ffbd8e132a7121573ac1` plus the existing uncommitted M4
backup/restore implementation and rolling-date correction browser fixture.
Build fingerprint:
`4ba3c8054da2b3db3ffa00beb480485fb376bc9d59567548078a0e860aab05da`,
schema 13. [Manifest](2026-11-01-core-trial-candidate.json) records 137 source/test
SHA-256 entries and four tested production artifact hashes. This is a version
baseline, not a commit, tag, immutable checkout or archival copy.

## Scope decision

Select the offline local planner, countdown/recovery, forest/coins/streaks/stats,
reviewed corrections and backup/restore for personal trial. Existing actual Deep
Idle 7 and Hibernate 4 evidence is included. Separate Standby type 5 remains
**unexercised/unverified**, with no documented supported trigger established under
the reviewed public ARM64 default and a running-kernel/source-version caveat.
See [assessment](2026-11-01-standby5-capability.md). This limited trial selection
does not waive the historical acceptance requirement or certify the complete
M2/M3 matrix. Full release scope still needs an honest closing decision.

Trial command selects the existing proposed configuration: America/Los_Angeles,
rate 1, Birch/Oak/Cherry 30/60/120, retention 7 daily/4 weekly. This does not change
product defaults or older sessions' captured rates. No setting was applied in this
preparation turn. AI, integrations and public release remain deferred.

## Deliverables and verification

- [Detailed operator guide](../CORE_TRIAL_CHECKLIST.md): exact Terminal tabs,
  candidate verifier, normal-data launch, baseline backup/inspection/Finder path,
  private notes copy, normal daily use, history/carryover and closing report.
- [Blank notes template](../CORE_TRIAL_NOTES_TEMPLATE.txt): user copies it to
  Desktop; no personal content or completed-day claim is stored in the repository.
- On actual **macOS 26.6.2 (25G83), Darwin**, the inline preparation verifier used
  `.venv/bin/python`, `hashlib.sha256`, `git ls-files --cached --others
  --exclude-standard -z` and `backend.platform.build_info.current_build()`.
  **Pass:** exact 137-file source/test inventory matches the prior readiness
  capture; all 141 source/test/build hashes match; build identity/schema match.
- Parsed all **nine** guide shell blocks with `/bin/zsh -n`: **Pass**. Executed
  the embedded read-only candidate verifier via `/bin/zsh`: exit 0, printed
  `Candidate verified`, the expected fingerprint and schema 13. It opens no DB.
- New local document links, JSON parse and whitespace checked: **Pass**.
  Scoped progress diff check passed. Existing review-plan whitespace was retained.

No runtime/schema/default change, app launch, database read/write, power change,
backup creation, personal-file creation, timer or reminder occurred. No commit,
push or index/stash modification. Full app tests were not rerun for these
documentation/version-record additions; the matching inputs retain the
[fresh 792-pass/one Windows skip and 136 frontend-pass evidence](2026-11-01-final-planner-readiness.md).

Acceptance for preparation is that the user can identify and verify the tested
version, launch the intended personal folder, preserve a baseline backup and keep
private daily notes without confusing test data with real use. Those user actions
are prepared, not reported completed. Existing records are unaffected; backup
restore remains clean-folder only. The daily notes use a no-overwrite copy.

Next: user follows the guide and reports actual Day 1. Record its actual date,
data path, baseline backup result and any issue in shared progress. Seven actual
days and the closing planner/data/time/reward review remain; no extra unchanged
hardware cycle is scheduled. Candidate changes require a recorded version and
affected verification rather than silently attributing all days to this baseline.
