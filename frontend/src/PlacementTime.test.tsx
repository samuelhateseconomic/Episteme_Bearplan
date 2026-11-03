import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { TaskPlanning } from "./WeeklyPlanner";
import type { Placement, Planning, Task } from "./api";

const task: Task = {
  id: "t1", project_id: "p1", parent_id: null, title: "Problem set", notes: "", deadline: null, estimate_minutes: null,
  completed: false, completed_at: null, subtask_count: 0, completed_subtask_count: 0,
  created_at: "2026-11-01T00:00:00Z", updated_at: "2026-11-01T00:00:00Z", revision: 1,
};
const placement = (start_time: string | null): Placement => ({
  id: "pl1", task_id: "t1", planned_date: "2026-11-05", start_time,
  created_at: "2026-11-01T00:00:00Z", updated_at: "2026-11-01T00:00:00Z", revision: 1,
});
const plan = (start_time: string | null): Planning => ({
  today: "2026-11-03", timezone: "America/Los_Angeles", week_start: "2026-11-02", week_end: "2026-11-08",
  tasks: [task], placements: [placement(start_time)],
});

afterEach(() => vi.restoreAllMocks());

it("saves a start time and says Google will remind 30 minutes before", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(placement("14:30")), { status: 200, headers: { "Content-Type": "application/json" } }));
  const onRun = vi.fn(async (work: () => Promise<unknown>, _done: string) => { await work(); });
  render(<TaskPlanning task={task} plan={plan(null)} selectedDay="2026-11-05" onRun={onRun} />);
  await userEvent.click(screen.getByText("Move or remove plan"));
  const input = screen.getByLabelText(/Start time on/);
  await userEvent.type(input, "14:30");
  await userEvent.click(screen.getByRole("button", { name: "Save time" }));
  expect(fetch).toHaveBeenCalledWith("/api/placements/pl1/time", expect.objectContaining({ method: "PUT", body: JSON.stringify({ start_time: "14:30" }) }));
  expect(onRun.mock.calls[0][1]).toMatch(/remind you 30 minutes before/);
});

it("shows the saved time and can clear it", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(placement(null)), { status: 200, headers: { "Content-Type": "application/json" } }));
  const onRun = vi.fn(async (work: () => Promise<unknown>, _done: string) => { await work(); });
  render(<TaskPlanning task={task} plan={plan("09:00")} selectedDay="2026-11-05" onRun={onRun} />);
  expect(screen.getByText(/Planned: .* at 9:00/)).toBeTruthy();
  await userEvent.click(screen.getByText("Move or remove plan"));
  await userEvent.click(screen.getByRole("button", { name: "Clear time" }));
  expect(fetch).toHaveBeenCalledWith("/api/placements/pl1/time", expect.objectContaining({ body: JSON.stringify({ start_time: null }) }));
});
