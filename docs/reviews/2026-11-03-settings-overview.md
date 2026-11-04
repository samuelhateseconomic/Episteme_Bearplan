# UX-C02 — Settings overview

November 3, 2026 · **Pass with follow-ups** for the bounded overview construction
and static/source review. Author and reviewer: Codex (single writer; source,
structural and visual self-review). Independent review and the actual user
walkthrough remain UX-C06. This does not advance original UX-01–36, application,
provider, hardware or release acceptance.

## Scope and acceptance

The user authorized the first work unit using the design/build guidance.
Selected UX-C02, the first eligible design unit after UX-C01, following
[the execution plan](../../frontend/plans/settings-connections/EXECUTION_PLAN.md#ux-c02--compact-settings-overview-and-navigation).
Used the frontend connection design skill, existing BearPlans design skill and
installed figma-use, generate-design and generate-library skills. Used the build
skill to reconcile runtime contracts; did not implement the application sequence.

Acceptance: enter Settings from existing Plan/work context; see two compact
provider summaries with useful status and last-success evidence; open/close
management detail; understand Google's three functions before consent; retain
the invoking workspace and same timer in the return contract. No credentials or
live provider data belong in the prototype. No task/database/provider records,
application rules or confirmed defaults change. Setup and Pause actions are
static placement references in this unit, with actual journeys reserved for C03–05.

## Delivered editable design

[Free flow section](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-5718)
on Canvas · Flows (2:5), arranged as three columns and two rows outside existing
sections. Existing product/reference IDs were retained. The prior handoff's
89 product/state frames and 46 references remain its historical baseline;
this extension adds six frames, two reusable components and three reference starts.
The separate original launcher remains unchanged.

| State | Frame | Saved 800×900 Light render |
| --- | --- | --- |
| Working overview | [219:5719](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-5719) | [Overview](../../frontend/design/settings-connections/overview-800-light.png) |
| Google management open | [219:5791](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-5791) | [Google](../../frontend/design/settings-connections/manage-google-800-light.png) |
| bCourses management open | [219:5859](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-5859) | [bCourses](../../frontend/design/settings-connections/manage-bcourses-800-light.png) |
| Setup needed / Google scope | [219:5927](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-5927) | [Setup](../../frontend/design/settings-connections/setup-needed-800-light.png) |
| Paused plus connection issue | [219:5999](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-5999) | [Attention](../../frontend/design/settings-connections/paused-attention-800-light.png) |
| Sync in progress | [219:6068](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-6068) | [Syncing](../../frontend/design/settings-connections/syncing-800-light.png) |

The provider component 218:5724 has text properties for provider, status, summary,
evidence, issue and management content, plus visibility properties for issue and
expanded management. Card instances are 752px wide, 141px closed and 287px in the
reviewed expanded examples. Settings gear 218:5743 has a 36px target; its future
accessible name/focus restoration are specified, not runtime-certified.

Reused Button set 3:241, semantic color and spacing/radius variables, and the
existing Heading/Body/Label/Context typography styles. All rendered text is Inter,
the existing Figma fallback; production system-font/default acceptance is unchanged.
Native text, vectors, auto-layout and component instances remain editable.
No image-filled node exists in any of the six frames.

## Navigation and static boundaries

Gear entry is added to Today 5:3972, Week 6:1802, Wednesday 6:1934,
Today paused 14:3112 and Track running 7:2639. Each opens the same Settings overview
as an overlay. Working-state Manage/Hide uses SWAP within that overlay; Plan,
Back to work and the highlighted gear use CLOSE. These new actions do not write
task/timer/completion prototype variables. The overlay preserves its invoking
frame by design; actual scroll/focus restoration still needs preview/runtime checks.

To try the bounded entry use [Today](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=5-3972&starting-point-node-id=5%3A3972&scaling=min-zoom),
then the gear. Direct Settings reference starts have no underlying invoking screen,
so their CLOSE controls are not a return-journey test. Arbitrary existing navigation
outside the five entries was not propagated; C06 owns full wiring and propagation.

Setup-needed, paused/error and syncing frames are explicitly static references.
Connect, Review, Manage in those references and expanded-management commands are
placement only. No fake authentication, successful recovery or Pause state change
is claimed. Canvas note 219:6137 records these boundaries.

## Source reconciliation

Reviewed macOS 26.6.2 (Darwin arm64), source at committed a43a456 and concurrent
uncommitted account-isolation changes. Existing f375f24/674db93 already supplied
data-folder credentials and write-only setup routes. a43a456 adds persistent Pause,
worker coordination, local disconnect plus best-effort revocation, pending-sign-in
guards and a summary status. Old findings that all of these were simply absent
are superseded as source observations; this unit did not rerun their runtime tests.

The design reads dimensions rather than treating the summary status as proof:
saved token/client setup, last-success evidence, busy state, errors and paused
preference remain distinguishable. No invented account email or independent
per-function success times are shown. Combined sync evidence uses the existing
last_success_at field. Calendar reading, owned-calendar publishing and all-task
Google Tasks export are explained, including added bCourses tasks.

Current Google.tsx still refreshes an empty calendar cache on mounting; explicit
calendar-selection routes can also contact Google outside the worker. Durable
worker Pause alone does not certify all automatic paths. The future UI must
respect Pause for mount-triggered refreshes and disclose explicit one-time work.
Concurrent account identity/adoption code is unverified by this review; do not
offer seamless switching or claim that its contract passed. The bCourses review
view location remains a proposed dedicated work view, not a confirmed relocation.

## Checks actually performed

- FIG-01 construction/static slice: inspected all six final renders at 800×900
  Light for readable text, reachability, alignment, clipping and action hierarchy.
  Both expanded examples fit within the frame; the main content has one defined
  vertical-scroll area. Other widths/themes remain C06.
- [Installed structure/reaction evidence](../../frontend/design/settings-connections/overview-audit.json):
  **56/56 assertions passed**, including six editable/font/geometry checks,
  neutral Plan selection, **29 new reaction contracts**, static-reference checks,
  corrected error copy and **10 in-memory overlay return journeys**.
- Six PNGs saved and inspected; no full-screen raster inside Figma.
- Local JSON, relative-link/fragment, evidence dimensions and scoped diff/whitespace
  checks passed: 278 local links/fragments, six PNG dimensions, JSON/ledger matching
  and scoped git diff --check. [Execution evidence](../../frontend/design/settings-connections/overview-checks.json)
  records commands/results, the download failure/recovery and checks not run. No application test suite was run:
  this unit changed only Figma and documentation/evidence.
- No browser/computer-control tool was available. Reactions were inspected and
  modeled, not clicked in the actual Figma preview. User acceptance is pending.

Visual review found and repaired inherited Plan selection, oversized bCourses
command buttons, a component notice whose visibility property overwrote its text
reference, and misleading static-reference navigation that would have replaced an
error/busy sample with the normal successful sample. Final renders reflect those
repairs. Initial Python asset download failed because its certificate store could
not verify the issuer; system curl downloaded the same Figma assets successfully
without disabling TLS verification. No provider connection or credential was used.

## Handoff and remaining work

Next eligible unit is UX-C03: masked bCourses Connect/Replace, validation/failure/
cancel states, course selection and work-view entry. Keep one ticket active.
UX-C04 covers Google setup/OAuth; UX-C05 covers Pause/recovery; UX-C06 covers
responsive/theme propagation, independent review and the bounded user walkthrough.

Detailed Pause defaults and bCourses work-view placement remain labelled proposals.
Prototype construction does not certify app persistence, keyboard/focus,
assistive technology, reflow/zoom, real credentials/OAuth or provider writes.
No application/core-trial/service/database changes, commit or push were performed.
Concurrent backend changes, CLAUDE edits and duplicate untracked files were preserved.


## Navigation correction after user review

The user reported that Settings disappeared on Track, Stats and Assistant.
Cause: the first C02 slice installed only five representative workspace entries;
the main Track-ready, Stats and Assistant frames and their supporting states were
omitted. That was inconsistent navigation and is corrected here.

Added the same existing Settings component to 84 missing headers, including nested
background headers in project/dialog examples. All 95 Canvas · Flows Navigation
headers now contain exactly one gear: 89 workspace entries open Settings as an
overlay and six Settings references close it. Existing actions/IDs were preserved
on every changed header. The review launcher has no navigation header.
The earlier five-entry coverage/propagation statements in this review describe
the initial construction; this correction supersedes them for the flow canvas.

[Navigation audit](../../frontend/design/settings-connections/navigation-audit.json)
reports zero missing/duplicate gears, clipping or sibling overlap; all 89 entry
reactions target the same Settings overlay and its close contract remains installed.
All 84 changed headers retained their original child IDs/reactions.
89 in-memory return models passed. These remain installed-metadata/model evidence,
not actual Figma preview execution.

Visually inspected the corrected [Track](../../frontend/design/settings-connections/track-settings-navigation-800-light.png),
[Stats](../../frontend/design/settings-connections/stats-settings-navigation-800-light.png)
and [Assistant](../../frontend/design/settings-connections/assistant-settings-navigation-800-light.png)
at 800×900 Light. The gear remains at the top right with a 36×36 target; tab
selection and page contents remain visible. No further composition repair needed.
Updated the exact inventory, ledger and canvas boundary note. Static responsive/
theme references on the Screens page remain outside this correction.

**Pass with follow-ups** for the navigation correction: visual and structural
checks passed; actual preview/keyboard/focus and broader UX-C06 acceptance remain
pending. The corrected prototype may need reloading to discard an already-open
preview's cached frame. No app, provider, saved-data, commit or push work.
