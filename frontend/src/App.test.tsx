import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "./App";
import type { Project, Task } from "./api";

const MATH = "00000000-0000-4000-8000-00000000aaaa";
const CS = "00000000-0000-4000-8000-00000000bbbb";

function project(id: string, name: string, isDefault = false): Project {
  const at = "2026-10-14T16:00:00.000000Z";
  return { id, name, is_default: isDefault, created_at: at, updated_at: at, revision: 1 };
}

function task(id: string, title: string, over: Partial<Task> = {}): Task {
  const at = `2026-10-14T16:0${id.slice(-1)}:00.000000Z`;
  return {
    id,
    project_id: MATH,
    parent_id: null,
    title,
    notes: "",
    deadline: null,
    estimate_minutes: null,
    completed: false,
    completed_at: null,
    subtask_count: 0,
    completed_subtask_count: 0,
    created_at: at,
    updated_at: at,
    revision: 1,
    ...over,
  };
}

function taskList(tasks: Task[]) {
  const leaves = tasks.filter((t) => t.subtask_count === 0);
  return { tasks, progress: { completed: leaves.filter((t) => t.completed).length, total: leaves.length } };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

interface Call {
  url: string;
  method: string;
  body: Record<string, unknown> | undefined;
}

/**
 * A fake service routed by URL. Every mutation in the app triggers a refresh, so a
 * fixed response sequence would desynchronise as soon as the component changes.
 */
function fakeService(projects: Project[], tasks: Task[], fail?: { url: string; status: number; error: unknown }) {
  const calls: Call[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body = init?.body ? (JSON.parse(init.body as string) as Record<string, unknown>) : undefined;
    calls.push({ url, method, body });

    if (fail && url.startsWith(fail.url) && method !== "GET") return json({ error: fail.error }, fail.status);
    if (url === "/api/projects" && method === "GET") return json({ projects });
    if (url === "/api/projects" && method === "POST") {
      const created = project(CS, String(body!.name));
      projects.push(created);
      return json(created, 201);
    }
    if (url.startsWith("/api/projects/") && method === "PATCH") {
      projects[0] = { ...projects[0], name: String(body!.name), revision: 2 };
      return json(projects[0]);
    }
    if (url.startsWith("/api/tasks?") && method === "GET") {
      const id = new URL(url, "http://x").searchParams.get("project_id");
      return json(taskList(tasks.filter((t) => t.project_id === id)));
    }
    if (url === "/api/tasks" && method === "POST") {
      const created = task("00000000-0000-4000-8000-000000000009", String(body!.title), {
        parent_id: (body!.parent_id as string) ?? null,
      });
      tasks.push(created);
      return json(created, 201);
    }
    if (url.includes("/completion") && method === "PUT") {
      const id = url.split("/")[3];
      const index = tasks.findIndex((t) => t.id === id);
      tasks[index] = { ...tasks[index], completed: Boolean(body!.complete) };
      return json(tasks[index]);
    }
    if (url.startsWith("/api/tasks/") && method === "DELETE") {
      const id = url.split("/")[3];
      const index = tasks.findIndex((t) => t.id === id);
      const child = tasks.splice(index, 1)[0];
      const parent = tasks.find((t) => t.id === child.parent_id)!;
      parent.subtask_count = 0;
      parent.completed_subtask_count = 0;
      parent.completed = false;
      return json(parent);
    }
    if (url.startsWith("/api/tasks/") && method === "PATCH") {
      const id = url.split("/")[3];
      const index = tasks.findIndex((t) => t.id === id);
      tasks[index] = { ...tasks[index], ...(body as Partial<Task>), revision: 2 };
      return json(tasks[index]);
    }
    throw new Error(`unexpected ${method} ${url}`);
  });
  return calls;
}

test("lists projects, selects the first, and shows its tasks", async () => {
  fakeService([project(MATH, "Math 55", true)], [task("00000000-0000-4000-8000-000000000001", "Write PS7")]);
  render(<App />);
  expect(await screen.findByRole("button", { name: "Math 55", current: true })).toBeInTheDocument();
  expect(await screen.findByText("Write PS7")).toBeInTheDocument();
});

test("shows an empty state for a project with no tasks", async () => {
  fakeService([project(MATH, "Math 55", true)], []);
  render(<App />);
  expect(await screen.findByText(/no tasks in this project yet/i)).toBeInTheDocument();
});

test("adds a task to the selected project, sending a trimmed title", async () => {
  const calls = fakeService([project(MATH, "Math 55", true)], []);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText(/no tasks in this project yet/i);

  await user.type(screen.getByLabelText("Title"), "  Essay outline  ");
  await user.click(screen.getByRole("button", { name: "Add task" }));

  await waitFor(() => expect(calls.some((c) => c.url === "/api/tasks" && c.method === "POST")).toBe(true));
  const post = calls.find((c) => c.url === "/api/tasks" && c.method === "POST")!;
  expect(post.body).toMatchObject({ title: "Essay outline", project_id: MATH });
});

test("adds a subtask under its parent", async () => {
  const parent = task("00000000-0000-4000-8000-000000000001", "Write PS7");
  const calls = fakeService([project(MATH, "Math 55", true)], [parent]);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Write PS7");

  await user.click(screen.getByRole("button", { name: "Add subtask" }));
  // Two Title fields are now on screen: the add-task form and the new subtask form.
  await user.type(screen.getAllByLabelText("Title").at(-1)!, "read ch.4");
  await user.click(screen.getAllByRole("button", { name: "Add subtask" }).at(-1)!);

  await waitFor(() => expect(calls.some((c) => c.method === "POST" && c.body?.parent_id === parent.id)).toBe(true));
});

test("a task with subtasks shows progress and cannot be completed directly", async () => {
  const parent = task("00000000-0000-4000-8000-000000000001", "Write PS7", {
    subtask_count: 2,
    completed_subtask_count: 1,
  });
  const child = task("00000000-0000-4000-8000-000000000002", "read ch.4", { parent_id: parent.id, completed: true });
  fakeService([project(MATH, "Math 55", true)], [parent, child]);
  render(<App />);

  await screen.findByText("Write PS7");
  expect(screen.getByText("1 of 2 subtasks done")).toBeInTheDocument();
  expect(screen.getByLabelText("Write PS7")).toBeDisabled();
  expect(screen.getByLabelText("read ch.4")).toBeEnabled();
});

test("completing a subtask calls the completion endpoint", async () => {
  const parent = task("00000000-0000-4000-8000-000000000001", "Write PS7", { subtask_count: 1 });
  const child = task("00000000-0000-4000-8000-000000000002", "read ch.4", { parent_id: parent.id });
  const calls = fakeService([project(MATH, "Math 55", true)], [parent, child]);
  const user = userEvent.setup();
  render(<App />);

  await user.click(await screen.findByLabelText("read ch.4"));
  await waitFor(() =>
    expect(calls.some((c) => c.url.endsWith(`/${child.id}/completion`) && c.body?.complete === true)).toBe(true),
  );
});

test("editing a task sends its changed fields", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Write PS7");
  const calls = fakeService([project(MATH, "Math 55", true)], [existing]);
  const user = userEvent.setup();
  render(<App />);

  await user.click(await screen.findByRole("button", { name: "Edit" }));
  const estimate = screen.getAllByLabelText("Estimate (minutes)").at(-1)!;
  await user.clear(estimate);
  await user.type(estimate, "90");
  await user.click(screen.getAllByRole("button", { name: "Save changes" }).at(-1)!);

  await waitFor(() => expect(calls.some((c) => c.method === "PATCH" && c.url.includes("/api/tasks/"))).toBe(true));
  const patch = calls.find((c) => c.method === "PATCH" && c.url.includes("/api/tasks/"))!;
  expect(patch.body).toMatchObject({ title: "Write PS7", estimate_minutes: 90 });
});

test("a rejected save shows the service's message and keeps what was typed", async () => {
  // The service is the authority on its rules, and the form cannot anticipate all of
  // them: a title of only invisible characters passes HTML's required check and is
  // still rejected once trimmed. The typed text must survive so it can be corrected.
  fakeService([project(MATH, "Math 55", true)], [], {
    url: "/api/tasks",
    status: 422,
    error: { code: "invalid_input", field: "title", message: "Enter a task title." },
  });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText(/no tasks in this project yet/i);

  await user.type(screen.getByLabelText("Title"), "Essay outline");
  await user.click(screen.getByRole("button", { name: "Add task" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("Enter a task title.");
  expect(screen.getByLabelText("Title")).toHaveValue("Essay outline");
});

test("the estimate field refuses an out-of-range value before it reaches the service", async () => {
  const calls = fakeService([project(MATH, "Math 55", true)], []);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText(/no tasks in this project yet/i);

  await user.type(screen.getByLabelText("Title"), "Essay outline");
  await user.type(screen.getByLabelText("Estimate (minutes)"), "0");
  await user.click(screen.getByRole("button", { name: "Add task" }));

  // min=1 fails the browser's own constraint check, so nothing is sent at all.
  // The service still enforces the same rule; see tests/test_tasks.py.
  await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(false));
  expect(screen.getByLabelText("Title")).toHaveValue("Essay outline");
});

test("adding a project selects it", async () => {
  fakeService([project(MATH, "Math 55", true)], []);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByRole("button", { name: "Math 55", current: true });

  await user.type(screen.getByLabelText("New project"), "CS 61A");
  await user.click(screen.getByRole("button", { name: "Add project" }));

  expect(await screen.findByRole("button", { name: "CS 61A", current: true })).toBeInTheDocument();
});

test("renaming a project keeps its tasks", async () => {
  fakeService([project(MATH, "Math 55", true)], [task("00000000-0000-4000-8000-000000000001", "Write PS7")]);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Write PS7");

  await user.click(screen.getByRole("button", { name: /rename/i }));
  const field = screen.getByLabelText(/rename/i);
  await user.clear(field);
  await user.type(field, "Math 55 - Honors");
  await user.click(screen.getByRole("button", { name: "Save name" }));

  expect(await screen.findByRole("button", { name: "Math 55 - Honors", current: true })).toBeInTheDocument();
  expect(screen.getByText("Write PS7")).toBeInTheDocument();
});

test("a failed projects load reports the problem and can be retried", async () => {
  let attempt = 0;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url === "/api/projects") {
      attempt += 1;
      if (attempt === 1) throw new TypeError("Failed to fetch");
      return json({ projects: [project(MATH, "Math 55", true)] });
    }
    return json(taskList([]));
  });
  const user = userEvent.setup();
  render(<App />);

  // Without a project there is no tasks section, so an error reported only there
  // would leave the page blank and silent.
  expect(await screen.findByRole("alert")).toHaveTextContent(/cannot reach the bearplans service/i);

  await user.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByRole("button", { name: "Math 55", current: true })).toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("adding a project closes an open rename form instead of retargeting it", async () => {
  const calls = fakeService([project(MATH, "Math 55", true)], []);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByRole("button", { name: "Math 55", current: true });

  await user.click(screen.getByRole("button", { name: /rename/i }));
  expect(screen.getByLabelText(/rename/i)).toHaveValue("Math 55");

  await user.type(screen.getByLabelText("New project"), "CS 61A");
  await user.click(screen.getByRole("button", { name: "Add project" }));
  await screen.findByRole("button", { name: "CS 61A", current: true });

  // The open form belonged to Math 55. Left mounted it would rename the brand-new
  // project to "Math 55", producing two projects of the same name.
  expect(screen.queryByRole("button", { name: "Save name" })).not.toBeInTheDocument();
  expect(calls.some((c) => c.method === "PATCH" && c.url.includes("/api/projects/"))).toBe(false);
});

test("a mutation resolving after a project switch does not show the old project's tasks", async () => {
  const mathTask = task("00000000-0000-4000-8000-000000000001", "Write PS7");
  const csTask = task("00000000-0000-4000-8000-000000000002", "Lab 3", { project_id: CS });
  let releaseCompletion: () => void = () => {};
  const held = new Promise<void>((resolve) => {
    releaseCompletion = resolve;
  });

  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url === "/api/projects")
      return json({ projects: [project(MATH, "Math 55", true), project(CS, "CS 61A")] });
    if (url.includes("/completion")) {
      await held; // still in flight while the user switches project
      return json({ ...mathTask, completed: true });
    }
    const id = new URL(url, "http://x").searchParams.get("project_id");
    return json(taskList([mathTask, csTask].filter((t) => t.project_id === id)));
  });

  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Write PS7");

  await user.click(screen.getByLabelText("Write PS7")); // PUT hangs
  await user.click(screen.getByRole("button", { name: "CS 61A" }));
  await screen.findByText("Lab 3");

  releaseCompletion();

  // The late refresh must not install Math 55's tasks under the CS 61A heading.
  await waitFor(() => expect(screen.getByRole("heading", { name: "CS 61A" })).toBeInTheDocument());
  expect(screen.getByText("Lab 3")).toBeInTheDocument();
  expect(screen.queryByText("Write PS7")).not.toBeInTheDocument();
});

test("Try again refetches the tasks, not only the projects", async () => {
  let taskAttempt = 0;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url === "/api/projects") return json({ projects: [project(MATH, "Math 55", true)] });
    taskAttempt += 1;
    if (taskAttempt === 1) throw new TypeError("Failed to fetch");
    return json(taskList([task("00000000-0000-4000-8000-000000000001", "Write PS7")]));
  });
  const user = userEvent.setup();
  render(<App />);

  expect(await screen.findByRole("alert")).toHaveTextContent(/cannot reach the bearplans service/i);
  await user.click(screen.getByRole("button", { name: "Try again" }));

  // Selecting the same project again does not re-run the load effect, so a retry that
  // only reloaded projects would leave the list stuck on "Loading…" forever.
  expect(await screen.findByText("Write PS7")).toBeInTheDocument();
  expect(screen.queryByText("Loading…")).not.toBeInTheDocument();
});


test("shows the service's leaf work total without counting the parent", async () => {
  const parent = task("00000000-0000-4000-8000-000000000001", "Container", { subtask_count: 1, completed_subtask_count: 1, completed: true });
  const child = task("00000000-0000-4000-8000-000000000002", "Done", { parent_id: parent.id, completed: true });
  fakeService([project(MATH, "Math 55", true)], [parent, child, task("00000000-0000-4000-8000-000000000003", "Standalone")]);
  render(<App />);
  expect(await screen.findByText("1 of 2 work items complete")).toBeInTheDocument();
});


test("removal needs an explicit action and restores parent completion control", async () => {
  const parent = task("00000000-0000-4000-8000-000000000001", "Container", { subtask_count: 1, completed_subtask_count: 1, completed: true });
  const child = task("00000000-0000-4000-8000-000000000002", "Done", { parent_id: parent.id, completed: true });
  const calls = fakeService([project(MATH, "Math 55", true)], [parent, child]);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Done");
  await user.click(screen.getAllByRole("button", { name: /^Edit$/ })[1]);
  await user.click(screen.getByRole("button", { name: "Remove subtask" }));
  expect(calls.some((c) => c.method === "DELETE")).toBe(false);
  expect(screen.getByText(/removing the last subtask leaves its parent incomplete/i)).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Keep subtask" }));
  expect(screen.queryByRole("button", { name: "Confirm removal" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Remove subtask" }));
  await user.click(screen.getByRole("button", { name: "Confirm removal" }));
  await waitFor(() => expect(screen.queryByLabelText("Done")).not.toBeInTheDocument());
  expect(screen.getByLabelText("Container")).toBeEnabled();
  expect(screen.getByLabelText("Container")).not.toBeChecked();
  expect(screen.getByText("0 of 1 work items complete")).toBeInTheDocument();
});


test("a storage save error keeps the edit available for correction or retry", async () => {
  fakeService([project(MATH, "Math 55", true)], [task("00000000-0000-4000-8000-000000000001", "Keep")], {
    url: "/api/tasks",
    status: 503,
    error: { code: "storage_unavailable", message: "Check disk space and folder permissions, then try again." },
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: /^Edit$/ }));
  const field = screen.getAllByLabelText("Title").at(-1)!;
  await user.clear(field);
  await user.type(field, "Changed");
  await user.click(screen.getByRole("button", { name: "Save changes" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Check disk space");
  expect(field).toHaveValue("Changed");
  expect(screen.getByLabelText("Keep")).toBeInTheDocument();
});
