import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { DailyStreak } from "./DailyStreak";
import type { StreakState } from "./api";

const HOUR = 3_600_000_000;
const currentStreak = (count: number) => (_text: string, element: Element | null) => element?.tagName === "P" && element.textContent === `${count} ${count === 1 ? "day" : "days"} in your current streak`;
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const streak = (over: Partial<StreakState> = {}): StreakState => ({
  today: "2026-10-21", timezone: "America/Los_Angeles", threshold_microseconds: HOUR, current_streak: 2, streak_through: "2026-10-20",
  days: [
    { date: "2026-10-15", active_microseconds: 0, qualified: false },
    { date: "2026-10-16", active_microseconds: HOUR, qualified: true },
    { date: "2026-10-17", active_microseconds: HOUR * 2, qualified: true },
    { date: "2026-10-18", active_microseconds: 0, qualified: false },
    { date: "2026-10-19", active_microseconds: HOUR, qualified: true },
    { date: "2026-10-20", active_microseconds: HOUR, qualified: true },
    { date: "2026-10-21", active_microseconds: HOUR / 2, qualified: false },
  ], ...over,
});

afterEach(() => vi.useRealTimers());

test("saved progress uses the service day and preserves yesterday's streak while today is unfinished", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(streak()));
  render(<DailyStreak visible lastSessionId={null} />);
  const section = screen.getByRole("region", { name: "Daily streak" });
  expect(await within(section).findByText(currentStreak(2))).toBeVisible();
  expect(within(section).getByText(/Today can still qualify/)).toHaveTextContent("your streak through yesterday stays intact");
  const progress = within(section).getByRole("progressbar", { name: /Today · Oct 21: 30 min 00 s of 60 min saved/ });
  expect(progress).toHaveAttribute("value", String(HOUR / 2));
  const days = within(section).getByRole("list", { name: "Last seven days" });
  expect(within(days).getAllByRole("listitem")).toHaveLength(7);
  expect(within(days).getAllByText("✓ Qualified")).toHaveLength(4);
  expect(days.querySelector('[aria-current="date"] time')).toHaveAttribute("datetime", "2026-10-21");
  expect(within(section).getByText(/Dates use America\/Los_Angeles/)).toHaveTextContent("Changing the service timezone recalculates the days for saved work");
  expect(within(section).getByText(/Saved sessions count/)).toHaveTextContent("Pauses and uncertain gaps never count");
  expect(fetcher).toHaveBeenCalledWith("/api/streaks", expect.objectContaining({ signal: expect.any(AbortSignal) }));
});

test.each([
  { active: HOUR - 1, qualified: false, label: "59 min 59 s", current: 0 },
  { active: HOUR, qualified: true, label: "60 min 00 s", current: 1 },
  { active: HOUR * 1.5, qualified: true, label: "90 min 00 s", current: 1 },
])("$active microseconds display without rounding across the hour goal", async ({ active, qualified, label, current }) => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json(streak({ current_streak: current, streak_through: qualified ? "2026-10-21" : null, days: [{ date: "2026-10-21", active_microseconds: active, qualified }] })));
  render(<DailyStreak visible lastSessionId={null} />);
  const progress = await screen.findByRole("progressbar", { name: `Today · Oct 21: ${label} of 60 min saved` });
  expect(progress).toHaveAttribute("value", String(Math.min(active, HOUR)));
  expect(progress).toHaveAttribute("max", String(HOUR));
  expect(screen.getByRole("region", { name: "Daily streak" }).textContent?.includes("Today qualifies.")).toBe(qualified);
  expect(screen.queryByText("✓ Qualified") !== null).toBe(qualified);
});

test("loading disables refresh and a keyboard retry keeps the last loaded progress", async () => {
  let finish!: (value: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }))
    .mockResolvedValueOnce(json({ error: { message: "Saved sessions could not be read." } }, 503))
    .mockResolvedValueOnce(json(streak({ current_streak: 3 })));
  const user = userEvent.setup();
  render(<DailyStreak visible lastSessionId={null} />);
  const refresh = screen.getByRole("button", { name: "Refresh streak" });
  expect(refresh).toBeDisabled();
  expect(screen.getByRole("status")).toHaveTextContent("Loading daily streak");
  await act(async () => finish(json(streak())));
  await user.tab();
  expect(refresh).toHaveFocus();
  await user.keyboard("{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("Saved sessions could not be read. Use Refresh streak to try again. Showing the last loaded progress.");
  expect(screen.getByText(currentStreak(2))).toBeVisible();
  await user.keyboard("{Enter}");
  expect(await screen.findByText(currentStreak(3))).toBeVisible();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(fetcher).toHaveBeenCalledTimes(3);
});

test("an earlier running service explains how to load the feature after restart", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ detail: "Not Found" }, 404));
  render(<DailyStreak visible lastSessionId={null} />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Daily streaks need the updated local service. Restart BearPlans, then use Refresh streak.");
  expect(screen.getByRole("button", { name: "Refresh streak" })).toBeEnabled();
});

test("the service calendar and timezone replace stale browser-day assumptions on refresh", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(streak()))
    .mockResolvedValueOnce(json(streak({ today: "2026-10-22", timezone: "Pacific/Auckland", current_streak: 0, streak_through: null, days: [{ date: "2026-10-22", active_microseconds: 0, qualified: false }] })));
  render(<DailyStreak visible lastSessionId={null} />);
  await screen.findByRole("progressbar");
  fireEvent.focus(window);
  expect(await screen.findByRole("progressbar", { name: "Today · Oct 22: 0 min 00 s of 60 min saved" })).toBeVisible();
  expect(screen.getByText(/Dates use Pacific\/Auckland/)).toBeVisible();
  expect(screen.getByText(/Save 60 active minutes in a day to begin a streak/)).toBeVisible();
  expect(fetcher).toHaveBeenCalledTimes(2);
});

test("hidden Track does no reads; a newly finalized session refreshes without duplicating progress", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(streak()));
  const { rerender } = render(<DailyStreak visible={false} lastSessionId={null} />);
  expect(fetcher).not.toHaveBeenCalled();
  rerender(<DailyStreak visible lastSessionId={null} />);
  await screen.findByRole("progressbar");
  fetcher.mockResolvedValue(json(streak({ current_streak: 3 })));
  rerender(<DailyStreak visible lastSessionId="saved-session" />);
  expect(await screen.findByText(currentStreak(3))).toBeVisible();
  rerender(<DailyStreak visible lastSessionId="saved-session" />);
  expect(fetcher).toHaveBeenCalledTimes(2);
});

test("superseded, hidden and aborted responses cannot replace fresh progress", async () => {
  let finishOld!: (value: Response) => void;
  let finishHidden!: (value: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => new Promise((resolve) => { finishOld = resolve; }))
    .mockResolvedValueOnce(json(streak({ current_streak: 3 })))
    .mockImplementationOnce(() => new Promise((resolve) => { finishHidden = resolve; }))
    .mockResolvedValue(json(streak({ current_streak: 4 })));
  const { rerender } = render(<DailyStreak visible lastSessionId={null} />);
  rerender(<DailyStreak visible lastSessionId="saved-session" />);
  await screen.findByText(currentStreak(3));
  await act(async () => finishOld(json(streak())));
  expect(screen.getByText(currentStreak(3))).toBeVisible();
  fireEvent.focus(window);
  rerender(<DailyStreak visible={false} lastSessionId="saved-session" />);
  await act(async () => finishHidden(json(streak({ current_streak: 90 }))));
  rerender(<DailyStreak visible lastSessionId="saved-session" />);
  expect(await screen.findByText(currentStreak(4))).toBeVisible();
  expect(screen.queryByText(/90 days/)).not.toBeInTheDocument();
  expect(fetcher).toHaveBeenCalledTimes(4);
});

test("visible minute rechecks cross midnight while hidden documents stop reads and discard in-flight data", async () => {
  vi.useFakeTimers();
  let finishHidden!: (value: Response) => void;
  let visibility = "visible";
  vi.spyOn(document, "visibilityState", "get").mockImplementation(() => visibility as DocumentVisibilityState);
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(streak()))
    .mockResolvedValueOnce(json(streak({ today: "2026-10-22", current_streak: 0 })))
    .mockImplementationOnce(() => new Promise((resolve) => { finishHidden = resolve; }))
    .mockResolvedValue(json(streak({ current_streak: 4 })));
  const { rerender } = render(<DailyStreak visible lastSessionId={null} />);
  await act(async () => {});
  expect(screen.getByRole("progressbar", { name: /Today · Oct 21/ })).toBeVisible();
  await act(async () => vi.advanceTimersByTimeAsync(60_000));
  expect(screen.getByRole("progressbar", { name: /Today · Oct 22/ })).toBeVisible();
  fireEvent.focus(window);
  visibility = "hidden";
  fireEvent(document, new Event("visibilitychange"));
  await act(async () => finishHidden(json(streak({ current_streak: 90 }))));
  await act(async () => vi.advanceTimersByTimeAsync(120_000));
  expect(fetcher).toHaveBeenCalledTimes(3);
  expect(screen.queryByText(/90 days/)).not.toBeInTheDocument();
  visibility = "visible";
  fireEvent(document, new Event("visibilitychange"));
  await act(async () => {});
  expect(screen.getByText(currentStreak(4))).toBeVisible();
  rerender(<DailyStreak visible={false} lastSessionId={null} />);
  await act(async () => vi.advanceTimersByTimeAsync(120_000));
  expect(fetcher).toHaveBeenCalledTimes(4);
});
