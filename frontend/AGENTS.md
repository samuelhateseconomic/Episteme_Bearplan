# BearPlans frontend guidance

Applies throughout `frontend/`. Read and retain the shared rules in
[root AGENTS.md](../AGENTS.md); this guide adds frontend navigation and workflow
routing without replacing the product, architecture or data-safety rules there.
Explicit user instructions and current authorization remain authoritative.

## Start with the current checkout

- Read [shared progress](../docs/PROGRESS.md), inspect Git status, recent commits,
  the full relevant diff and untracked files before changing work in progress.
- Resolve the repository root from Git. Do not reuse the removed nested project
  folder or assume another agent's commit/test report describes the current tree.
- Read [package.json](package.json) before choosing commands or dependencies.
  Extend the existing React/TypeScript/Vite application and its tests.

## Find the relevant material

| Area | Entry point |
| --- | --- |
| Frontend plans | [Plan index](plans/README.md) |
| Settings / Connections | [Feature entry point](plans/settings-connections/README.md) |
| Existing UX brief | [UX plan](BEARPLANS_UX_PLAN.md) |
| Existing design handoff | [UX handoff](BEARPLANS_UX_HANDOFF.md) |
| Figma inventory and evidence | [Prototype index](FIGMA_PROTOTYPE.md), `design/` |
| App shell, views and styling | `src/App.tsx`, `src/`, `src/styles.css` |
| API client and interface tests | `src/api.ts`, colocated `src/*.test.tsx` |
| Service/domain and browser tests | `../backend/`, `../tests/` |

`docs/PROGRESS.md` is the only mutable work/handoff tracker;
[COMPLETED](../docs/COMPLETED.md) is the append-only finished-work log. Plans define
requirements and tickets; reviews and the Figma ledger hold evidence, not another
current-status register. Do not move historical evidence merely to tidy folders.

## Select the workflow

For Settings / bCourses / Google connection work, select the matching skill:

- Planning, Figma construction or design review:
  [bearplans-connections-design](.agents/skills/bearplans-connections-design/SKILL.md).
- Separately authorized application implementation or runtime review:
  [bearplans-connections-build](.agents/skills/bearplans-connections-build/SKILL.md).

These skills live here at the user's requested location. The links make them
reachable from this guide; do not claim the host skill catalog has already been
updated. Load the relevant skill, not both for every frontend task. For other
BearPlans design work use the existing
[BearPlans design skill](../.agents/skills/bearplans-design/SKILL.md).
Ordinary unrelated frontend work does not need either connection skill.

Saving a plan or guide does not authorize Figma edits, application builds,
provider requests or changes to saved user data. Follow the user's actual scope.
Keep one delivery ticket active; serialize Figma writes with one writer. Preserve
concurrent work and existing capabilities absent from an older prototype.

## Commands

Run these from the repository root; use the accepted Node versions in
[package.json](package.json) and the existing lockfile.

```sh
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run dev
```

Use checks appropriate to the change and the root guidance. Documentation-only
work needs content/link/diff checks, not unrelated app test reruns. Interface
changes need meaningful behavior, width/theme, keyboard and failure-state checks.
Backend/schema/provider changes also require their applicable root checks.

Before stopping, update shared progress/completed records with actual checks,
limitations and the next concrete step. Do not infer a commit or push request
from a documentation or handoff task.
