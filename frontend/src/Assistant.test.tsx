import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { Assistant } from "./Assistant";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const status = { available: true, read_only: true, prompt_version: "readonly-v1", models: [{ name: "qwen3:4b", digest: "fixture", details: {} }] };
const summary = { tool: "get_time_summary", arguments: {}, data: { active_microseconds: 60000001, session_count: 1, timezone: "America/Los_Angeles",
  completion: { completed: 1, total: 3 }, days: [{ date: "2026-11-01", active_microseconds: 60000001 }], days_truncated: false } };
const reply = { answer: "A model reply.", model: "qwen3:4b", elapsed_seconds: 1.2, rounds: 2, read_only: true, sources: [summary] };

test("does not contact Ollama when hidden; shows actionable unavailable state and retries", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json({ error: { message: "Open Ollama, then refresh models." } }, 503)).mockResolvedValue(json(status));
  const view = render(<Assistant visible={false} projectId={null} />);
  expect(fetcher).not.toHaveBeenCalled();
  view.rerender(<Assistant visible projectId={null} />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Open Ollama");
  expect(screen.getByRole("button", { name: "Ask" })).toBeDisabled();
  await userEvent.click(screen.getByRole("button", { name: "Refresh models" }));
  expect(await screen.findByRole("option", { name: "qwen3:4b" })).toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("keyboard submission carries context and renders exact source values independently of model wording", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status)).mockResolvedValue(json(reply));
  const user = userEvent.setup();
  render(<Assistant visible projectId="project" date="2026-10-26" />);
  await screen.findByRole("option", { name: "qwen3:4b" });
  await user.type(screen.getByRole("textbox", { name: "Question" }), "How much saved time?");
  screen.getByRole("button", { name: "Ask" }).focus();
  await user.keyboard("{Enter}");
  expect(await screen.findByText("A model reply.")).toBeVisible();
  expect(screen.getByText("All-time saved active time: 1 min 0.000001 s")).toBeVisible();
  expect(screen.getByText("Current leaf completion: 1 of 3")).toBeVisible();
  const body = JSON.parse((fetcher.mock.calls[1][1] as RequestInit).body as string);
  expect(body.context).toEqual({ project_id: "project", date: "2026-10-26" });
  expect(body.prompt).toBe("How much saved time?");
});

test("cancel aborts inference and ignores late reply while preserving question", async () => {
  let resolve!: (value: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status)).mockImplementationOnce(() => new Promise((done) => { resolve = done; }));
  const user = userEvent.setup();
  render(<Assistant visible projectId={null} />);
  await screen.findByRole("option", { name: "qwen3:4b" });
  await user.type(screen.getByRole("textbox", { name: "Question" }), "Today's plan?");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  expect(screen.getByRole("button", { name: "Looking up…" })).toBeDisabled();
  const signal = (fetcher.mock.calls[1][1] as RequestInit).signal;
  await user.click(screen.getByRole("button", { name: "Cancel question" }));
  expect(signal?.aborted).toBe(true);
  await act(async () => resolve(json(reply)));
  expect(screen.queryByText("A model reply.")).not.toBeInTheDocument();
  expect(screen.getByRole("textbox")).toHaveValue("Today's plan?");
  expect(screen.getByRole("button", { name: "Ask" })).toBeEnabled();
});

test("navigation cancels outstanding request and discards old results on reentry", async () => {
  let resolve!: (value: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status))
    .mockImplementationOnce(() => new Promise((done) => { resolve = done; })).mockResolvedValue(json(status));
  const user = userEvent.setup();
  const view = render(<Assistant visible projectId={null} />);
  await screen.findByRole("option", { name: "qwen3:4b" });
  await user.type(screen.getByRole("textbox"), "Question");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  view.rerender(<Assistant visible={false} projectId={null} />);
  expect((fetcher.mock.calls[1][1] as RequestInit).signal?.aborted).toBe(true);
  view.rerender(<Assistant visible projectId="next" />);
  await act(async () => resolve(json(reply)));
  expect(screen.queryByText("A model reply.")).not.toBeInTheDocument();
  expect(screen.getByRole("textbox")).toHaveValue("Question");
});

test("failed answer retains input and supports explicit retry; no sources are invented", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status))
    .mockResolvedValueOnce(json({ error: { message: "Choose a tools-capable model." } }, 422))
    .mockResolvedValueOnce(json({ ...reply, sources: [], answer: "Use Plan to edit tasks." }));
  const user = userEvent.setup();
  render(<Assistant visible projectId={null} />);
  await screen.findByRole("option", { name: "qwen3:4b" });
  await user.type(screen.getByRole("textbox"), "Change this task");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Choose a tools-capable model");
  expect(screen.getByRole("textbox")).toHaveValue("Change this task");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  expect(await screen.findByText("No saved records were read for this reply.")).toBeVisible();
});

test("task sources render plain untrusted text, preserve dates and explain truncation/history", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status)).mockResolvedValueOnce(json({ ...reply, sources: [{
    tool: "get_week_plan", arguments: {}, data: { historical: true, start_date: "2026-10-19", end_date: "2026-10-25", timezone: "America/Los_Angeles",
      unique_leaf_total: 1, completed_leaf_total: 0, truncated: true, items: [{ task_id: "task", title: "<script>bad()</script>", project_name: "Math", deadline: "2026-11-20", planned_date: "2026-10-20", completed: false }] },
  }] }));
  const user = userEvent.setup();
  const view = render(<Assistant visible projectId={null} />);
  await screen.findByRole("option", { name: "qwen3:4b" });
  await user.type(screen.getByRole("textbox"), "Past plan");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  expect(await screen.findByText("<script>bad()</script>")).toBeVisible();
  expect(view.container.querySelector("script")).toBeNull();
  expect(screen.getByText(/Frozen history/)).toBeVisible();
  expect(screen.getByText(/Due 2026-11-20/)).toBeVisible();
  expect(screen.getByText(/More records exist/)).toBeVisible();
});

const proposal = { kind: "complete_task", arguments: { task_id: "t1", complete: true }, summary: 'Mark "Essay" complete', undoable: true,
  expected: { tasks: { t1: 3 }, session_id: null, session_revision: null }, preview: {} };
const proposing = { ...reply, sources: [], proposals: [proposal] };

async function ask(user: ReturnType<typeof userEvent.setup>) {
  await screen.findByRole("option", { name: "qwen3:4b" });
  await user.type(screen.getByRole("textbox", { name: "Question" }), "Complete Essay");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  return await screen.findByRole("article", { name: 'Proposed change: Mark "Essay" complete' });
}

test("proposals save nothing until Apply; a failed apply retries with the same key, then Undo refreshes", async () => {
  const applied = { operation_id: "op", kind: "complete_task", summary: 'Mark "Essay" complete', applied_at: "x", undoable: true, replayed: false };
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status)).mockResolvedValueOnce(json(proposing))
    .mockRejectedValueOnce(new TypeError("network")).mockResolvedValueOnce(json(applied)).mockResolvedValueOnce(json({ operation_id: "u", action_operation_id: "op", undone_at: "y", summary: "Undid", replayed: false }));
  const changed = vi.fn();
  const user = userEvent.setup();
  render(<Assistant visible projectId={null} onChanged={changed} />);
  const card = await ask(user);
  expect(card).toHaveTextContent("Not applied");
  expect(fetcher).toHaveBeenCalledTimes(2);
  await user.click(screen.getByRole("button", { name: "Apply" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("never applied twice");
  expect(changed).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: "Apply" }));
  expect(await screen.findByText("Applied.")).toBeVisible();
  const first = JSON.parse((fetcher.mock.calls[2][1] as RequestInit).body as string);
  const second = JSON.parse((fetcher.mock.calls[3][1] as RequestInit).body as string);
  expect(second.operation_id).toBe(first.operation_id);
  expect(second.proposal.expected).toEqual({ tasks: { t1: 3 }, session_id: null, session_revision: null });
  expect(changed).toHaveBeenCalledTimes(1);
  await user.click(screen.getByRole("button", { name: "Undo" }));
  expect(await screen.findByText(/Undone/)).toBeVisible();
  expect(fetcher.mock.calls[4][0]).toBe("/api/assistant/actions/op/undo");
  expect(changed).toHaveBeenCalledTimes(2);
});

test("stale proposal conflict stays visible; dismiss sends nothing", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status)).mockResolvedValueOnce(json(proposing))
    .mockResolvedValueOnce(json({ error: { code: "assistant_action_conflict", message: '"Essay" changed after this proposal was prepared.' } }, 409));
  const user = userEvent.setup();
  render(<Assistant visible projectId={null} />);
  await ask(user);
  await user.click(screen.getByRole("button", { name: "Apply" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("changed after this proposal");
  expect(screen.getByText("A model reply.")).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Dismiss" }));
  expect(screen.getByText("Dismissed. Nothing was changed.")).toBeVisible();
  expect(fetcher).toHaveBeenCalledTimes(3);
});

test("gate questions keep the request pending; a choice continues it without retyping, then Start over clears it", async () => {
  const pending = { intent: "complete_task", slots: { task: "Reading" }, round: 1 };
  const clarify = { ...reply, sources: [], kind: "clarify", answer: "Several tasks match “Reading”. Which one do you mean?",
    route: { intent: "complete_task", agents: ["router", "action_library", "gate"] },
    clarification: { questions: ["Several tasks match “Reading”. Which one do you mean?"], pending,
      choices: { task_id: [{ value: "a", label: "Reading — Writing (incomplete)" }, { value: "b", label: "Reading — History (incomplete)" }] } } };
  const ready = { ...proposing, kind: "proposal", clarification: null, route: { intent: "complete_task", agents: ["action_library", "gate"] } };
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status)).mockResolvedValueOnce(json(clarify))
    .mockResolvedValueOnce(json(ready)).mockResolvedValueOnce(json(clarify));
  const user = userEvent.setup();
  render(<Assistant visible projectId={null} />);
  await screen.findByRole("option", { name: "qwen3:4b" });
  await user.type(screen.getByRole("textbox", { name: "Question" }), "Complete Reading");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  expect(await screen.findByRole("heading", { name: "Details needed" })).toBeVisible();
  expect(screen.queryByRole("button", { name: "Apply" })).not.toBeInTheDocument();
  expect(screen.getByText(/A change is waiting for details/)).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Reading — History (incomplete)" }));
  expect(await screen.findByRole("button", { name: "Apply" })).toBeVisible();
  const choiceBody = JSON.parse((fetcher.mock.calls[2][1] as RequestInit).body as string);
  expect(choiceBody).toMatchObject({ prompt: "", pending, choice: { slot: "task_id", value: "b" } });
  expect(screen.queryByText(/A change is waiting for details/)).not.toBeInTheDocument();

  await user.type(screen.getByRole("textbox", { name: "Question" }), "Complete Reading");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  await screen.findByRole("heading", { name: "Details needed" });
  await user.click(screen.getByRole("button", { name: "Start over" }));
  expect(screen.queryByText(/A change is waiting for details/)).not.toBeInTheDocument();
  expect(JSON.parse((fetcher.mock.calls[3][1] as RequestInit).body as string).pending).toBeUndefined();
});

test("a week carryover card lists each task's same-weekday date and unchanged deadline, and sends the review token", async () => {
  const carry = { kind: "carry_over_week", arguments: { week_start: "2026-10-12", selections: [{ task_id: "t1", planned_date: "2026-10-20" }] },
    summary: "Carry 1 unfinished task from the week of Mon 2026-10-12 to the same weekday next week", undoable: true,
    expected: { tasks: {}, session_id: null, session_revision: null, preview_token: "tok" },
    preview: { items: [{ task_id: "t1", title: "Proof", project_name: "Seminar", parent_title: "Assignment", planned_date: "2026-10-20", deadline: "2026-10-30" }] } };
  const applied = { operation_id: "op", kind: "carry_over_week", summary: carry.summary, applied_at: "x", undoable: true, replayed: false };
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(status))
    .mockResolvedValueOnce(json({ ...reply, sources: [], proposals: [carry] })).mockResolvedValueOnce(json(applied));
  const user = userEvent.setup();
  render(<Assistant visible projectId={null} />);
  await screen.findByRole("option", { name: "qwen3:4b" });
  await user.type(screen.getByRole("textbox", { name: "Question" }), "Move last week's unfinished to next week");
  await user.click(screen.getByRole("button", { name: "Ask" }));
  const card = within(await screen.findByRole("article", { name: `Proposed change: ${carry.summary}` }));
  const list = within(card.getByRole("list", { name: "Tasks to carry over" }));
  expect(list.getByText("Proof")).toBeVisible();
  expect(list.getByText("Seminar / Assignment")).toBeVisible();
  expect(list.getByText(/Tue, Oct 20.*due Fri, Oct 30 \(unchanged\)/)).toBeVisible();
  await user.click(card.getByRole("button", { name: "Apply" }));
  expect(await card.findByText("Applied.")).toBeVisible();
  expect(JSON.parse((fetcher.mock.calls[2][1] as RequestInit).body as string).proposal.expected.preview_token).toBe("tok");
});
