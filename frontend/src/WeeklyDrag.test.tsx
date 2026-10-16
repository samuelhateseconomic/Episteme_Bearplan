import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import type { Placement, Planning, Task } from "./api";
import { WeeklyPlanner, type usePlanning } from "./WeeklyPlanner";

const at = "2026-10-16T16:00:00.000000Z";
const task: Task = { id: "leaf", project_id: "project", parent_id: null, title: "Read chapter", notes: "Keep notes", deadline: "2026-10-25", estimate_minutes: 30, completed: false, completed_at: null, subtask_count: 0, completed_subtask_count: 0, created_at: at, updated_at: at, revision: 1 };
const source: Placement = { id: "p1", task_id: task.id, planned_date: "2026-10-15", created_at: at, updated_at: at, revision: 1 };
function setup(placements = [source], overrides: Partial<Planning> = {}) {
  const plan: Planning = { today: "2026-10-15", timezone: "America/Los_Angeles", week_start: "2026-10-12", week_end: "2026-10-18", tasks: [task], placements, ...overrides };
  const state: ReturnType<typeof usePlanning> = { plan, selectedDay: "2026-10-15", loading: false, error: null, setSelectedDay: vi.fn(), refresh: vi.fn(), navigate: vi.fn() };
  const run = vi.fn(async (work: () => Promise<unknown>) => { await work(); });
  const onTrack = vi.fn();
  const rendered = render(<WeeklyPlanner state={state} projects={[]} onRun={run} locked={false} onTrack={onTrack} />);
  return { ...rendered, state, run, onTrack };
}
function transfer() { return { setData: vi.fn(), effectAllowed: "none", dropEffect: "none" }; }
const handle = () => screen.getByRole("img", { name: "Drag “Read chapter” from Oct 15, 2026" });
const friday = () => screen.getByRole("region", { name: "Friday, Oct 16, 2026" });
const thursday = () => screen.getByRole("region", { name: "Thursday, Oct 15, 2026" });
function drag(element: Element, type: string, dataTransfer: ReturnType<typeof transfer>, add = false) {
  // jsdom has no DragEvent constructor; MouseEvent supplies real modifier fields.
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, altKey: add });
  Object.defineProperty(event, "dataTransfer", { value: dataTransfer });
  return fireEvent(element, event);
}
function start(add = false) {
  const dataTransfer = transfer();
  drag(handle(), "dragstart", dataTransfer, add);
  return dataTransfer;
}
function json(body: unknown, status = 200) { return new Response(JSON.stringify(body), { status }); }

test("a handle moves the existing placement, highlights valid days and leaves source visible while saving", async () => {
  let finish!: (response: Response) => void;
  const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  setup();
  expect(screen.getByText(/Option \(Mac\) \/ Alt \(Windows\)/)).toBeInTheDocument();
  const dataTransfer = start();
  expect(screen.getByRole("status")).toHaveTextContent("Move");
  expect(friday()).toHaveClass("drop-valid");
  expect(thursday()).toHaveClass("drop-source");
  fireEvent.dragOver(friday(), { dataTransfer });
  expect(friday()).toHaveClass("drop-over");
  fireEvent.drop(friday(), { dataTransfer });
  expect(fetch).toHaveBeenCalledWith("/api/placements/p1", expect.objectContaining({ method: "PATCH", body: JSON.stringify({ planned_date: "2026-10-16" }) }));
  expect(within(thursday()).getByLabelText("Read chapter, planned Oct 15, 2026")).toBeInTheDocument();
  expect(handle()).toHaveAttribute("draggable", "false");
  finish(json({ ...source, planned_date: "2026-10-16" }));
  await waitFor(() => expect(screen.queryByText("Saving planned date…")).not.toBeInTheDocument());
});

test("Option/Alt at drop adds a destination with source identity and keeps the source placement", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ ...source, id: "p2", planned_date: "2026-10-16" }));
  setup();
  const dataTransfer = start();
  fireEvent.keyDown(window, { key: "Alt" });
  expect(screen.getByRole("status")).toHaveTextContent("Add");
  fireEvent.keyUp(window, { key: "Alt" });
  expect(screen.getByRole("status")).toHaveTextContent("Move");
  drag(friday(), "dragover", dataTransfer, true);
  expect(dataTransfer.dropEffect).toBe("copy");
  expect(screen.getByRole("status")).toHaveTextContent("Add");
  drag(friday(), "drop", dataTransfer, true);
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  expect(fetch).toHaveBeenCalledWith("/api/placements", expect.objectContaining({ method: "POST", body: JSON.stringify({ task_id: task.id, planned_date: "2026-10-16", source_placement_id: source.id }) }));
  expect(within(thursday()).getByLabelText("Read chapter, planned Oct 15, 2026")).toBeInTheDocument();
});

test("narrow-layout day buttons accept drops without changing selected day or week", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(source));
  const { state } = setup();
  const target = within(screen.getByRole("group", { name: "Selected day" })).getByRole("button", { name: /FriOct 16/ });
  const dataTransfer = start();
  expect(target).toHaveClass("drop-valid");
  fireEvent.dragOver(target, { dataTransfer });
  fireEvent.drop(target, { dataTransfer });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  expect(state.setSelectedDay).not.toHaveBeenCalled();
  expect(state.navigate).not.toHaveBeenCalled();
});

test.each([false, true])("duplicate destination rejects %s add mode and keeps both placements", async (add) => {
  const fetch = vi.spyOn(globalThis, "fetch");
  setup([source, { ...source, id: "p2", planned_date: "2026-10-16" }]);
  const dataTransfer = start(add);
  expect(friday()).toHaveClass("drop-conflict");
  expect(friday()).not.toHaveClass("drop-valid");
  drag(friday(), "dragover", dataTransfer, add);
  expect(screen.getByRole("status")).toHaveTextContent("already planned here");
  drag(friday(), "drop", dataTransfer, add);
  expect(screen.getByRole("alert")).toHaveTextContent("Both existing placements are kept");
  expect(screen.getAllByRole("checkbox")).toHaveLength(2);
  // A new native drag must not remove in-flow feedback and shift the source.
  start(add);
  expect(screen.getByRole("alert")).toHaveTextContent("Both existing placements are kept");
  expect(fetch).not.toHaveBeenCalled();
});

test("same day, outside drop, Escape and drag cancellation never write", () => {
  const fetch = vi.spyOn(globalThis, "fetch");
  setup();
  let dataTransfer = start(true);
  drag(thursday(), "drop", dataTransfer, true);
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  dataTransfer = start();
  fireEvent.drop(document.body, { dataTransfer });
  fireEvent.dragEnd(handle(), { dataTransfer });
  expect(friday()).not.toHaveClass("drop-valid");
  dataTransfer = start();
  fireEvent.keyDown(window, { key: "Escape" });
  fireEvent.drop(friday(), { dataTransfer });
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  expect(fetch).not.toHaveBeenCalled();
});

test("failed saves retain displayed placements and offer refresh for stale state", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ error: { message: "This week is now closed. No placements were changed." } }, 409));
  const { state } = setup();
  const dataTransfer = start();
  fireEvent.drop(friday(), { dataTransfer });
  expect(await screen.findByRole("alert")).toHaveTextContent("This week is now closed");
  expect(screen.getByRole("alert")).toHaveTextContent("Refresh the weekly plan to check its saved state");
  expect(within(thursday()).getByLabelText("Read chapter, planned Oct 15, 2026")).toBeInTheDocument();
  await userEvent.setup().click(screen.getByRole("button", { name: "Refresh weekly plan" }));
  expect(state.refresh).toHaveBeenCalledTimes(1);
});

test("closed history has no drag handles or scheduling forms and ignores drops", () => {
  const fetch = vi.spyOn(globalThis, "fetch");
  setup([], { closed_week: { snapshot_version: 1, week_start: "2026-10-12", week_end: "2026-10-18", closed_at: at, timezone: "America/Los_Angeles", tasks: [{ ...task, project_name: "Project", parent_title: null }], placements: [source], completed: 0, total: 1 } });
  expect(screen.queryByRole("img", { name: /Drag/ })).not.toBeInTheDocument();
  expect(screen.queryByText("Add another planned day")).not.toBeInTheDocument();
  fireEvent.drop(friday(), { dataTransfer: transfer() });
  expect(fetch).not.toHaveBeenCalled();
});

test("card controls cannot initiate drag and still work independently", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ ...task, completed: true }));
  const { onTrack } = setup();
  const checkbox = screen.getByRole("checkbox");
  const tracking = screen.getByRole("button", { name: "Start tracking" });
  const summary = screen.getByText("Move or remove");
  for (const control of [checkbox, tracking, summary, screen.getByText("Read chapter")]) {
    expect(fireEvent.dragStart(control, { dataTransfer: transfer() })).toBe(false);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  }
  await userEvent.setup().click(tracking);
  expect(onTrack).toHaveBeenCalledWith(task.id);
  await userEvent.setup().click(checkbox);
  await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledWith("/api/tasks/leaf/completion", expect.objectContaining({ method: "PUT" })));
});

test("keyboard date form adds another day from a card with source validation", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(source));
  setup();
  const user = userEvent.setup();
  await user.click(screen.getByText("Add another planned day"));
  const date = screen.getByLabelText("Planned date for “Read chapter”");
  expect(date).toHaveValue("2026-10-16");
  date.focus();
  expect(date).toHaveFocus();
  await user.tab();
  expect(screen.getByRole("button", { name: "Add to day" })).toHaveFocus();
  await user.keyboard("{Enter}");
  await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/placements", expect.objectContaining({ method: "POST", body: JSON.stringify({ task_id: task.id, planned_date: "2026-10-16", source_placement_id: source.id }) })));
});
