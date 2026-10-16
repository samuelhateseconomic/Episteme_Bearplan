import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { type CarryoverOptions, type ClosedWeek, type HistoricalTask, type Placement, type Planning, type Task } from "./api";
import { WeekActions } from "./WeekActions";
import { TaskPlanning, WeeklyPlanner, type usePlanning } from "./WeeklyPlanner";

const at = "2026-10-18T21:00:00.000000Z";
function task(id = "leaf", over: Partial<Task> = {}): Task {
  return { id, project_id: "project", parent_id: null, title: "Read chapter", notes: "Original notes", deadline: "2026-10-25", estimate_minutes: 30, completed: false, completed_at: null, subtask_count: 0, completed_subtask_count: 0, created_at: at, updated_at: at, revision: 1, ...over };
}
function placement(id = "p1", taskId = "leaf", day = "2026-10-15"): Placement {
  return { id, task_id: taskId, planned_date: day, created_at: at, updated_at: at, revision: 1 };
}
function historical(over: Partial<HistoricalTask> = {}): HistoricalTask {
  return { ...task(), project_name: "Original project", parent_title: "Original parent", ...over };
}
function snapshot(over: Partial<ClosedWeek> = {}): ClosedWeek {
  return { snapshot_version: 1, week_start: "2026-10-12", week_end: "2026-10-18", closed_at: at, timezone: "America/Los_Angeles", tasks: [historical()], placements: [placement()], completed: 0, total: 1, ...over };
}
function planning(over: Partial<Planning> = {}): Planning {
  return { today: "2026-10-15", timezone: "America/Los_Angeles", week_start: "2026-10-12", week_end: "2026-10-18", tasks: [task()], placements: [placement()], ...over };
}
function options(over: Partial<CarryoverOptions> = {}): CarryoverOptions {
  return { week_start: "2026-10-12", destination_start: "2026-10-19", destination_end: "2026-10-25", candidates: [{ task_id: "leaf", snapshot_task: historical(), task: task(), eligible: true, reason: null, existing_planned_date: null }], ...over };
}
function json(body: unknown, status = 200) { return new Response(JSON.stringify(body), { status }); }
const run = async (work: () => Promise<unknown>) => { await work(); };
function boardState(plan: Planning): ReturnType<typeof usePlanning> {
  return { plan, selectedDay: "2026-10-15", loading: false, error: null, setSelectedDay: vi.fn(), refresh: vi.fn(), navigate: vi.fn() };
}

test("End Week previews frozen task details and counts before any close write", async () => {
  const calls: { url: string; init?: RequestInit }[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (url, init) => {
    calls.push({ url: String(url), init });
    return String(url).endsWith("close-preview") ? json({ preview_token: "reviewed", snapshot: snapshot({ closed_at: null }) }) : json(snapshot());
  });
  const user = userEvent.setup();
  render(<WeekActions plan={planning()} onRun={run} locked={false} />);
  expect(screen.queryByRole("button", { name: "Close week" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "End Week" }));
  const preview = within(await screen.findByRole("region", { name: "End week preview" }));
  expect(preview.getByText("Original project / Original parent")).toBeInTheDocument();
  expect(preview.getByText("Original notes")).toBeInTheDocument();
  expect(preview.getByText("Due Oct 25, 2026")).toBeInTheDocument();
  expect(preview.getByText("0 of 1 work items complete (0%).")).toBeInTheDocument();
  expect(calls.filter((call) => call.init?.method === "POST")).toHaveLength(0);
  await user.click(preview.getByRole("button", { name: "Close week" }));
  await waitFor(() => expect(calls.filter((call) => call.init?.method === "POST")).toHaveLength(1));
  expect(JSON.parse(String(calls.at(-1)?.init?.body))).toEqual({ preview_token: "reviewed" });
});

test("an empty week previews zero percent and may be cancelled without writing", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ preview_token: "empty", snapshot: snapshot({ tasks: [], placements: [], total: 0, completed: 0, closed_at: null }) }));
  const user = userEvent.setup();
  render(<WeekActions plan={planning()} onRun={run} locked={false} />);
  await user.click(screen.getByRole("button", { name: "End Week" }));
  expect(await screen.findByText("0 of 0 work items complete (0%).")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: /^Cancel$/ }));
  expect(screen.queryByRole("region", { name: "End week preview" })).not.toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(1);
});

test("a failed or stale close keeps the preview and exposes refresh for another review", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => String(url).endsWith("close-preview") ? json({ preview_token: "old", snapshot: snapshot() }) : json({ error: { message: "The week changed. Review again before closing." } }, 409));
  const user = userEvent.setup();
  render(<WeekActions plan={planning()} onRun={run} locked={false} />);
  await user.click(screen.getByRole("button", { name: "End Week" }));
  await user.click(await screen.findByRole("button", { name: "Close week" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("The week changed");
  expect(screen.getByRole("region", { name: "End week preview" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Refresh end-week preview" })).toBeEnabled();
});

test("the closed board uses frozen details with separate current status and no scheduling controls", () => {
  const frozen = snapshot();
  const plan = planning({ closed_week: frozen, placements: [], tasks: [task("leaf", { title: "Changed later", notes: "New notes", completed: true, deadline: "2026-11-30" })] });
  render(<WeeklyPlanner state={boardState(plan)} projects={[]} onRun={run} locked={false} onTrack={vi.fn()} />);
  expect(screen.getByText("Closed week · read-only history")).toBeInTheDocument();
  expect(screen.getByText("Read chapter")).toBeInTheDocument();
  expect(screen.getByText("Original notes")).toBeInTheDocument();
  expect(screen.getByText("Original project / Original parent")).toBeInTheDocument();
  expect(screen.getByText("Due Oct 25, 2026")).toBeInTheDocument();
  expect(screen.getByText("At closure: Unfinished")).toBeInTheDocument();
  expect(screen.queryByText("Planned Oct 15, 2026")).not.toBeInTheDocument();
  expect(screen.getByText("Current task: Complete")).toBeInTheDocument();
  expect(screen.queryByText("Changed later")).not.toBeInTheDocument();
  expect(screen.queryByText("New notes")).not.toBeInTheDocument();
  expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  expect(screen.queryByText("Move or remove")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "End Week" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Start tracking" })).not.toBeInTheDocument();
});

test("a completed weekly card disables tracking without extra explanation", () => {
  const onTrack = vi.fn();
  render(<WeeklyPlanner state={boardState(planning({ tasks: [task("leaf", { completed: true })] }))} projects={[]} onRun={run} locked={false} onTrack={onTrack} />);
  const start = screen.getByRole("button", { name: "Start tracking" });
  expect(start).toBeDisabled();
  expect(screen.queryByText("Reopen this task to start a new session. An existing session continues.")).not.toBeInTheDocument();
  fireEvent.click(start);
  expect(onTrack).not.toHaveBeenCalled();
});

test("closed history navigates to the selected snapshot and an open board counts unique leaves once", async () => {
  const state = boardState(planning({ tasks: [task("leaf", { completed: true }), task("parent", { subtask_count: 2 })], placements: [placement(), placement("p2", "leaf", "2026-10-16"), placement("p3", "parent")], closed_weeks: [{ week_start: "2026-10-05", week_end: "2026-10-11", closed_at: at, completed: 0, total: 0 }] }));
  render(<WeeklyPlanner state={state} projects={[]} onRun={run} locked={false} />);
  expect(screen.getByText("Weekly completion: 1 of 1 work items complete (100%).")).toBeInTheDocument();
  await userEvent.setup().selectOptions(screen.getByLabelText("Closed-week history"), "2026-10-05");
  expect(state.navigate).toHaveBeenCalledWith("2026-10-05");
});

test("closed-week task planning does not offer an assignment into history", () => {
  render(<TaskPlanning task={task()} plan={planning({ closed_week: snapshot(), placements: [] })} selectedDay="2026-10-15" onRun={run} />);
  expect(screen.getByText("Viewing a closed week. Choose an open week to plan this task.")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Add to day" })).not.toBeInTheDocument();
});

test("carryover explains completed/conflicting tasks and requires reviewing selected destination dates", async () => {
  const calls: { url: string; body: Record<string, unknown> | null }[] = [];
  const candidates = options().candidates;
  candidates.push({ task_id: "done", snapshot_task: historical({ id: "done", title: "Done now" }), task: task("done", { title: "Done now", completed: true }), eligible: false, reason: "This task is currently complete.", existing_planned_date: null });
  candidates.push({ task_id: "conflict", snapshot_task: historical({ id: "conflict", title: "Already planned" }), task: task("conflict", { title: "Already planned" }), eligible: false, reason: "This task already has an active plan.", existing_planned_date: "2026-10-21" });
  vi.spyOn(globalThis, "fetch").mockImplementation(async (url, init) => {
    const path = String(url);
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    calls.push({ url: path, body });
    if (path.endsWith("carryover-preview")) return json({ preview_token: "carry", week_start: "2026-10-12", destination_start: "2026-10-19", destination_end: "2026-10-25", items: [{ ...body.selections[0], task: task(), project_name: "Original project", parent_title: "Original parent" }] });
    return json(options({ candidates }));
  });
  const user = userEvent.setup();
  render(<WeekActions plan={planning({ closed_week: snapshot() })} onRun={run} locked={false} />);
  await user.click(screen.getByRole("button", { name: "Carry unfinished work" }));
  expect(await screen.findByRole("checkbox", { name: "Done now" })).toBeDisabled();
  expect(screen.getByRole("checkbox", { name: "Already planned" })).toBeDisabled();
  expect(screen.getByText(/Existing plan: Oct 21, 2026/)).toBeInTheDocument();
  await user.click(screen.getByRole("checkbox", { name: "Read chapter" }));
  const date = screen.getByLabelText("Carry “Read chapter” to");
  expect(date).toHaveAttribute("min", "2026-10-19");
  expect(date).toHaveAttribute("max", "2026-10-25");
  fireEvent.change(date, { target: { value: "2026-10-26" } });
  expect(screen.getByRole("button", { name: "Review carryover" })).toBeDisabled();
  fireEvent.change(date, { target: { value: "2026-10-23" } });
  expect(screen.queryByRole("button", { name: "Apply carryover" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Review carryover" }));
  const preview = within(await screen.findByRole("region", { name: "Carryover preview" }));
  expect(preview.getByText("Planned Oct 23, 2026")).toBeInTheDocument();
  expect(preview.getByText("Original notes")).toBeInTheDocument();
  expect(calls.at(-1)?.body).toEqual({ selections: [{ task_id: "leaf", planned_date: "2026-10-23" }] });
  fireEvent.change(date, { target: { value: "2026-10-22" } });
  expect(screen.queryByRole("region", { name: "Carryover preview" })).not.toBeInTheDocument();
});

test("failed carryover retains selections and retry reuses the reviewed operation identity", async () => {
  const applied: Record<string, unknown>[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (url, init) => {
    const path = String(url);
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    if (path.endsWith("carryover-preview")) return json({ preview_token: "carry", week_start: "2026-10-12", destination_start: "2026-10-19", destination_end: "2026-10-25", items: [{ ...body.selections[0], task: task(), project_name: "Original project", parent_title: null }] });
    if (init?.method === "POST") {
      applied.push(body);
      if (applied.length === 1) throw new TypeError("connection lost after write");
      return json({ operation_id: body.operation_id, week_start: "2026-10-12", placements: [placement("carried", "leaf", "2026-10-19")] });
    }
    return json(options());
  });
  const user = userEvent.setup();
  render(<WeekActions plan={planning({ closed_week: snapshot() })} onRun={run} locked={false} />);
  await user.click(screen.getByRole("button", { name: "Carry unfinished work" }));
  await user.click(await screen.findByRole("checkbox", { name: "Read chapter" }));
  await user.click(screen.getByRole("button", { name: "Review carryover" }));
  await user.click(await screen.findByRole("button", { name: "Apply carryover" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Your selections are kept");
  expect(screen.getByLabelText("Carry “Read chapter” to")).toHaveValue("2026-10-19");
  await user.click(screen.getByRole("button", { name: "Apply carryover" }));
  await waitFor(() => expect(applied).toHaveLength(2));
  expect(applied[0]).toEqual(applied[1]);
  expect(applied[0].operation_id).toMatch(/^[\da-f-]{36}$/i);
  expect(await screen.findByRole("status")).toHaveTextContent("Carried over 1 work item");
});
