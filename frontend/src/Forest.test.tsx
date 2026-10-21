import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ForestCollection } from "./Forest";
import type { ForestTree } from "./api";

const tree = (over: Partial<ForestTree> = {}): ForestTree => ({
  id: "tree-1", species: "pine", stage: "mature", progress: 1, outcome: "mature",
  session_id: "session-1", task_title: "Reading at session start", project_name: "Original seminar", parent_title: "Original chapter",
  started_at: "2026-10-20T16:00:00.000000Z", finished_at: "2026-10-20T16:01:00.000000Z", duration_minutes: 1, active_seconds: 60,
  ...over,
});
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

test("the forest shows saved mature and unfinished outcomes with historical session context", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ trees: [tree(), tree({ id: "tree-2", session_id: "session-2", stage: "seedling", progress: 0.25, outcome: "unfinished", active_seconds: 15, task_title: "Stopped reading" })] }));
  render(<ForestCollection visible lastSessionId="session-2" />);
  const forest = screen.getByRole("region", { name: "Forest collection" });
  expect(await within(forest).findByText("Mature Pine")).toBeVisible();
  expect(within(forest).getByText("Unfinished Pine")).toBeVisible();
  expect(within(forest).getByText("Reading at session start")).toBeVisible();
  expect(within(forest).getAllByText("Original seminar / Original chapter")).toHaveLength(2);
  expect(within(forest).getByText(/00:15 confirmed active time/)).toBeVisible();
  expect(within(forest).getByRole("img", { name: "Pine mature" })).toBeVisible();
  expect(fetcher).toHaveBeenCalledWith("/api/forest", expect.objectContaining({ signal: expect.any(AbortSignal) }));
});

test("an empty forest explains new-session eligibility and unfinished trees", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ trees: [] }));
  render(<ForestCollection visible lastSessionId={null} />);
  expect(await screen.findByText(/Your forest is ready to grow/)).toBeVisible();
  expect(screen.getByText(/Trees begin with new countdowns/)).toHaveTextContent("earlier sessions stay unchanged");
  expect(screen.getByText(/Early finishes save an unfinished tree/)).toBeVisible();
});

test("forest failures preserve the saved collection and offer a working retry", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json({ trees: [tree()] }))
    .mockResolvedValueOnce(json({ error: { message: "Forest storage is unavailable." } }, 503))
    .mockResolvedValueOnce(json({ trees: [tree(), tree({ id: "tree-2", task_title: "New saved work" })] }));
  const user = userEvent.setup();
  render(<ForestCollection visible lastSessionId="session-1" />);
  await screen.findByText("Reading at session start");
  await user.click(screen.getByRole("button", { name: "Refresh forest" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Forest storage is unavailable");
  expect(screen.getByText("Reading at session start")).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Refresh forest" }));
  expect(await screen.findByText("New saved work")).toBeVisible();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(fetcher).toHaveBeenCalledTimes(3);
});

test("forest loads on Track visibility and refreshes when another session is finalized", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ trees: [] }));
  const { rerender } = render(<ForestCollection visible={false} lastSessionId={null} />);
  expect(fetcher).not.toHaveBeenCalled();
  rerender(<ForestCollection visible lastSessionId={null} />);
  await screen.findByText(/Your forest is ready to grow/);
  fetcher.mockResolvedValue(json({ trees: [tree()] }));
  rerender(<ForestCollection visible lastSessionId="session-1" />);
  expect(await screen.findByText("Reading at session start")).toBeVisible();
  expect(fetcher).toHaveBeenCalledTimes(2);
});

test("a superseded forest response cannot replace newer session results", async () => {
  let resolveOld!: (value: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveOld = resolve; }))
    .mockResolvedValue(json({ trees: [tree({ task_title: "Newest saved work" })] }));
  const { rerender } = render(<ForestCollection visible lastSessionId={null} />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading forest");
  rerender(<ForestCollection visible lastSessionId="session-1" />);
  await screen.findByText("Newest saved work");
  await act(async () => resolveOld(json({ trees: [] })));
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  expect(screen.getByText("Newest saved work")).toBeVisible();
  expect(screen.queryByText(/Your forest is ready to grow/)).not.toBeInTheDocument();
});
