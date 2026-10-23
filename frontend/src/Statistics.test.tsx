import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { Statistics } from "./Statistics";
import type { StatisticsState } from "./api";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const report = (over: Partial<StatisticsState> = {}): StatisticsState => ({
  today: "2026-10-23", timezone: "America/Los_Angeles", completion: { completed: 1, total: 3, percent: 33.33 },
  active_microseconds: 3_600_000_001, session_count: 2,
  days: [{ date: "2026-10-23", active_microseconds: 3_600_000_001, completed: 1 }],
  projects: [
    { project_id: "math", name: "Math", completion: { completed: 1, total: 2, percent: 50 }, active_microseconds: 2_400_000_001 },
    { project_id: "inbox", name: "Inbox", completion: { completed: 0, total: 1, percent: 0 }, active_microseconds: 1_200_000_000 },
  ],
  tasks: [
    { task_id: "one", project_id: "math", title: "Exercises", parent_title: "Problem set", current_leaf: true, completed: true,
      estimate_minutes: 60, active_microseconds: 2_400_000_001, session_count: 1 },
    { task_id: "two", project_id: "inbox", title: "Essay", parent_title: null, current_leaf: true, completed: false,
      estimate_minutes: null, active_microseconds: 1_200_000_000, session_count: 1 },
    { task_id: "old", project_id: "math", title: "Removed child", parent_title: "Old parent", current_leaf: false, completed: null,
      estimate_minutes: null, active_microseconds: 0, session_count: 0 },
  ], ...over,
});

test("shows service calendar, exact saved credit, current completion, estimates and historical task context", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(report()));
  render(<Statistics visible />);
  expect(await screen.findByText("1 of 3 complete (33.33%)")).toBeVisible();
  expect(screen.getByText("60 min 0.000001 s", { selector: "dd" })).toBeVisible();
  expect(screen.getByText(/Dates use America\/Los_Angeles/)).toBeVisible();
  const days = screen.getByRole("list", { name: "Daily statistics" });
  expect(days.querySelector("time")).toHaveAttribute("datetime", "2026-10-23");
  const tasks = screen.getByRole("list", { name: "Task statistics" });
  expect(within(tasks).getByText("Math / Problem set")).toBeVisible();
  expect(within(tasks).getByText("Estimate: 60 min")).toBeVisible();
  expect(within(tasks).getAllByText("Estimate: Not set")).toHaveLength(2);
  expect(within(tasks).getByText("Historical work · no current leaf")).toBeVisible();
  expect(fetcher).toHaveBeenCalledWith("/api/statistics", expect.objectContaining({ signal: expect.any(AbortSignal) }));
});

test("project filter affects task details and leaves overall totals explicit", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json(report()));
  const user = userEvent.setup();
  render(<Statistics visible />);
  const filter = await screen.findByRole("combobox", { name: "Filter task details by project" });
  await user.selectOptions(filter, "inbox");
  expect(screen.queryByText("Exercises")).not.toBeInTheDocument();
  expect(screen.getByText("Essay")).toBeVisible();
  expect(screen.getByText("1 of 3 complete (33.33%)")).toBeVisible();
  await user.selectOptions(filter, "");
  expect(screen.getByText("Exercises")).toBeVisible();
});

test("keyboard refresh retains last loaded report on failure and recovers", async () => {
  let resolve!: (response: Response) => void;
  vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => new Promise((done) => { resolve = done; }))
    .mockResolvedValueOnce(json({ error: { message: "Saved data unavailable." } }, 503))
    .mockResolvedValueOnce(json(report({ session_count: 3 })));
  const user = userEvent.setup();
  render(<Statistics visible />);
  const refresh = screen.getByRole("button", { name: "Refresh statistics" });
  expect(refresh).toBeDisabled();
  await act(async () => resolve(json(report())));
  refresh.focus();
  await user.keyboard("{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("Saved data unavailable. Use Refresh statistics to try again. Showing the last loaded statistics.");
  expect(screen.getByText("1 of 3 complete (33.33%)")).toBeVisible();
  await user.keyboard("{Enter}");
  expect(await screen.findByText("3", { selector: "dd" })).toBeVisible();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("navigation aborts and ignores stale results, re-entry and focus request fresh statistics", async () => {
  let resolve!: (response: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => new Promise((done) => { resolve = done; }))
    .mockResolvedValue(json(report({ session_count: 7 })));
  const view = render(<Statistics visible />);
  const signal = (fetcher.mock.calls[0][1] as RequestInit).signal;
  view.rerender(<Statistics visible={false} />);
  expect(signal?.aborted).toBe(true);
  await act(async () => resolve(json(report({ session_count: 99 }))));
  view.rerender(<Statistics visible />);
  expect(await screen.findByText("7", { selector: "dd" })).toBeVisible();
  expect(screen.queryByText("99", { selector: "dd" })).not.toBeInTheDocument();
  await act(async () => fireEvent(window, new Event("focus")));
  expect(fetcher).toHaveBeenCalledTimes(3);
});

test("empty report and old service error have usable recovery instructions", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json({}, 404)).mockResolvedValue(json(report({
    completion: { completed: 0, total: 0, percent: 0 }, active_microseconds: 0, session_count: 0, days: [], tasks: [],
  })));
  render(<Statistics visible />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Restart BearPlans, then use Refresh statistics");
  fireEvent.click(screen.getByRole("button", { name: "Refresh statistics" }));
  expect(await screen.findByText("0 of 0 complete (0%)")).toBeVisible();
  expect(screen.getByText("No saved time or completed tasks yet.")).toBeVisible();
  expect(fetcher).toHaveBeenCalledTimes(2);
});
