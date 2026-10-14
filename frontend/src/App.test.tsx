import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "./App";
import type { Task } from "./api";

function task(title: string, n = 1): Task {
  const at = `2026-10-14T16:0${n}:00.000000Z`;
  return { id: `00000000-0000-4000-8000-00000000000${n}`, title, created_at: at, updated_at: at, revision: 1 };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function mockFetch(...responses: Array<Response | Error>) {
  const fetchMock = vi.spyOn(globalThis, "fetch");
  for (const response of responses) {
    if (response instanceof Error) fetchMock.mockRejectedValueOnce(response);
    else fetchMock.mockResolvedValueOnce(response);
  }
  return fetchMock;
}

test("shows saved tasks from the service", async () => {
  mockFetch(json({ tasks: [task("Read chapter 4", 1), task("Problem set 2", 2)] }));
  render(<App />);
  expect(await screen.findByText("Read chapter 4")).toBeInTheDocument();
  expect(screen.getByText("Problem set 2")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /saved tasks \(2\)/i })).toBeInTheDocument();
});

test("shows an empty state", async () => {
  mockFetch(json({ tasks: [] }));
  render(<App />);
  expect(await screen.findByText(/no tasks yet/i)).toBeInTheDocument();
});

test("adds a task with the keyboard, sends the trimmed title and keeps focus", async () => {
  const fetchMock = mockFetch(json({ tasks: [] }), json(task("Essay outline"), 201));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText(/no tasks yet/i);

  const input = screen.getByLabelText("Task title");
  await user.type(input, "  Essay outline  {Enter}");

  expect(await screen.findByText("Essay outline")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenLastCalledWith("/api/tasks", expect.objectContaining({ method: "POST" }));
  expect(JSON.parse(fetchMock.mock.lastCall![1]!.body as string)).toEqual({ title: "Essay outline" });
  expect(input).toHaveValue("");
  expect(input).toHaveFocus();
  expect(screen.getByRole("status")).toHaveTextContent("Saved “Essay outline”.");
});

test("disables Add task for a blank title", async () => {
  const fetchMock = mockFetch(json({ tasks: [] }));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText(/no tasks yet/i);

  const button = screen.getByRole("button", { name: "Add task" });
  expect(button).toBeDisabled();
  await user.type(screen.getByLabelText("Task title"), "   {Enter}");
  expect(button).toBeDisabled();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("keeps the typed title and shows the service's message when saving fails", async () => {
  mockFetch(
    json({ tasks: [] }),
    json({ error: { code: "invalid_input", field: "title", message: "Enter a task title." } }, 422),
  );
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText(/no tasks yet/i);

  await user.type(screen.getByLabelText("Task title"), "Lab report{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("Enter a task title.");
  expect(screen.getByLabelText("Task title")).toHaveValue("Lab report");
  expect(screen.getByRole("button", { name: "Add task" })).toBeEnabled();
});

test("counts characters like the service and blocks titles over the limit", async () => {
  const fetchMock = mockFetch(json({ tasks: [] }));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText(/no tasks yet/i);

  const input = screen.getByLabelText("Task title");
  await user.click(input);
  await user.paste("📚".repeat(200));
  expect(input).toHaveValue("📚".repeat(200));
  expect(screen.getByRole("button", { name: "Add task" })).toBeEnabled();

  await user.paste("x");
  expect(screen.getByText(/200 characters or fewer \(currently 201\)/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Add task" })).toBeDisabled();
  await user.keyboard("{Enter}");
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("a task saved while the first load is slow still appears (last list request wins)", async () => {
  let resolveSlow!: (response: Response) => void;
  const fetchMock = vi.spyOn(globalThis, "fetch");
  fetchMock
    .mockImplementationOnce(() => new Promise<Response>((resolve) => (resolveSlow = resolve)))
    .mockResolvedValueOnce(json(task("Lost task"), 201))
    .mockResolvedValueOnce(json({ tasks: [task("Lost task")] }));
  const user = userEvent.setup();
  render(<App />);

  await user.type(screen.getByLabelText("Task title"), "Lost task{Enter}");
  expect(await screen.findByText("Lost task", { selector: ".task-title" })).toBeInTheDocument();

  resolveSlow(json({ tasks: [] }));
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(screen.getByText("Lost task", { selector: ".task-title" })).toBeInTheDocument();
  expect(screen.queryByText(/no tasks yet/i)).not.toBeInTheDocument();
});

test("reports an unreachable service and recovers with Retry", async () => {
  mockFetch(new TypeError("Failed to fetch"), json({ tasks: [task("Recovered")] }));
  const user = userEvent.setup();
  render(<App />);

  expect(await screen.findByRole("alert")).toHaveTextContent(/cannot reach the bearplans service/i);
  await user.click(screen.getByRole("button", { name: "Retry" }));
  expect(await screen.findByText("Recovered")).toBeInTheDocument();
  await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
});
