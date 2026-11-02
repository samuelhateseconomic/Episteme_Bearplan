# Refinement evidence and resumption support

These are Figma-only support files, not application source or a second task tracker.
Current status and the next action live in [PROGRESS](../../../docs/PROGRESS.md).
Use the current native metadata in [the ledger](../figma-node-ledger.json), the
synthetic fixture, the execution record, and the dated review together.

- `native-journey-checks.js`: read-only Map interpreter over installed Figma reactions;
  ten checks passed on November 2. Supply current `META`; no browser execution claim.
- `full-native-audit-draft.js`: read-only broad audit that timed out. Partition and
  cache its reads before reuse; it has not produced a passing full-file result.
- `*-patch-executed.js`: archived executed Figma mutation bodies. **Do not replay**
  against the existing file. They require the original helper and supplied metadata;
  current objects already exist. Reconcile exact IDs before a targeted repair.
- `navigation-last-pass.js`: last successful navigation pass, executed before the
  new row pairs and reverse-reorder frame. Adapt its registry and scope before a
  final navigation/Start pass; it is not proof that the paused tree is fully wired.
- `handoff-draft.md`: preliminary handoff content; not an accepted handoff.

The existing ten named starts are preserved and a separate review launcher was
added. That launcher's reset still needs the later time variables and other final
state integration. Full interaction and post-change rendering checks are pending.
