# Local assistant development preview

The first M5 ticket added read-only questions about day/week plans, task search,
task details and exact saved-time totals. The second adds **proposed changes**:
create/edit/plan/complete a task and start/pause/finish a countdown. A router
model classifies each request; BearPlans then checks that every needed detail
was actually stated and matches exactly one record. If something is missing or
several tasks match, it asks a question or shows choice buttons and keeps the
request waiting (**Start over** clears it). Only then does a proposal card
appear, showing every field it will set; nothing is saved until you choose **Apply**.
Ask for one change at a time. Day words such as “Tuesday”, “next Friday” or
“November 12” are converted by BearPlans, not the model; check the weekday on
the card. Numeric dates like 11/12 are ambiguous and will be asked.
Task and plan changes show **Undo** while the record is unchanged since; timer
changes are controlled in Track afterward. Larger replans and the full 30-case
write-acceptance gate remain later tickets. Each question is
independent; selected project/week IDs provide context. Conversation text is not
written to the database or browser storage.

## Keep the trial copy separate

Use `/Users/hiberkeley/Desktop/BearPlans-core-trial-2026-11-01` for the seven-day
core trial. It preserves the tested source, built interface and its own Python
environment, verified against all 141 candidate hashes. It contains no personal
data and is a local code snapshot, not another Git repository or an installation
portable to a different Mac. See the [updated trial guide](CORE_TRIAL_CHECKLIST.md).

The original Projects repository is the development copy with Assistant. Use
separate preview data below; do not point it at the normal trial database. The
existing instance guard rejects mixed builds sharing one active data folder.

## Open the preview

Open Terminal (Command+Space → Terminal → Return). In a new tab, run:

```sh
cd "/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan"
```

Create a preview folder once:

```sh
mkdir "$HOME/Desktop/BearPlans-assistant-preview"
```

If it already exists, keep it; it may contain earlier preview work. Launch using
that folder, with a different port from the trial:

```sh
BEARPLANS_DATA_DIR="$HOME/Desktop/BearPlans-assistant-preview" BEARPLANS_TIMEZONE=America/Los_Angeles python3 launch.py --port 8878
```

Check `data: /Users/hiberkeley/Desktop/BearPlans-assistant-preview` and
`open: http://127.0.0.1:8878/`. Keep this Terminal tab open. Create a sample task
in Plan if you want to ask about it, then click **Assistant** in the top navigation.

Ollama must be open on this Mac. The authorized setup downloaded **qwen3:4b** and
**qwen3:8b** for comparison on November 1. Click **Refresh models**, select a local
tools-capable model, enter a question, then **Ask**. Installed Gemma 3 models do
not advertise tools and are rejected for this assistant. Example questions:

- What is planned for today?
- Show this week's plan.
- Find tasks titled Reading and distinguish their projects.
- Check the incomplete subtasks. (Lists across all projects unless you name one.)
- How much saved active time do I have in total?
- Plan Essay for Tuesday. · Start Math 55 for 45 minutes. · Reopen Reading in History.

Each answer shows **Saved records used**, calculated by BearPlans domain functions.
Those source cards retain exact saved totals and service-local dates independently
of the model's prose. Frozen plans use their closed snapshot; task detail/search
use current task records. Search/plan limits are explicitly labeled. Check the
source cards when model wording is unclear. A reply with no sources explicitly
says that no saved records were read.

**Cancel question** aborts the browser request; the service cancels inference and
releases its assistant slot. Switching screens also cancels a pending question.
Plan, Track and Stats remain usable during generation. If Ollama is absent, a
model lacks tools, an answer is incomplete or inference times out, the input is
kept with a useful error. Refresh/retry explicitly. There is one assistant request
slot, five model rounds, ten lookups, a 120-second request deadline, bounded context
and response sizes; the HTTP transport is pinned to `127.0.0.1:11434`, without
environment proxies or redirects. It never pulls models automatically.

The assistant has no SQL execution, shell, filesystem or external provider
access, and its change tools never write by themselves. Each proposal names exact
task IDs and the revisions it was based on; if the task or countdown changed
before you apply it, BearPlans refuses with a message and changes nothing.
Applying twice (for example after a lost response) never repeats the change.
It cannot delete tasks, close weeks, buy trees, mint rewards or apply corrections.
If several tasks share a name, it asks which one you mean. Notes and task
titles are treated as untrusted records. The model only receives bounded records
returned by requested lookups; local questions still contain private content, so
choose locally stored weights. Remote/cloud model configurations are rejected.

To stop the preview, return to its Terminal tab, press Control+C once, and wait
for `BearPlans stopped.`. The trial copy and normal database remain separate.

## Protocol references

The adapter uses Ollama's documented [local chat/tool messages](https://docs.ollama.com/api/chat)
and [tool calling protocol](https://docs.ollama.com/capabilities/tool-calling).
Qwen documents the [/no_think soft control](https://qwenlm.github.io/blog/qwen3/).
The adapter explicitly disables thinking for thinking-capable models (Ollama
`think: false`; omitting it lets qwen3 think), discards any reasoning field and
rejects token-limited partial answers rather than displaying them as completed
replies. Models stay loaded for 15 minutes between questions.
Model quality and latency results belong in the implementation review; this
preview alone does not certify all of M5 or a production release.

Questions are now routed: common, fully specified lookups (today's or this
week's plan, all-time saved time, tasks/subtasks by status, tasks titled X,
upcoming deadlines) are answered directly by BearPlans in under a second, with
no model; anything else goes to a plan, tasks or time specialist (about 4–9
seconds). The footer shows the path, for example `router → direct` or
`router → time_specialist`.

After the November 1 speed fixes (thinking off, project names in lookups,
actionable lookup errors), qwen3:8b answered six synthetic questions twice each
in **6.3–10.7 seconds**, 12/12 with correct lookups; change requests take about
1 second. See the [actions review](reviews/2026-11-01-assistant-actions.md).

Earlier comparison (with thinking on) recommended **Qwen3 8B** for the preview: nine of ten final
retrieval cases completed with exact sources; one completion-count question hit
the output limit and returned an error. Use Stats directly if that happens.
Successful final comparison responses took 25.483 seconds at the median and
35.259 seconds at the slowest; these are small-sample observations. The 4B model
completed fewer cases. See the [implementation review](reviews/2026-11-01-local-assistant-readonly.md)
for retained failures and the remaining M5 gates.
