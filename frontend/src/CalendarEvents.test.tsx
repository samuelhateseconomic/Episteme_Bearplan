import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { CalendarEvents } from "./WeeklyPlanner";
import type { GoogleEvent } from "./api";

const event = (overrides: Partial<GoogleEvent>): GoogleEvent => ({
  calendar_id: "me", calendar_summary: "Me", color: "#9fc6e7", event_id: "a", summary: "Office hours", location: "Soda 283",
  html_link: "", all_day: false, start_at: "2026-11-05T15:00:00-08:00", end_at: "2026-11-05T16:30:00-08:00",
  first_day: "2026-11-05", last_day: "2026-11-05", task_id: null, ...overrides,
});

afterEach(() => vi.restoreAllMocks());

it("shows events and adds one as a task", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ event: event({}), task: {}, planned: true }), { status: 200, headers: { "Content-Type": "application/json" } }));
  const onRun = vi.fn(async (work: () => Promise<unknown>, _done: string) => { await work(); });
  render(<CalendarEvents date="2026-11-05" locked={false} onRun={onRun} events={[event({}), event({ event_id: "b", summary: "Trip", all_day: true, location: "", task_id: "t9" })]} />);
  expect(screen.getByText("From your calendar")).toBeTruthy();
  expect(screen.getByText(/Me · Soda 283/)).toBeTruthy();
  expect(screen.getByText(/All day · Me/)).toBeTruthy();
  expect(screen.getByText("Added as a task")).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: "Add as task" }));
  expect(fetch).toHaveBeenCalledWith("/api/google/events/add", expect.objectContaining({ method: "POST", body: JSON.stringify({ calendar_id: "me", event_id: "a" }) }));
  expect(onRun.mock.calls[0][1]).toMatch(/Added “Office hours” as a task/);
});

it("renders nothing without events", () => {
  const { container } = render(<CalendarEvents date="2026-11-05" locked={false} onRun={vi.fn()} events={[]} />);
  expect(container.textContent).toBe("");
});
