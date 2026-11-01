import { act, render, screen } from "@testing-library/react";
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
