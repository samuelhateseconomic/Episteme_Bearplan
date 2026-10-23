import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, vi } from "vitest";
import { Corrections } from "./Corrections";
import type { CorrectionPreview, SavedSession } from "./api";

const HOUR = 3_600_000_000;
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const session = (over: Partial<SavedSession> = {}): SavedSession => ({
  id: "session", task_title: "Saved focus", project_name: "Math", parent_title: "Exercises", finished_at: "2026-10-23T20:00:00Z",
  duration_minutes: 60, active_microseconds: HOUR, outcome: "completed", revision: 4, blocked_reason: null, coin_contribution: 60,
  intervals: [{ id: "interval", started_at: "2026-10-23T19:00:00Z", ended_at: "2026-10-23T20:00:00Z", active_microseconds: HOUR, maximum_microseconds: HOUR }],
  history: [], ...over,
});
const preview = (): CorrectionPreview => ({
  session_id: "session", preview_token: "reviewed", before_microseconds: HOUR, after_microseconds: HOUR / 2,
  coin_delta: -30, balance_before: 0, balance_after: -30, coin_contribution_after: 30,
  tree_before: "mature", tree_after: "unfinished", timezone: "UTC",
  days: [{ date: "2026-10-23", before_microseconds: HOUR, after_microseconds: HOUR / 2,
    day_total_before_microseconds: HOUR, day_total_after_microseconds: HOUR / 2, qualified_before: true, qualified_after: false }],
});
const result = { operation_id: "key", session_id: "session", revision: 5, active_microseconds: HOUR / 2, coin_delta: -30, balance_at_save: -30, tree_outcome: "unfinished" };

beforeEach(() => localStorage.clear());

async function prepare(user: ReturnType<typeof userEvent.setup>, value = "1800") {
  await user.click(await screen.findByRole("button", { name: "Correct saved time" }));
  const seconds = screen.getByLabelText(/Interval 1 active seconds/);
  await user.clear(seconds); await user.type(seconds, value);
  await user.type(screen.getByLabelText("Reason for correction"), "Exclude an unattended break");
  await user.click(screen.getByRole("button", { name: "Review correction" }));
}

test("review explains time, coin, tree and streak effects; cancel never applies", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(async (path) => json(String(path).endsWith("/preview") ? preview() : { sessions: [session()] }));
  const user = userEvent.setup();
  render(<Corrections visible onApplied={vi.fn()} />);
  await prepare(user);
  const review = await screen.findByRole("region", { name: "Correction preview" });
  expect(review).toHaveTextContent("Balance: 0 → -30");
  expect(review).toHaveTextContent("mature → unfinished");
  expect(review).toHaveTextContent("Qualified → Below goal");
  expect(review).toHaveTextContent("Owned species stay yours; new purchases are blocked");
  expect(screen.getByLabelText("Reason for correction")).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Cancel correction" }));
  expect(screen.queryByRole("region", { name: "Correction preview" })).not.toBeInTheDocument();
  expect(fetcher.mock.calls.filter(([path]) => String(path).endsWith("/correction"))).toHaveLength(0);
});

test("lost apply response retains the exact operation after remount and retries once", async () => {
  const packets: string[] = [];
  let fail = true;
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(async (path, init) => {
    if (String(path).endsWith("/preview")) return json(preview());
    if (String(path).endsWith("/correction")) {
      packets.push(init?.body as string);
      if (fail) throw new Error("Lost response");
      return json(result);
    }
    return json({ sessions: [session()] });
  });
  const user = userEvent.setup(); const applied = vi.fn();
  const first = render(<Corrections visible onApplied={applied} />);
  await prepare(user);
  await user.click(await screen.findByRole("button", { name: "Apply correction" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Cannot reach");
  expect(Object.keys(localStorage).filter((key) => key.startsWith("bearplans-pending-correction"))).toHaveLength(1);
  first.unmount(); fail = false;
  render(<Corrections visible onApplied={applied} />);
  const retry = await screen.findByRole("button", { name: "Retry correction" });
  retry.focus(); await user.keyboard("{Enter}");
  expect(await screen.findByText(/Correction saved/)).toHaveTextContent("Coin adjustment: -30");
  expect(packets).toHaveLength(2); expect(packets[0]).toBe(packets[1]);
  expect(applied).toHaveBeenCalledOnce(); expect(localStorage.length).toBe(0);
  expect(fetcher).toHaveBeenCalled();
});

test("stale apply clears the reviewed request and keeps input for refresh and another review", async () => {
  let revision = 4;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (path) => {
    if (String(path).endsWith("/preview")) return json(preview());
    if (String(path).endsWith("/correction")) return json({ error: { message: "The session changed. Review again." } }, 409);
    return json({ sessions: [session({ revision })] });
  });
  const user = userEvent.setup();
  render(<Corrections visible onApplied={vi.fn()} />);
  await prepare(user);
  await user.click(await screen.findByRole("button", { name: "Apply correction" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("The session changed");
  expect(screen.getByLabelText(/Interval 1 active seconds/)).toHaveValue("1800");
  expect(screen.getByLabelText("Reason for correction")).toHaveValue("Exclude an unattended break");
  expect(localStorage.length).toBe(0); revision = 5;
  await user.click(screen.getByRole("button", { name: "Refresh saved sessions" }));
  expect(screen.getByLabelText(/Interval 1 active seconds/)).toHaveValue("1800");
});

test("microsecond input is exact and excessive precision fails before a preview request", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(async (path) => json(String(path).endsWith("/preview") ? preview() : { sessions: [session()] }));
  const user = userEvent.setup(); render(<Corrections visible onApplied={vi.fn()} />);
  await prepare(user, "0.000001");
  const body = JSON.parse(fetcher.mock.calls.find(([path]) => String(path).endsWith("/preview"))![1]?.body as string);
  expect(body.intervals[0].active_microseconds).toBe(1);
  await user.click(await screen.findByRole("button", { name: "Back to editing" }));
  const input = screen.getByLabelText(/Interval 1 active seconds/);
  await user.clear(input); await user.type(input, "0.0000001");
  await user.click(screen.getByRole("button", { name: "Review correction" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("at most six decimal places");
  expect(fetcher.mock.calls.filter(([path]) => String(path).endsWith("/preview"))).toHaveLength(1);
});

test("ineligible records explain restrictions and history prepares a reviewed reversal", async () => {
  const history = [{ operation_id: "old", reason: "Prior break", created_at: "2026-10-23T20:10:00Z",
    before: [{ id: "interval", active_microseconds: HOUR }], after: [{ id: "interval", active_microseconds: HOUR / 2 }] }];
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ sessions: [session({ id: "blocked", blocked_reason: "Saved totals disagree." }), session({ history })] }));
  const user = userEvent.setup(); render(<Corrections visible onApplied={vi.fn()} />);
  expect((await screen.findAllByRole("button", { name: "Correct saved time" }))[0]).toBeDisabled();
  await user.click(screen.getByText("Correction history (1)"));
  await user.click(screen.getByRole("button", { name: "Prepare reversal of latest correction" }));
  expect(screen.getByLabelText(/Interval 1 active seconds/)).toHaveValue("3600");
  expect(screen.getByLabelText("Reason for correction")).toHaveValue("Reversal of correction old");
  expect(screen.getByRole("button", { name: "Review correction" })).toBeVisible();
});

test("loading, older-service failure and empty retry remain usable", async () => {
  let resolve!: (response: Response) => void;
  vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => new Promise((done) => { resolve = done; }))
    .mockResolvedValueOnce(json({ sessions: [] }));
  const user = userEvent.setup(); render(<Corrections visible onApplied={vi.fn()} />);
  expect(screen.getByRole("button", { name: "Refresh saved sessions" })).toBeDisabled();
  await act(async () => resolve(json({}, 404)));
  expect(await screen.findByRole("alert")).toHaveTextContent("Restart BearPlans");
  await user.click(screen.getByRole("button", { name: "Refresh saved sessions" }));
  expect(await screen.findByText("No saved sessions yet.")).toBeVisible();
});

test("one queued retry cannot delete another tab's pending request", async () => {
  const packet = { session_id: "session", operation_id: "first", preview_token: "reviewed",
    draft: { reason: "Fix", expected_revision: 4, intervals: [{ id: "interval", active_microseconds: 1 }] } };
  localStorage.setItem("bearplans-pending-correction-v1:first", JSON.stringify(packet));
  localStorage.setItem("bearplans-pending-correction-v1:second", JSON.stringify({ ...packet, operation_id: "second" }));
  vi.spyOn(globalThis, "fetch").mockImplementation(async (path) => json(String(path).endsWith("/correction") ? result : { sessions: [] }));
  const user = userEvent.setup(); render(<Corrections visible onApplied={vi.fn()} />);
  await user.click(await screen.findByRole("button", { name: "Retry correction" }));
  expect(await screen.findByText(/Correction saved/)).toBeVisible();
  expect(localStorage.getItem("bearplans-pending-correction-v1:first")).toBeNull();
  expect(localStorage.getItem("bearplans-pending-correction-v1:second")).not.toBeNull();
  expect(screen.getByRole("button", { name: "Retry correction" })).toBeVisible();
});

test("stale retry after reload restores the rejected inputs against current records", async () => {
  const packet = { session_id: "session", operation_id: "retry", preview_token: "old",
    draft: { expected_revision: 4, reason: "Keep this reason", intervals: [{ id: "interval", active_microseconds: HOUR / 2 }] } };
  localStorage.setItem("bearplans-pending-correction-v1:retry", JSON.stringify(packet));
  vi.spyOn(globalThis, "fetch").mockImplementation(async (path) => String(path).endsWith("/correction")
    ? json({ error: { message: "The wallet changed. Review again." } }, 409) : json({ sessions: [session({ revision: 5 })] }));
  const user = userEvent.setup(); render(<Corrections visible onApplied={vi.fn()} />);
  await user.click(await screen.findByRole("button", { name: "Retry correction" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("wallet changed");
  expect(await screen.findByLabelText("Reason for correction")).toHaveValue("Keep this reason");
  expect(screen.getByLabelText(/Interval 1 active seconds/)).toHaveValue("1800");
  expect(localStorage.length).toBe(0);
});

test("storage failure keeps the review and prevents an unrecoverable apply request", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(async (path) => json(String(path).endsWith("/preview") ? preview() : { sessions: [session()] }));
  const user = userEvent.setup(); render(<Corrections visible onApplied={vi.fn()} />);
  await prepare(user);
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Denied storage"); });
  await user.click(await screen.findByRole("button", { name: "Apply correction" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("retry request could not be saved");
  expect(screen.getByRole("region", { name: "Correction preview" })).toBeVisible();
  expect(fetcher.mock.calls.filter(([path]) => String(path).endsWith("/correction"))).toHaveLength(0);
});
