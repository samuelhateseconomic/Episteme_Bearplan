# UX plan and design skill — November 1, 2026

**Decision: Pass for documentation and skill-guidance preparation.**
No Figma construction, prototype, app implementation or release gate is passed.

## Request and acceptance

User requested saving the full agreed draft plan as Markdown inside `frontend/`
and creating its agents/skill guidance. Success means the 36-ticket plan is
portable and discoverable, the existing shared guide retains its domain rules,
the repo-local skill validates and gives useful scoped guidance, and the shared
register records actual completion without starting Figma.

Created the [frontend plan](../../frontend/BEARPLANS_UX_PLAN.md), extended
[root AGENTS.md](../../AGENTS.md), and created the
[design skill](../../.agents/skills/bearplans-design/SKILL.md) with minimal UI
metadata and a review/handoff reference. Shared progress remains the single
mutable tracker. UX-01–04 cover this documentation preparation; UX-05–36 remain
Not started. Proposed visual measurements/month filing/Earlier selection remain
draft defaults. Confirmed planned-week Done and both drag operations supersede
older discovery proposals, while current same-day application drops stay no-ops.

No product record, application API, schema, default, timer, reward or task behavior
changed. All source dependencies and the separate core-trial copy are unchanged.
The root moved before this request; canonical paths use
`/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan`, and document links are
repository-relative. No nested checkout or compatibility symlink was created.

## Environment and exact checks

Actual host: Darwin/macOS; existing app Python **3.13.15**. No app suite, build,
service, hardware, model or private-data check is claimed for this docs-only work.
HEAD remains `d9b5f90`; no commit/push.

The app/system Python environments lack PyYAML. Initial validator dependency
inspection failed with `ModuleNotFoundError`; two sandboxed temporary installs
reported no available distribution. The isolated install below then succeeded
through approved elevated network access. It installs only under the temporary
staging folder; no app dependency or lock file was changed.

Commands were run from the canonical root or `/private/tmp` with an explicit shell
because this chat's old default working directory no longer exists.

```sh
/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan/.venv/bin/python -m pip --isolated install --index-url https://pypi.org/simple --target /private/tmp/bearplans-ux-docs-stage/validator-deps --no-cache-dir --disable-pip-version-check --retries 0 --timeout 15 PyYAML
```

Result: temporary **PyYAML 6.0.3** installed successfully.

```sh
PYTHONPATH=/private/tmp/bearplans-ux-docs-stage/validator-deps .venv/bin/python /Users/hiberkeley/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/bearplans-design
PYTHONPATH=/private/tmp/bearplans-ux-docs-stage/validator-deps .venv/bin/python /private/tmp/bearplans-ux-docs-stage/check_docs.py
git diff --check -- AGENTS.md docs/PROGRESS.md
git diff -- AGENTS.md
```

Results:

- Bundled validator: **Skill is valid!**
- YAML frontmatter and UI metadata parse; skill name, normal automatic discovery,
  short-description length and `$bearplans-design` invocation example pass.
- All **36 ordered ticket definitions** match the shared register. UX-01–04 are
  Done for documentation; every remaining ticket is Not started.
- All local Markdown links in the new/changed documents and skill resolve;
  no stale hardcoded checkout paths or unfinished scaffold markers are present.
- Markdown text has final newlines, balanced fences and no trailing whitespace.
- Existing AGENTS.md content is exactly preserved outside the new design section
  and the explicit current-versus-future same-day-drop clarification.
- The previous progress record is preserved intact after the new current entry.
- Baseline hashes confirm all other existing tracked/untracked files and the Git
  index/HEAD are unchanged. Scoped diff checks pass. Existing unrelated staged
  review-plan formatting/content remains untouched.

The temporary checker and baseline live under
`/private/tmp/bearplans-ux-docs-stage/`; their absence in a later environment does
not prevent reading the durable plan, skill, register or this review.

## Independent review and semantic dry runs

Independent content review found no actionable issue: confirmed choices, all
36 tickets, domain protections, portable guidance, one writer and the docs-only
execution boundary are preserved.

An independent agent used the staged skill, brief and review reference against
five raw scenarios, without Figma or application mutations:

| Scenario | Observed result |
| --- | --- |
| Save the plan and guidance without opening Figma | Applies the skill to documentation; validates files and leaves UX-05 onwards unstarted. |
| Resume Week with missing ledger IDs and existing user/matching frames | Inspects/reconciles identities before writes; does not recreate by guess or alter user-owned Notes. |
| Recovery frame shows seven saved minutes from 120 trusted seconds plus a 300-second gap and automatic resume | Rejects the frame; only two minutes are confirmed and an explicit recovery decision is required. |
| Done task has two archived October planned dates but a November completion date; another task was never planned; parent has two complete children | Uses Oct 26–Nov 1 once for the first task, No planned week for the second, and child-only counting with parent context. |
| Fix launcher Python path detection | Does not route ordinary app debugging into the design skill. |

No skill defect was found in these dry runs. They verify guidance interpretation,
not Figma integration, rendered design, keyboard behavior, drag performance or
real persistence. No new scripts, fixtures or test dependencies were added to the
application repository for these semantic checks.

## Next permitted step and limits

Documentation request is complete. No ticket is active. When Figma work is
requested, begin UX-05 with live workspace/file/library discovery and the
installed Figma workflow skills. Do not infer authorization from this handoff.
Future visual/user checkpoints, implementation verification and existing Mac,
trial and M5 acceptance requirements remain separate.
