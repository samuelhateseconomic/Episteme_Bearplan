# UX-C03 — bCourses Settings setup and work entry

Date: November 3, 2026. **Pass with follow-ups for bounded Figma construction and installed-action review.** No user acceptance or application/provider execution is certified.

## Scope and acceptance

User requested “continue” after the Settings navigation correction. Executed the next eligible design unit, [UX-C03](../../frontend/plans/settings-connections/EXECUTION_PLAN.md#ux-c03--bcourses-setup-replacement-and-work-entry), using BearPlans design, connections design, figma-use, screen generation and scoped library guidance. Build guidance/source were consulted for coherence only.

Scenario: Settings → bCourses Connect/Replace → masked draft → Check and save → settled result → chosen courses → assignment review. Cancel before submission returns without saving. Errors keep the open sample draft; only Add represents task creation. Course selection changes do not remove local work. No product rule/default was changed. The dedicated assignment-review location remains proposed.

Environment: macOS 26.6.2; `uname -srm` returned Darwin 25.6.0 arm64. Source baseline remains a43a456 with concurrent Google account-isolation work, other documentation and duplicate “(1)” files preserved. No application code, dependency, service, database, credential, core-trial copy, commit or push changed.

## Editable result

File: [BearPlans free canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=2-5).
Session: `5d94b33e-2248-4cee-a5ff-d6427a1d518b`.

| Flow | Section | Scope |
| --- | --- | --- |
| [Connect / Replace](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=234-6386) | 234:6386 | Empty and masked drafts, two busy states, accepted and replaced results |
| [Recovery](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=234-6387) | 234:6387 | Rejected, offline, pre-write failure, uncertain save, saved-access check, retained-data explanation and nine review starts |
| [Courses / review](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=234-6388) | 234:6388 | Three/two selection drafts, loading, empty/unavailable, partial refresh failure, saved result and four work-view states |

21 dialogs at 540px width, with actual heights 222–556px except settled result variants as listed in the inventory; four 800×900 Light work views. Original frame IDs and free-canvas arrangement are preserved. The dialogs are centered overlays with outside interaction NONE. Their height is content-driven. Review has an owned vertical scroll area; the default view has 871px of content in 840px, so the final group line requires scrolling intentionally.

Reused existing Button, Input, Checkbox, Feedback and navigation components with semantic color, space and radius tokens. New course-option component: **233:6184**, with editable Course/Term properties and nested Checkbox. Five narrowly scoped connection text styles reuse the existing scale.

SF Pro was advertised by the font list, but rendered component text reported `hasMissingFont: true` and rejected text-property updates. The final result uses the established **Inter fallback**, with no missing fonts in the 25-state audit. This does not settle the broader product-font decision or migrate existing styles.

Evidence:
- [Exact inventory](../../frontend/design/settings-connections/bcourses-inventory.json)
- [Final structural / installed-action audit](../../frontend/design/settings-connections/bcourses-audit.json)
- [31 action-model checks](../../frontend/design/settings-connections/bcourses-models.json)
- [Connect render](../../frontend/design/settings-connections/bcourses-connect-light.png)
- [Rejection render](../../frontend/design/settings-connections/bcourses-rejected-light.png)
- [Long-course render](../../frontend/design/settings-connections/bcourses-courses-light.png)
- [Work-view render](../../frontend/design/settings-connections/bcourses-review-light.png)
- [Updated management render](../../frontend/design/settings-connections/bcourses-management-light.png)
- Full setup/recovery/course flow PNGs are beside these files. Section export bounds include Figma's section margins; they are not app viewport sizes.

## Source reconciliation and recovery

Read `backend/routes/connections.py`, bCourses routes/domain/client, secrets status persistence, `frontend/src/BCourses.tsx` and connection test definitions. This was inspection, not a fresh runtime test.

- Check is a bounded read-only courses request. Rejection/offline before save leaves the previous credential. Stored token values are never returned or shown.
- Credential write precedes the separate status-file write. A later error or lost response can mean the credential was saved. Therefore “Save not confirmed” does **not** promise rollback. Checking saved access proves access only, not which token was stored; ensuring replacement requires explicitly saving the new token again.
- Separate “Could not save” is explicitly the **pre-credential-write failure** example. It must not be used as generic copy for every failed response.
- Course selection is committed before refresh. Its partial-success state says **Courses saved · refresh failed** and retries refresh, rather than incorrectly treating the selection as unsaved.
- Source auto-fetches on first opening when configured with no prior attempt. New course loading is shown explicitly; manual-refresh scope remains unchanged.
- Only Add creates/reuses the source-linked local task. New source deadlines require Use new due date / Keep mine; planned dates stay separate.
- Token removal/data retention is annotated. Its confirmation/effect states remain UX-C05.

## Wiring and state boundaries

Working Settings now wires Choose courses, Replace token and Review assignments. Setup-needed bCourses Connect is wired. All use overlay SWAP so the invoking workspace remains underneath; Back to work closes the Settings overlay. Direct reference starts do not supply an original work background and cannot prove workspace restoration.

Clicking an empty token field inserts fixed mask glyphs; no real/free text entry exists. Busy save states settle after 2.5 seconds, and course loading after 1.5 seconds. Network/storage are simulated. No live provider URL, token content or provider operation was used.

Six new variables represent only connection demo state: saved two/three selection, management wording, source Add receipt, deadline decision/wording and refresh evidence. All eight existing reset starts now initialize these six **in addition to their preserved prior actions**. Booleans require ALL_SCOPES in this API; the empty scope array is rejected. Strings use TEXT_CONTENT. No existing task/timer/history variable is changed by connection actions.

Selection draft changes are not applied until Save. Cancel preserves the saved count; re-entry uses the saved selection. Review re-entry retains its one Add result and the deadline choice. Resolving a deadline after Add keeps that Add result.

All **99 Navigation headers** now have exactly one Settings gear, including the four added review views. Their gear returns to Settings. The pre-existing 89 workspace overlay entries remain. Review's ordinary top tabs, disabled Refresh/source actions, Dismiss/Restore, unsampled Add and group expansion are identified placement references, to finish in UX-C06. Removal and remaining Google controls retain their later-unit boundaries.

## Verification actually performed

- Live Figma inventory reconciliation before writes.
- Final structural audit: **25 states**, **519 nodes** (115 frames, 265 text nodes, 122 instances, 17 vectors); no image-filled UI, missing/mismatched fonts, overlapping normal-flow siblings or horizontal overflows.
- **80 installed action sources** retrieved in bounded batches; **31/31 model assertions passed** for setup, cancel/reopen, bounded busy results, rejection/offline/pre-write retry, uncertain-save recovery, course cancel/save/re-entry, explicit Add, preserved deadline choice, refresh-only recovery, Settings entry and reset isolation.
- Eight reset starts each contain all six new variable resets; no connection action writes an old work variable.
- Actual-size primary dialog/error/long-name/management/work renders inspected; three full flow compositions rendered. Initial long-text overlaps were repaired with content-height sizing before the final render.
- Final documentation verification: scoped `git diff --check`, inline Python JSON/inventory/ledger/link/PNG validation. See the closing check record below.
- No app test suite run for Figma/docs-only changes.

Construction failures were corrected, not counted as passes: SF Pro missing-font error; invalid empty Boolean scope; missing resolvedType in variable action data; self-target SWAP rejected; oversized read output; one provider-stack index lookup; one JSON serialization helper. Failed canvas writes reported safe rollback; live reconciliation and bounded reads were used before building further. Initial sandbox DNS failed for the screenshot download; approved system curl with normal TLS downloaded the synthetic assets. No automatic approval rejection occurred.

## Follow-ups and next unit

Actual Figma preview clicking, keyboard/Escape/focus restoration, assistive technology, 640/1440 widths, Dark, 200% browser zoom and user walkthrough were **not performed**; no browser/computer-control tools were available. The review's scoped pass is for visual construction/metadata/models, not UX-C06 or runtime acceptance. No new heuristic score was assigned.

Next eligible design unit: **UX-C04**, Google sign-in-file setup and external-browser authorization, including the three-function scope and account mismatch recovery. Not started. UX-C05 handles Pause/recovery/removal; UX-C06 completes responsive wiring and bounded user review. Application slices remain separately scoped and must reuse current backend work.

## Closing content checks

The final inline Python check validates three JSON evidence files, 25 unique frame IDs, 31 passed models, six isolated variables/reset coverage, all 99 header gears, inventory/ledger links, eight PNG headers/dimensions, local Markdown links and scoped whitespace. This records artifact checks, not runtime tests.

Result: **Pass**. Eight PNGs and 278 local links checked; all JSON/ledger,
31 model, six-variable/eight-reset and 99-gear assertions passed. Scoped
`git diff --check -- docs/PROGRESS.md docs/COMPLETED.md frontend/FIGMA_PROTOTYPE.md frontend/design/figma-node-ledger.json` exited 0.
