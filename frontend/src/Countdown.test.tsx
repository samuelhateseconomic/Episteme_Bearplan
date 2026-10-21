import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, vi } from "vitest";
import App from "./App";
import { formatRemaining, TrackScreen, useCountdown } from "./Countdown";
import type { Planning, Project, Task, TimerSession, TimerState } from "./api";

const NOW = "2026-10-16T16:00:00.000000Z";
const PROJECT = "00000000-0000-4000-8000-000000000001";
const LEAF = "00000000-0000-4000-8000-000000000002";
const PARENT = "00000000-0000-4000-8000-000000000003";
const project: Project = { id: PROJECT, name: "Seminar", is_default: true, created_at: NOW, updated_at: NOW, revision: 1 };
const task: Task = {
  id: LEAF, title: "Unscheduled reading", project_id: PROJECT, parent_id: null, notes: "Keep these notes", deadline: "2026-11-01", estimate_minutes: null,
  completed: false, completed_at: null, subtask_count: 0, completed_subtask_count: 0, created_at: NOW, updated_at: NOW, revision: 1,
};
const plan: Planning = { today: "2026-10-16", timezone: "America/Los_Angeles", week_start: "2026-10-12", week_end: "2026-10-18", placements: [], tasks: [task, { ...task, id: PARENT, title: "Container", subtask_count: 1 }] };

function session(over: Partial<TimerSession> = {}): TimerSession {
  return {
    id: "00000000-0000-4000-8000-000000000004", start_operation_id: "00000000-0000-4000-8000-000000000005", task_id: LEAF, task_title: task.title,
    project_id: PROJECT, project_name: project.name, parent_title: null, state: "running", duration_minutes: 1, requested_seconds: 60,
    active_seconds: 0, remaining_seconds: 60, started_at: NOW, checkpoint_at: NOW, deadline_at: "2026-10-16T16:01:00.000000Z", finished_at: null,
    outcome: null, review_reason: null, revision: 1, tree: null, ...over,
  };
}

const empty = (): TimerState => ({ server_now: NOW, active_session: null, last_session: null });
const running = (over: Partial<TimerSession> = {}): TimerState => ({ ...empty(), active_session: session(over) });
const interrupted = (): TimerState => running({
  state: "needs_review", active_seconds: 15, remaining_seconds: 45, deadline_at: null,
  review_reason: "The app restarted. The gap has not been counted.",
  recovery: {
    id: "00000000-0000-4000-8000-000000000010", kind: "service_restart", reason: "The app restarted. The gap has not been counted.",
    checkpoint_at: NOW, detected_at: "2026-10-16T16:05:00.000000Z", confirmed_active_seconds: 15,
    measured_sleep_seconds: null, resolved_at: null, resolution: null,
  },
});
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

interface Call { url: string; method: string; body: Record<string, unknown> }
function service(initial = empty(), initialPlan = plan) {
  const holder = { state: initial, plan: initialPlan };
  const calls: Call[] = [];
  const recoveries = new Map<string, string>();
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body = JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown>;
    calls.push({ url, method, body });
    if (url === "/api/timer" && method === "GET") return json(holder.state);
    if (url === "/api/forest" && method === "GET") return json({ trees: [] });
    if (url === "/api/timer/start") {
      if (holder.state.active_session) return json({ error: { message: "Another session is active. Open Track to use it." } }, 409);
      holder.state = running({ duration_minutes: Number(body.duration_minutes), requested_seconds: Number(body.duration_minutes) * 60, remaining_seconds: Number(body.duration_minutes) * 60, start_operation_id: String(body.operation_id) });
      return json(holder.state);
    }
    if (url.endsWith("/recover")) {
      const operation = String(body.operation_id);
      const fingerprint = JSON.stringify(body);
      if (recoveries.has(operation)) return recoveries.get(operation) === fingerprint
        ? json(holder.state) : json({ error: { field: "operation_id", message: "This request ID was already used." } }, 409);
      const active = holder.state.active_session;
      if (!active || active.state !== "needs_review" || active.revision !== body.expected_revision) return json({ error: { field: "revision", message: "The countdown changed in another tab. Review its current state and try again." } }, 409);
      const recovered = { ...active, recovery: active.recovery ? { ...active.recovery, resolved_at: NOW, resolution: body.resolution as "resume" | "finish" } : null, revision: active.revision + 1 };
      holder.state = body.resolution === "resume"
        ? { ...holder.state, active_session: { ...recovered, state: "running", deadline_at: "2026-10-16T16:00:45.000000Z", review_reason: null } }
        : { ...holder.state, active_session: null, last_session: { ...recovered, state: "finished", outcome: "interrupted", finished_at: NOW, deadline_at: null } };
      recoveries.set(operation, fingerprint);
      return json(holder.state);
    }
    const active = holder.state.active_session;
    if (url.endsWith("/pause") && active) {
      holder.state = { ...holder.state, active_session: { ...active, state: "paused", remaining_seconds: 45, active_seconds: 15, deadline_at: null, revision: active.revision + 1 } };
      return json(holder.state);
    }
    if (url.endsWith("/resume") && active) {
      holder.state = { ...holder.state, active_session: { ...active, state: "running", deadline_at: "2026-10-16T16:00:45.000000Z", recovery: active.recovery ? { ...active.recovery, resolved_at: NOW, resolution: "resume" } : null, revision: active.revision + 1 } };
      return json(holder.state);
    }
    if (url.endsWith("/finish") && active) {
      holder.state = { ...holder.state, active_session: null, last_session: { ...active, state: "finished", outcome: body.discard_uncertain ? "interrupted" : "finished_early", active_seconds: 15, finished_at: NOW, deadline_at: null, revision: active.revision + 1 } };
      return json(holder.state);
    }
    if (url === "/api/projects") return json({ projects: [project] });
    if (url.startsWith("/api/planning")) return json(holder.plan);
    if (url.endsWith("/completion") && method === "PUT") {
      const id = url.split("/")[3];
      holder.plan = { ...holder.plan, tasks: holder.plan.tasks.map((item) => item.id === id ? { ...item, completed: Boolean(body.complete), completed_at: body.complete ? NOW : null } : item) };
      return json(holder.plan.tasks.find((item) => item.id === id));
    }
    if (url.startsWith("/api/tasks")) return json({ tasks: holder.plan.tasks, progress: { completed: 0, total: 1 } });
    throw new Error(`Unexpected ${method} ${url}`);
  });
  return { holder, calls };
}

function Harness({ requestedTaskId = LEAF }: { requestedTaskId?: string }) {
  const timer = useCountdown();
  return <>
    {timer.error ? <p role="alert">{timer.error}<button onClick={timer.refresh}>Refresh timer</button></p> : null}
    <TrackScreen timer={timer} plan={plan} projects={[project]} requestedTaskId={requestedTaskId} visible />
  </>;
}

beforeEach(() => { window.history.replaceState(null, "", "/"); sessionStorage.clear(); });
afterEach(() => { window.history.replaceState(null, "", "/"); sessionStorage.clear(); vi.useRealTimers(); });

test("direct Track navigation selects unscheduled leaves and enforces whole minutes 1–180", async () => {
  const { calls } = service();
  window.history.replaceState(null, "", "/#track");
  const user = userEvent.setup();
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Track" })).toBeVisible();
  const choices = screen.getByLabelText("Task to track");
  expect(within(choices).queryByRole("option", { name: /Container/ })).not.toBeInTheDocument();
  await user.selectOptions(choices, LEAF);
  const duration = screen.getByLabelText("Duration (minutes)");
  for (const value of ["0", "181", "1.5", ""]) {
    fireEvent.change(duration, { target: { value } });
    expect(screen.getByRole("button", { name: "Start countdown" })).toBeDisabled();
  }
  fireEvent.change(duration, { target: { value: "180" } });
  await user.click(screen.getByRole("button", { name: "Start countdown" }));
  expect(await screen.findByRole("region", { name: "Current session" })).toHaveTextContent("180 minute countdown");
  expect(calls.find((call) => call.url === "/api/timer/start")?.body).toMatchObject({ task_id: LEAF, duration_minutes: 180, operation_id: expect.any(String) });
  expect(calls.some((call) => call.url.includes("/completion"))).toBe(false);
});

test("leaf Start tracking opens Track with that task and keeps the duration across navigation", async () => {
  service();
  const user = userEvent.setup();
  render(<App />);
  const start = await screen.findByRole("button", { name: "Start tracking" });
  expect(screen.getAllByRole("button", { name: "Start tracking" })).toHaveLength(1);
  await user.click(start);
  expect(screen.getByLabelText("Task to track")).toHaveValue(LEAF);
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), { target: { value: "12" } });
  await user.click(screen.getByRole("link", { name: "Plan" }));
  await user.click(screen.getByRole("link", { name: "Track" }));
  expect(screen.getByLabelText("Duration (minutes)")).toHaveValue(12);
});

test("new-session choices include scheduled and unscheduled incomplete leaves across projects", async () => {
  const scheduled = { ...task, id: "00000000-0000-4000-8000-000000000006", title: "Scheduled subtask", parent_id: PARENT };
  const otherProject = { ...task, id: "00000000-0000-4000-8000-000000000007", title: "Other project work", project_id: "another-project" };
  const completed = { ...task, id: "00000000-0000-4000-8000-000000000008", title: "Finished reading", completed: true };
  const completedChild = { ...completed, id: "00000000-0000-4000-8000-000000000009", title: "Finished subtask", parent_id: PARENT };
  service(empty(), { ...plan, tasks: [...plan.tasks, scheduled, otherProject, completed, completedChild], placements: [{ id: "placement", task_id: scheduled.id, planned_date: plan.today, created_at: NOW, updated_at: NOW, revision: 1 }] });
  window.history.replaceState(null, "", "/#track");
  render(<App />);
  const choices = await screen.findByLabelText("Task to track");
  await waitFor(() => expect(within(choices).getAllByRole("option")).toHaveLength(4));
  expect(within(choices).getByRole("option", { name: /Unscheduled reading/ })).toBeInTheDocument();
  expect(within(choices).getByRole("option", { name: /Container \/ Scheduled subtask/ })).toBeInTheDocument();
  expect(within(choices).getByRole("option", { name: /Other project work/ })).toBeInTheDocument();
  expect(within(choices).queryByRole("option", { name: /Finished/ })).not.toBeInTheDocument();
  expect(within(choices).queryByRole("option", { name: "Seminar / Container" })).not.toBeInTheDocument();
});

test("completed Plan leaves disable new-session entry without extra explanation", async () => {
  const { calls } = service(empty(), { ...plan, tasks: [{ ...task, completed: true }] });
  const user = userEvent.setup();
  render(<App />);
  const start = await screen.findByRole("button", { name: "Start tracking" });
  expect(start).toBeDisabled();
  expect(screen.queryByText("Reopen this task to start a new session. An existing session continues.")).not.toBeInTheDocument();
  await user.click(start);
  expect(calls.some((call) => call.url === "/api/timer/start")).toBe(false);
});

test("a weekly card opens Track by keyboard with the same task and existing duration flow", async () => {
  const { calls } = service(empty(), { ...plan, tasks: [task], placements: [{ id: "placement", task_id: LEAF, planned_date: plan.today, created_at: NOW, updated_at: NOW, revision: 1 }] });
  const user = userEvent.setup();
  render(<App />);
  await user.click(screen.getByRole("link", { name: "Track" }));
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), { target: { value: "9" } });
  await user.click(screen.getByRole("link", { name: "Plan" }));
  const friday = await screen.findByRole("region", { name: /Friday,/ });
  const start = within(friday).getByRole("button", { name: "Start tracking" });
  start.focus();
  await user.keyboard("{Enter}");
  expect(screen.getByLabelText("Task to track")).toHaveValue(LEAF);
  expect(screen.getByLabelText("Duration (minutes)")).toHaveValue(9);
  expect(screen.getByRole("heading", { name: "Track" })).toHaveFocus();
  expect(calls.some((call) => call.url === "/api/timer/start")).toBe(false);
  await user.click(screen.getByRole("button", { name: "Start countdown" }));
  expect(await screen.findByRole("region", { name: "Current session" })).toBeVisible();
  expect(calls.find((call) => call.url === "/api/timer/start")?.body).toMatchObject({ task_id: LEAF, duration_minutes: 9 });
});

test.each([{ label: "no tasks", tasks: [] }, { label: "all complete", tasks: [{ ...task, completed: true }] }])("Track explains how to get eligible work when no incomplete leaves exist: $label", async ({ tasks }) => {
  service(empty(), { ...plan, tasks });
  window.history.replaceState(null, "", "/#track");
  render(<App />);
  expect(await screen.findByText(/No incomplete tasks to track/)).toHaveTextContent("Add a task or reopen a completed task in Plan");
  expect(screen.getByLabelText("Task to track")).toBeDisabled();
  expect(screen.getByRole("button", { name: "Start countdown" })).toBeDisabled();
  expect(screen.getByLabelText("Duration (minutes)")).toBeEnabled();
});

test("a stale completed-task rejection refreshes choices and preserves duration", async () => {
  const { holder, calls } = service(empty(), { ...plan, tasks: [task] });
  const original = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input) === "/api/timer/start") {
      holder.plan = { ...holder.plan, tasks: [{ ...task, completed: true }] };
      return json({ error: { code: "invalid_input", field: "task_id", message: "This task is complete. Reopen it or choose an incomplete task." } }, 422);
    }
    return original(input, init);
  });
  window.history.replaceState(null, "", "/#track");
  const user = userEvent.setup();
  render(<App />);
  await waitFor(() => expect(screen.getByLabelText("Task to track")).toBeEnabled());
  await user.selectOptions(screen.getByLabelText("Task to track"), LEAF);
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), { target: { value: "17" } });
  await user.click(screen.getByRole("button", { name: "Start countdown" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("This task is complete. Reopen it or choose an incomplete task.");
  expect(await screen.findByText(/No incomplete tasks to track/)).toBeVisible();
  expect(screen.getByLabelText("Duration (minutes)")).toHaveValue(17);
  expect(within(screen.getByLabelText("Task to track")).queryByRole("option", { name: /Unscheduled reading/ })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Start countdown" })).toBeDisabled();
  expect(calls.filter((call) => call.url.startsWith("/api/planning"))).toHaveLength(2);
  expect(calls.some((call) => call.url.includes("/completion"))).toBe(false);
});

test.each(["running", "paused", "needs_review"] as const)("completing a task preserves its %s session and excludes it from later new-session choices", async (state) => {
  const active = running({ state, deadline_at: state === "running" ? "2026-10-16T16:01:00.000000Z" : null });
  const { holder, calls } = service(active, { ...plan, tasks: [task] });
  const user = userEvent.setup();
  render(<App />);
  const compact = await screen.findByRole("complementary", { name: "Active countdown" });
  await user.click(await screen.findByLabelText(task.title));
  await waitFor(() => expect(screen.getByRole("button", { name: "Start tracking" })).toBeDisabled());
  expect(holder.state).toEqual(active);
  expect(compact).toHaveTextContent(task.title);
  await user.click(within(compact).getByRole("button", { name: "Open Track" }));
  expect(screen.getByRole("region", { name: "Current session" })).toHaveTextContent(task.title);
  expect(screen.queryByLabelText("Task to track")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Start countdown" })).not.toBeInTheDocument();
  const finish = state === "needs_review" ? "Save confirmed time and finish" : "Finish early";
  await user.click(screen.getByRole("button", { name: finish }));
  expect(await screen.findByRole("region", { name: "Saved session outcome" })).toHaveTextContent(task.title);
  expect(screen.getByText(/No incomplete tasks to track/)).toBeVisible();
  expect(holder.plan.tasks[0].completed).toBe(true);
  expect(calls.filter((call) => call.url.includes("/completion"))).toHaveLength(1);
  expect(calls.filter((call) => call.url.endsWith(state === "needs_review" ? "/recover" : "/finish"))).toHaveLength(1);
  expect(calls.some((call) => call.url === "/api/timer/start")).toBe(false);
});

test("pause and resume use backend state and revisions; finish saves the outcome without completing the task", async () => {
  const { calls } = service(running());
  const user = userEvent.setup();
  render(<Harness />);
  await user.click(await screen.findByRole("button", { name: "Pause" }));
  expect(screen.getByRole("timer", { name: "Time remaining" })).toHaveTextContent("00:45");
  expect(screen.getByText(/paused time is excluded/)).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Resume" }));
  await user.click(screen.getByRole("button", { name: "Finish early" }));
  expect(await screen.findByRole("region", { name: "Saved session outcome" })).toHaveTextContent("Finished early · 00:15 active time");
  expect(calls.filter((call) => call.method === "POST").map((call) => call.body.expected_revision)).toEqual([1, 2, 3]);
  expect(calls.some((call) => call.url.startsWith("/api/tasks") && call.method !== "GET")).toBe(false);
  expect(task.completed).toBe(false);
});

test("starting from the same task again reselects it after a different Track choice", async () => {
  service();
  const second = { ...task, id: "00000000-0000-4000-8000-000000000006", title: "Review notes" };
  const original = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input).startsWith("/api/planning")) return json({ ...plan, tasks: [...plan.tasks, second] });
    return original(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: "Start tracking" }));
  await user.selectOptions(screen.getByLabelText("Task to track"), second.id);
  await user.click(screen.getByRole("link", { name: "Plan" }));
  await user.click(screen.getByRole("button", { name: "Start tracking" }));
  expect(screen.getByLabelText("Task to track")).toHaveValue(LEAF);
});

test("direct Track exposes a task-choice load failure and retries without changing duration", async () => {
  service();
  window.history.replaceState(null, "", "/#track");
  const original = vi.mocked(fetch).getMockImplementation()!;
  let attempt = 0;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input).startsWith("/api/planning") && ++attempt === 1) throw new TypeError("Failed read");
    return original(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Refresh task choices to try again");
  expect(screen.getByLabelText("Task to track")).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), { target: { value: "18" } });
  await user.click(screen.getByRole("button", { name: "Refresh task choices" }));
  await waitFor(() => expect(screen.getByLabelText("Task to track")).toBeEnabled());
  expect(screen.getByLabelText("Duration (minutes)")).toHaveValue(18);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("the compact timer remains available while Plan operations are usable", async () => {
  service(running());
  const user = userEvent.setup();
  render(<App />);
  const compact = await screen.findByRole("complementary", { name: "Active countdown" });
  expect(compact).toHaveTextContent(task.title);
  await user.type(await screen.findByLabelText("Title"), "Another task");
  expect(await screen.findByRole("button", { name: "Add task" })).toBeEnabled();
  await user.click(within(compact).getByRole("button", { name: "Pause" }));
  expect(compact).toHaveTextContent("Paused");
  await user.click(within(compact).getByRole("button", { name: "Open Track" }));
  expect(screen.getByRole("region", { name: "Current session" })).toBeVisible();
  expect(screen.queryByRole("complementary", { name: "Active countdown" })).not.toBeInTheDocument();
});

test("failed Start keeps inputs and uses the identical operation ID on retry", async () => {
  const { calls } = service();
  const original = vi.mocked(fetch).getMockImplementation()!;
  let fail = true;
  const attempts: Record<string, unknown>[] = [];
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input) === "/api/timer/start") {
      attempts.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
      if (fail) { fail = false; throw new TypeError("Disconnected"); }
    }
    return original(input, init);
  });
  const user = userEvent.setup();
  render(<Harness />);
  const start = await screen.findByRole("button", { name: "Start countdown" });
  await waitFor(() => expect(start).toBeEnabled());
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), { target: { value: "7" } });
  await user.click(start);
  expect(await screen.findByRole("alert")).toHaveTextContent("Your inputs are kept");
  expect(screen.getByLabelText("Duration (minutes)")).toHaveValue(7);
  await user.click(start);
  expect(await screen.findByRole("region", { name: "Current session" })).toBeVisible();
  expect(attempts).toHaveLength(2);
  expect(attempts[0]).toEqual(attempts[1]);
  expect(calls.filter((call) => call.url === "/api/timer/start")).toHaveLength(1);
});

test("a lost successful Start response is acknowledged by poll and a later session gets a new ID", async () => {
  service();
  const original = vi.mocked(fetch).getMockImplementation()!;
  const attempts: Record<string, unknown>[] = [];
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    const response = await original(input, init);
    if (String(input) === "/api/timer/start") {
      attempts.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
      if (attempts.length === 1) throw new TypeError("Lost response");
    }
    return response;
  });
  const user = userEvent.setup();
  render(<Harness />);
  await waitFor(() => expect(screen.getByRole("button", { name: "Start countdown" })).toBeEnabled());
  await user.click(screen.getByRole("button", { name: "Start countdown" }));
  await user.click(await screen.findByRole("button", { name: "Finish early" }));
  await user.click(await screen.findByRole("button", { name: "Start countdown" }));
  await screen.findByRole("region", { name: "Current session" });
  expect(attempts).toHaveLength(2);
  expect(attempts[0].operation_id).not.toBe(attempts[1].operation_id);
});

test("a competing tab conflict refreshes the active session instead of creating local timer state", async () => {
  const { holder } = service();
  const user = userEvent.setup();
  render(<Harness />);
  await waitFor(() => expect(screen.getByRole("button", { name: "Start countdown" })).toBeEnabled());
  holder.state = running({ task_title: "Other tab's task" });
  await user.click(screen.getByRole("button", { name: "Start countdown" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Another session is active");
  expect(await screen.findByRole("region", { name: "Current session" })).toHaveTextContent("Other tab's task");
  expect(screen.queryByRole("button", { name: "Start countdown" })).not.toBeInTheDocument();
});

test("refresh reconstructs paused state and interrupted sessions explicitly save confirmed time", async () => {
  const { calls, holder } = service(running({ state: "paused", active_seconds: 15, remaining_seconds: 45, deadline_at: null }));
  const user = userEvent.setup();
  const first = render(<Harness />);
  expect(await screen.findByRole("button", { name: "Resume" })).toBeEnabled();
  first.unmount();
  holder.state = running({ state: "needs_review", active_seconds: 15, remaining_seconds: 45, deadline_at: null, review_reason: "The service restarted. Uncertain time is excluded." });
  render(<Harness />);
  expect(await screen.findByRole("status", { name: "Session recovery" })).toHaveTextContent("The service restarted");
  expect(screen.queryByRole("button", { name: "Resume" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Finish early" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Save confirmed time and finish" }));
  expect(await screen.findByRole("region", { name: "Saved session outcome" })).toHaveTextContent("Interrupted · uncertain time excluded");
  expect(calls.find((call) => call.url.endsWith("/recover"))?.body).toMatchObject({ resolution: "finish", discard_uncertain: true, expected_revision: 1 });
});

test("interruption review explains confirmed time and continues the same session by keyboard without crediting the gap", async () => {
  const { calls, holder } = service(interrupted());
  const user = userEvent.setup();
  render(<Harness />);
  const review = await screen.findByRole("status", { name: "Session recovery" });
  expect(review).toHaveTextContent("Confirmed active time: 00:15");
  expect(review).toHaveTextContent("Time since the last saved checkpoint is excluded");
  expect(review).toHaveTextContent("Last confirmed:");
  expect(screen.getByRole("timer", { name: "Time remaining" })).toHaveTextContent("00:45");
  expect(screen.queryByRole("button", { name: "Resume" })).not.toBeInTheDocument();
  const resume = screen.getByRole("button", { name: "Continue with confirmed time" });
  resume.focus();
  await user.keyboard("{Enter}");
  expect(await screen.findByRole("button", { name: "Pause" })).toBeEnabled();
  expect(holder.state.active_session).toMatchObject({ id: session().id, state: "running", active_seconds: 15, remaining_seconds: 45 });
  expect(calls.find((call) => call.url.endsWith("/recover"))?.body).toMatchObject({ resolution: "resume", discard_uncertain: true, expected_revision: 1, operation_id: expect.any(String) });
  expect(calls.some((call) => call.url.includes("/completion"))).toBe(false);
  expect(screen.queryByRole("status", { name: "Session recovery" })).not.toBeInTheDocument();
});

test("measured sleep stays paused with an explanation until ordinary Resume", async () => {
  const state = interrupted();
  state.active_session = { ...state.active_session!, state: "paused", recovery: { ...state.active_session!.recovery!, kind: "sleep", measured_sleep_seconds: 120 } };
  const { calls, holder } = service(state);
  const user = userEvent.setup();
  render(<Harness />);
  expect(await screen.findByText("Paused after sleep. Sleep time is excluded. Resume when you are ready.")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Continue with confirmed time" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Resume" }));
  expect(await screen.findByRole("button", { name: "Pause" })).toBeEnabled();
  expect(holder.state.active_session?.active_seconds).toBe(15);
  expect(calls.filter((call) => call.url.endsWith("/resume"))).toHaveLength(1);
  expect(calls.some((call) => call.url.endsWith("/recover"))).toBe(false);
  expect(screen.queryByText(/Paused after sleep/)).not.toBeInTheDocument();
});

test("a lost recovery response replays the identical request once without adding time or a second resolution", async () => {
  const { holder } = service(interrupted());
  const original = vi.mocked(fetch).getMockImplementation()!;
  const attempts: Record<string, unknown>[] = [];
  let readsUnavailable = false;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input) === "/api/timer" && readsUnavailable) throw new TypeError("Disconnected");
    const response = await original(input, init);
    if (String(input).endsWith("/recover")) {
      attempts.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
      if (attempts.length === 1) { readsUnavailable = true; throw new TypeError("Lost response"); }
      readsUnavailable = false;
    }
    return response;
  });
  const user = userEvent.setup();
  render(<Harness />);
  const resume = await screen.findByRole("button", { name: "Continue with confirmed time" });
  await user.click(resume);
  expect(await screen.findByRole("alert")).toHaveTextContent("Your inputs are kept");
  expect(screen.getByRole("timer")).toHaveTextContent("00:45");
  await user.click(resume);
  expect(await screen.findByRole("button", { name: "Pause" })).toBeEnabled();
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
  expect(holder.state.active_session).toMatchObject({ revision: 2, active_seconds: 15, remaining_seconds: 45 });
});

test("an uncommitted recovery choice survives a page reload and retries its original operation", async () => {
  service(interrupted());
  const original = vi.mocked(fetch).getMockImplementation()!;
  const attempts: Record<string, unknown>[] = [];
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input).endsWith("/recover")) {
      attempts.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
      if (attempts.length === 1) throw new TypeError("Disconnected");
    }
    return original(input, init);
  });
  const user = userEvent.setup();
  const first = render(<Harness />);
  await user.click(await screen.findByRole("button", { name: "Save confirmed time and finish" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Your inputs are kept");
  first.unmount();
  render(<Harness />);
  await user.click(await screen.findByRole("button", { name: "Save confirmed time and finish" }));
  expect(await screen.findByRole("region", { name: "Saved session outcome" })).toHaveTextContent("00:15 active time");
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
});

test("a stale recovery choice refreshes the state resolved in another tab", async () => {
  const { holder, calls } = service(interrupted());
  const user = userEvent.setup();
  render(<Harness />);
  const resume = await screen.findByRole("button", { name: "Continue with confirmed time" });
  holder.state = running({ active_seconds: 15, remaining_seconds: 45, revision: 2 });
  await user.click(resume);
  expect(await screen.findByRole("alert")).toHaveTextContent("The countdown changed in another tab");
  expect(await screen.findByRole("button", { name: "Pause" })).toBeEnabled();
  expect(screen.queryByRole("button", { name: "Continue with confirmed time" })).not.toBeInTheDocument();
  expect(calls.filter((call) => call.url.endsWith("/recover"))).toHaveLength(1);
  expect(sessionStorage.getItem("bearplans.timer.pending")).toBeNull();
});

test("recovery disables both choices while saving and keeps the review if saving fails", async () => {
  service(interrupted());
  const original = vi.mocked(fetch).getMockImplementation()!;
  let rejectRequest!: (error: unknown) => void;
  vi.mocked(fetch).mockImplementation(async (input, init) => String(input).endsWith("/recover")
    ? new Promise<Response>((_resolve, reject) => { rejectRequest = reject; }) : original(input, init));
  const user = userEvent.setup();
  render(<Harness />);
  const resume = await screen.findByRole("button", { name: "Continue with confirmed time" });
  const finish = screen.getByRole("button", { name: "Save confirmed time and finish" });
  await user.click(resume);
  expect(resume).toBeDisabled();
  expect(finish).toBeDisabled();
  expect(screen.getByRole("region", { name: "Current session" })).toHaveAttribute("aria-busy", "true");
  await act(async () => rejectRequest(new TypeError("Disconnected")));
  expect(await screen.findByRole("alert")).toHaveTextContent("Your inputs are kept");
  expect(resume).toBeEnabled();
  expect(finish).toBeEnabled();
  expect(screen.getByRole("status", { name: "Session recovery" })).toHaveTextContent("00:15");
});

test("display ticks interpolate service remaining time, stop while paused, and never save expiry locally", async () => {
  vi.useFakeTimers();
  let monotonic = 0;
  vi.spyOn(performance, "now").mockImplementation(() => monotonic);
  const { holder, calls } = service(running({ remaining_seconds: 1.5 }));
  render(<Harness />);
  await act(async () => { await Promise.resolve(); });
  expect(screen.getByRole("timer")).toHaveTextContent("00:02");
  holder.state = running({ state: "paused", remaining_seconds: 45, deadline_at: null });
  monotonic = 1000;
  await act(async () => { vi.advanceTimersByTime(1000); });
  expect(screen.getByRole("timer")).toHaveTextContent("00:01");
  monotonic = 2000;
  await act(async () => { vi.advanceTimersByTime(1000); });
  expect(screen.getByRole("timer")).toHaveTextContent("00:45");
  monotonic = 9000;
  await act(async () => { vi.advanceTimersByTime(1000); });
  expect(screen.getByRole("timer")).toHaveTextContent("00:45");
  holder.state = { ...empty(), last_session: session({ state: "finished", outcome: "completed", active_seconds: 60, remaining_seconds: 0, finished_at: NOW }) };
  await act(async () => { vi.advanceTimersByTime(1000); });
  expect(screen.getByRole("region", { name: "Saved session outcome" })).toHaveTextContent("Countdown completed");
  expect(calls.every((call) => call.method === "GET")).toBe(true);
});

test("hiding the tab refreshes authoritative state without sending pause or finish", async () => {
  const { calls } = service(running());
  render(<Harness />);
  await screen.findByRole("button", { name: "Pause" });
  fireEvent(document, new Event("visibilitychange"));
  await waitFor(() => expect(calls.filter((call) => call.url === "/api/timer")).toHaveLength(2));
  expect(calls.every((call) => call.method === "GET")).toBe(true);
});

test("remaining display handles the three-hour cap and never goes negative", () => {
  expect(formatRemaining(10800)).toBe("3:00:00");
  expect(formatRemaining(60.1)).toBe("01:01");
  expect(formatRemaining(-5)).toBe("00:00");
});

test("browser countdown ticks never advance the confirmed tree stage, including pause and review", async () => {
  vi.useFakeTimers();
  let monotonic = 0;
  vi.spyOn(performance, "now").mockImplementation(() => monotonic);
  const tree = { id: "pine-1", species: "pine", stage: "seedling", progress: 0.49, outcome: null } as const;
  const { holder } = service(running({ tree, active_seconds: 29.4, remaining_seconds: 30.6 }));
  render(<Harness />);
  await act(async () => { await Promise.resolve(); });
  const growth = screen.getByRole("progressbar", { name: "Confirmed tree growth" });
  expect(screen.getByRole("img", { name: "Pine seedling" })).toBeVisible();
  monotonic = 1200;
  await act(async () => { vi.advanceTimersByTime(1000); });
  expect(screen.getByRole("timer")).toHaveTextContent("00:30");
  expect(growth).toHaveAttribute("value", "0.49");
  expect(screen.getByRole("img", { name: "Pine seedling" })).toBeVisible();
  holder.state = running({ tree, state: "paused", active_seconds: 29.4, remaining_seconds: 30.6 });
  await act(async () => { vi.advanceTimersByTime(1000); });
  expect(screen.getByText("Growth is preserved while paused.")).toBeVisible();
  holder.state = { ...interrupted(), active_session: { ...interrupted().active_session!, tree } };
  monotonic = 90000;
  await act(async () => { vi.advanceTimersByTime(2000); });
  expect(screen.getByText(/Growth is frozen at confirmed time/)).toBeVisible();
  expect(growth).toHaveAttribute("value", "0.49");
  expect(screen.queryByRole("img", { name: "Pine mature" })).not.toBeInTheDocument();
});

test.each(["mature", "unfinished"] as const)("saved %s tree displays its server outcome beside the associated session", async (outcome) => {
  const mature = outcome === "mature";
  service({ ...empty(), last_session: session({ state: "finished", outcome: mature ? "completed" : "finished_early", active_seconds: mature ? 60 : 59.99,
    finished_at: NOW, tree: { id: "pine-1", species: "pine", stage: mature ? "mature" : "sapling", progress: mature ? 1 : 0.9998, outcome } }) });
  render(<Harness />);
  const saved = await screen.findByRole("region", { name: "Saved session outcome" });
  expect(within(saved).getByRole("heading", { name: mature ? "Mature Pine" : "Unfinished Pine" })).toBeVisible();
  expect(within(saved).getByText(mature ? "100% of your countdown confirmed" : "99% of your countdown confirmed")).toBeVisible();
  expect(within(saved).getByText(task.title, { exact: false })).toBeVisible();
  if (!mature) expect(screen.queryByRole("img", { name: "Pine mature" })).not.toBeInTheDocument();
});

test("old active sessions explain eligibility without creating a tree from display time", async () => {
  service(running({ tree: null, active_seconds: 59, remaining_seconds: 1 }));
  render(<Harness />);
  expect(await screen.findByText(/This session began before trees were available/)).toBeVisible();
  expect(screen.queryByRole("region", { name: "Session tree" })).not.toBeInTheDocument();
});
