# Frontend Settings / Connections agent package

Date: November 3, 2026, America/Los_Angeles. Environment verified: macOS 26.6.2,
Darwin arm64. Scope: the user's requested frontend plan organization, detailed
steps/tests, AGENTS.md and local skills. **Pass for this documentation/guidance
package.** No Settings prototype or application capability is certified here.

## Delivered organization

- [Frontend plan index](../../frontend/plans/README.md).
- [Connection entrypoint](../../frontend/plans/settings-connections/README.md),
  [SPEC](../../frontend/plans/settings-connections/SPEC.md),
  [execution sequence](../../frontend/plans/settings-connections/EXECUTION_PLAN.md)
  and [test plan](../../frontend/plans/settings-connections/TEST_PLAN.md).
- [Frontend AGENTS.md](../../frontend/AGENTS.md).
- [Design skill](../../frontend/.agents/skills/bearplans-connections-design/SKILL.md)
  and [build skill](../../frontend/.agents/skills/bearplans-connections-build/SKILL.md),
  each with quoted UI metadata/default prompt and normal implicit-invocation policy.

The detailed connection section moved into one canonical frontend specification.
The existing UX plan section-6 anchor forwards there; original plans, historical
reviews, Figma ledger/IDs and handoff paths remain. No global/project skill install
or host-catalog refresh is claimed; frontend AGENTS explicitly links both skills.

The package defines 12 requirements, six design units, nine future application
parents with small execution slices and 54 verification cases. Each case contains
layer/ticket, prerequisites, actions, expected result and evidence; requirement
coverage and unit-to-case maps make it actionable. Ordered units specify inputs,
steps, verification, outputs and exit conditions. Only PROGRESS tracks status.

## Source boundary and preservation

Started with f375f24 and concurrent uncommitted setup work; 674db93 committed
credential routes during preparation. Reconciled that baseline and existing test
homes. Other source continued changing, including connection-route tests; it was
not modified, executed or certified by this package. Earlier CLAUDE changes,
design evidence, duplicate `(1)` files and saved core-trial/user data were preserved.
No app/API/schema/desktop code changes, service startup, credential migration,
provider requests, live secrets or saved user-data access were performed by this
work. Documentation permission did not start UX-C02 or any APP-C slice. No commit
or push was requested/performed.

## Independent reviews and corrections

- Independent test-plan author reviewed current test homes and wrote case contracts.
- Independent skill/guidance author created only the frontend guide/two skills and
  metadata; both passed the bundled skill validator.
- Independent package review identified a real live-scope gap: Google authorization
  for a read-only check could start combined automatic writes. LIVE-02 now requires
  acknowledged Pause across all triggers or an isolated read-only harness before
  authorization; otherwise defer it or establish scope for all bundled exports.
- Corrected same-client Google setup replacement: preserve existing usable sign-in
  or its prior reconnect state; fresh/different-client setup requires sign-in.
- Added explicit Pause coverage for UI mount/reopen with an empty calendar cache,
  which can fetch outside the worker. A deliberate disclosed picker refresh is
  separate one-shot work. Added parent-tick checks against root completion rules
  rather than treating an adapter's inherited behavior as a new product decision.
- Preserved existing authorization when it already covers live work; historical
  success alone is not authorization. No repeat-approval requirement was added.

## Skill forward tests

A separate agent received the skills/raw files with three realistic requests and
performed read-only execution-note dry runs, without intended answers supplied:

1. Figma Settings overview: selected design skill/UX-C02, existing assets/one writer,
   800×900 Light render and FIG-01, without starting all downstream journeys.
2. Local Google Pause implementation: selected build skill/focused APP-C04 plus
   necessary API/UI slices; reused committed credential routes, fake providers and
   scheduler/restart/race checks rather than a cosmetic toggle.
3. Plan organization: kept documentation-only scope; no Figma/app/provider work.

All three routed usefully with no blocking contradiction. The pending bCourses
work-view preference did not block an independent overview or Pause task. Material
Pause details stayed proposed; discovery/test preparation can continue while
resolving them. These are agent-behavior checks, not runtime feature tests.

## Checks actually run

- Python document checks: eight new Markdown files, 72 relative target/fragment
  links; 12 unique CON requirements, six unique UX-C parents, nine unique APP-C
  parents and 54 unique case IDs; requirement/test references and existing test-file
  paths passed. No checkbox status tracker in plan files.
- Bundled validator, both skills: `PYTHONPATH=/private/tmp/bearplans-skill-validation-20261103
  python3 /Users/hiberkeley/.codex/skills/.system/skill-creator/scripts/quick_validate.py
  <skill-directory>` — both **Skill is valid!**.
- YAML metadata checks: quoted strings, 25–64-character short descriptions, correct
  skill invocation in default prompts and no implicit-invocation override passed.
- `git diff --check -- frontend/BEARPLANS_UX_PLAN.md frontend/AGENTS.md frontend/plans
  frontend/.agents docs/PROGRESS.md docs/COMPLETED.md` passed; explicit whitespace
  checks include newly untracked docs not covered by Git's normal diff.
- Existing npm script names, Python/browser/frontend test-file references and
  command prerequisites checked; future commands are labelled not executed.

System and repo Python initially lacked PyYAML; validator imports failed for that
reason. The skill author used cached PyYAML 6.0.3 in a disposable `/private/tmp`
validation directory; no application dependency/lockfile changed. Initial link
checks ran before parallel authors finished their target files; final integrated
links resolved. No application suite/browser/Figma run was needed for Markdown.

## Handoff and limits

Shared PROGRESS now points to the package and is the sole connection/design
status register. UX-C01 review is complete; UX-C02–06/new APP-C execution units
remain unstarted. Existing committed backend capability is not erased by new
unstarted ticket definitions. Resume at the user-authorized phase and reconcile
current source first. Visual, runtime, real-account, accessibility, hardware,
core-trial and release evidence remain separate future gates.
