import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "./App";
import type { Placement, Project, Task } from "./api";
import { addDays } from "./WeeklyPlanner";

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

function planningSnapshot(tasks: Task[], placements: Placement[] = [], query = "") {
  const requested = new URL(query || "/api/planning", "http://x").searchParams.get("week") || "2026-10-15";
  const date = new Date(`${requested}T00:00:00Z`);
  const weekStart = addDays(requested, -((date.getUTCDay() + 6) % 7));
  return { today: "2026-10-15", timezone: "America/Los_Angeles", week_start: weekStart, week_end: addDays(weekStart, 6), tasks, placements };
}

function placement(id: string, taskId: string, date: string): Placement {
  const at = "2026-10-15T16:00:00.000000Z";
  return { id, task_id: taskId, planned_date: date, created_at: at, updated_at: at, revision: 1 };
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
function fakeService(projects: Project[], tasks: Task[], fail?: { url: string; status: number; error: unknown }, placements: Placement[] = []) {
  const calls: Call[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body = init?.body ? (JSON.parse(init.body as string) as Record<string, unknown>) : undefined;
    calls.push({ url, method, body });

    if (url === "/api/timer") return json({ server_now: "2026-10-16T16:00:00.000000Z", active_session: null, last_session: null });
    if (url === "/api/forest") return json({ trees: [] });
    if (url === "/api/shop") return json({ balance: 0, coins_per_minute: 1, species: [{ id: "pine", name: "Pine", price: 0, owned: true }], recent_entries: [] });

    if (fail && url.startsWith(fail.url) && method !== "GET") return json({ error: fail.error }, fail.status);
    if (url.startsWith("/api/planning") && method === "GET") return json(planningSnapshot(tasks, placements, url));
    if (url === "/api/placements" && method === "POST") {
      const existing = placements.find((p) => p.task_id === body!.task_id && p.planned_date === body!.planned_date);
      if (existing) {
        return json({ error: { code: "placement_conflict", message: `This task is already planned for ${existing.planned_date}. Choose another day. No records were changed.` } }, 409);
      }
      const created = placement(`placement-${placements.length + 1}`, String(body!.task_id), String(body!.planned_date));
      placements.push(created);
      return json(created, 201);
    }
    if (url.startsWith("/api/placements/") && method === "PATCH") {
      const existing = placements.find((p) => p.id === url.split("/")[3])!;
      if (placements.some((p) => p.id !== existing.id && p.task_id === existing.task_id && p.planned_date === body!.planned_date)) {
        return json({ error: { code: "placement_conflict", message: "This task is already planned for that day. No placements were changed." } }, 409);
      }
      existing.planned_date = String(body!.planned_date);
      return json(existing);
    }
    if (url.startsWith("/api/placements/") && method === "DELETE") {
      const index = placements.findIndex((p) => p.id === url.split("/")[3]);
      return json({ removed: placements.splice(index, 1)[0].id });
    }
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

test("finishing a child save preserves a different editor opened while it was pending", async () => {
  const parent = task("00000000-0000-4000-8000-000000000001", "Prepare seminar", { subtask_count: 1 });
  const child = task("00000000-0000-4000-8000-000000000002", "Read chapter", { parent_id: parent.id });
  fakeService([project(MATH, "Math 55", true)], [parent, child]);
  const original = vi.mocked(fetch).getMockImplementation()!;
  let finishSave!: () => void;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input) === `/api/tasks/${child.id}` && init?.method === "PATCH") await new Promise<void>((resolve) => { finishSave = resolve; });
    return original(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  const childRow = (await screen.findByLabelText(child.title)).closest("li")!;
  await user.click(within(childRow).getByRole("button", { name: "Edit" }));
  await user.click(screen.getByRole("button", { name: "Save changes" }));
  const parentRow = screen.getByLabelText(parent.title).closest("li")!;
  await user.click(within(parentRow).getByRole("button", { name: "Edit" }));
  const parentTitle = screen.getAllByLabelText("Title").at(-1)!;
  await user.clear(parentTitle);
  await user.type(parentTitle, "Seminar draft still open");
  await act(async () => finishSave());
  await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Changes saved."));
  expect(screen.getAllByLabelText("Title").at(-1)).toHaveValue("Seminar draft still open");
  expect(screen.getByRole("button", { name: "Save changes" })).toBeEnabled();
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
    if (url === "/api/timer") return json({ server_now: "2026-10-16T16:00:00.000000Z", active_session: null, last_session: null });
    if (url.startsWith("/api/planning")) return json(planningSnapshot([], [], url));
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
    if (url === "/api/timer") return json({ server_now: "2026-10-16T16:00:00.000000Z", active_session: null, last_session: null });
    if (url.startsWith("/api/planning")) return json(planningSnapshot([], [], url));
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
    if (url === "/api/timer") return json({ server_now: "2026-10-16T16:00:00.000000Z", active_session: null, last_session: null });
    if (url.startsWith("/api/planning")) return json(planningSnapshot([], [], url));
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

function taskPlanner(title: string) {
  return within(screen.getByRole("checkbox", { name: title }).closest(".task-row")!.querySelector(".task-main") as HTMLElement);
}

function board() {
  return within(screen.getByRole("region", { name: "Weekly plan" }));
}

test("the server defines Today and the board spans Monday through Sunday across year boundaries", async () => {
  const calls = fakeService([project(MATH, "Math 55", true)], []);
  const user = userEvent.setup();
  render(<App />);
  expect(await screen.findByText("Today is Oct 15, 2026 · America/Los_Angeles")).toBeInTheDocument();
  expect(board().getByRole("region", { name: "Monday, Oct 12, 2026" })).toBeInTheDocument();
  expect(board().getByRole("region", { name: "Sunday, Oct 18, 2026" })).toBeInTheDocument();
  await user.click(board().getByRole("button", { name: "Next week" }));
  expect(await screen.findByRole("region", { name: "Monday, Oct 19, 2026" })).toBeInTheDocument();
  await user.click(board().getByRole("button", { name: "Previous week" }));
  await screen.findByRole("region", { name: "Monday, Oct 12, 2026" });
  await user.click(board().getByRole("button", { name: "Today" }));
  expect(calls.filter((call) => call.url === "/api/planning")).toHaveLength(2);
  expect(addDays("2026-12-28", 6)).toBe("2027-01-03");
  expect(addDays("2027-01-04", -7)).toBe("2026-12-28");
  expect(addDays("2026-03-08", 1)).toBe("2026-03-09");
});

test("assigning existing leaf work preserves its fields and replaces assignment with keyboard move controls", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Problem set", { deadline: "2026-10-20", notes: "Keep my notes", estimate_minutes: 60 });
  const placements: Placement[] = [];
  const calls = fakeService([project(MATH, "Math 55", true)], [existing], undefined, placements);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByLabelText("Problem set");
  await user.click(taskPlanner("Problem set").getByText("Plan task"));
  const date = taskPlanner("Problem set").getByLabelText("Planned date for “Problem set”");
  fireEvent.change(date, { target: { value: "2026-10-16" } });
  await user.click(taskPlanner("Problem set").getByRole("button", { name: "Add to day" }));
  expect(await board().findByLabelText("Problem set, planned Oct 16, 2026")).toBeInTheDocument();
  expect(board().queryByText("Planned Oct 16, 2026")).not.toBeInTheDocument();
  expect(board().getByText("Due Oct 20, 2026")).toBeInTheDocument();
  expect(placements).toHaveLength(1);
  expect(placements[0].task_id).toBe(existing.id);
  expect(existing).toMatchObject({ notes: "Keep my notes", deadline: "2026-10-20", estimate_minutes: 60, revision: 1 });
  expect(calls.some((call) => call.url.startsWith("/api/tasks") && call.method !== "GET")).toBe(false);
  expect(taskPlanner("Problem set").getByText("Planned: Oct 16, 2026")).toBeInTheDocument();
  expect(taskPlanner("Problem set").getByText("Move or remove plan")).toBeInTheDocument();
  expect(taskPlanner("Problem set").queryByText("Add another planned day")).not.toBeInTheDocument();
  expect(taskPlanner("Problem set").queryByLabelText("Planned date for “Problem set”")).not.toBeInTheDocument();
  expect(taskPlanner("Problem set").getByRole("button", { name: "Move placement" })).toBeDisabled();
  expect(calls.filter((call) => call.url === "/api/placements" && call.method === "POST")).toHaveLength(1);
  expect(placements).toHaveLength(1);
});

test("a stale assignment form rejects an already occupied date and keeps both records unchanged", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Read");
  const placements: Placement[] = [];
  fakeService([project(MATH, "Math 55", true)], [existing], undefined, placements);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByLabelText("Read");
  await user.click(taskPlanner("Read").getByText("Plan task"));
  const date = taskPlanner("Read").getByLabelText("Planned date for “Read”");
  fireEvent.change(date, { target: { value: "2026-10-17" } });
  // Another tab has saved this destination since this view loaded.
  placements.push(placement("p1", existing.id, "2026-10-17"));
  await user.click(taskPlanner("Read").getByRole("button", { name: "Add to day" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("already planned for 2026-10-17");
  expect(screen.getByRole("alert")).toHaveTextContent("Choose another day");
  expect(date).toHaveValue("2026-10-17");
  expect(placements).toEqual([placement("p1", existing.id, "2026-10-17")]);
  expect(existing.revision).toBe(1);
});

test("parents are context; only leaves get assignment controls", async () => {
  const parent = task("00000000-0000-4000-8000-000000000001", "Homework", { subtask_count: 1 });
  const child = task("00000000-0000-4000-8000-000000000002", "Problem 1", { parent_id: parent.id });
  fakeService([project(MATH, "Math 55", true)], [parent, child], undefined, [placement("p1", child.id, "2026-10-15")]);
  render(<App />);
  await screen.findByLabelText("Homework");
  expect(taskPlanner("Homework").queryByText("Plan task")).not.toBeInTheDocument();
  expect(taskPlanner("Homework").getByText("Plan the subtasks below.")).toBeInTheDocument();
  expect(taskPlanner("Problem 1").getByText("Move or remove plan")).toBeInTheDocument();
  expect(taskPlanner("Problem 1").queryByText("Add another planned day")).not.toBeInTheDocument();
  expect(await board().findByText("Math 55 / Homework")).toBeInTheDocument();
});

test("moving across weeks keeps one planned day, preserves the task and leaves other tasks unchanged", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Read");
  const other = task("00000000-0000-4000-8000-000000000002", "Write");
  const originalTask = { ...existing };
  const placements = [placement("p1", existing.id, "2026-10-15"), placement("p2", other.id, "2026-10-16")];
  const calls = fakeService([project(MATH, "Math 55", true)], [existing, other], undefined, placements);
  const user = userEvent.setup();
  render(<App />);
  await board().findByLabelText("Read, planned Oct 15, 2026");
  const thursday = within(board().getByRole("region", { name: "Thursday, Oct 15, 2026" }));
  await user.click(thursday.getByText("Move or remove"));
  fireEvent.change(thursday.getByLabelText("Move “Read” from Oct 15, 2026 to"), { target: { value: "2026-10-23" } });
  await user.click(thursday.getByRole("button", { name: "Move placement" }));
  await waitFor(() => expect(placements[0].planned_date).toBe("2026-10-23"));
  expect(placements[1].planned_date).toBe("2026-10-16");
  expect(placements.filter((p) => p.task_id === existing.id)).toHaveLength(1);
  expect(placements[0].id).toBe("p1");
  expect(existing).toEqual(originalTask);
  expect(calls.find((call) => call.method === "PATCH")?.url).toBe("/api/placements/p1");
  expect(await taskPlanner("Read").findByText("Planned: Oct 23, 2026")).toBeInTheDocument();
  await user.click(taskPlanner("Read").getByText("Move or remove plan"));
  expect(taskPlanner("Read").queryByText("Add another planned day")).not.toBeInTheDocument();
  expect(taskPlanner("Read").getByLabelText("Move “Read” from Oct 23, 2026 to")).toHaveValue("2026-10-23");
  await user.click(board().getByRole("button", { name: "Next week" }));
  expect(await board().findByLabelText("Read, planned Oct 23, 2026")).toBeInTheDocument();
  expect(board().queryByLabelText("Write, planned Oct 16, 2026")).not.toBeInTheDocument();
  await user.click(board().getByRole("button", { name: "Previous week" }));
  expect(await board().findByLabelText("Write, planned Oct 16, 2026")).toBeInTheDocument();
  expect(board().queryByLabelText("Read, planned Oct 15, 2026")).not.toBeInTheDocument();
});

test("a failed move preserves the existing plan and the attempted destination for retry", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Read");
  const placements = [placement("p1", existing.id, "2026-10-15")];
  fakeService([project(MATH, "Math 55", true)], [existing], { url: "/api/placements", status: 503, error: { code: "storage_unavailable", message: "Check disk space, then try again. No records were changed." } }, placements);
  const user = userEvent.setup();
  render(<App />);
  await board().findByLabelText("Read, planned Oct 15, 2026");
  const thursday = within(board().getByRole("region", { name: "Thursday, Oct 15, 2026" }));
  await user.click(thursday.getByText("Move or remove"));
  const date = thursday.getByLabelText("Move “Read” from Oct 15, 2026 to");
  fireEvent.change(date, { target: { value: "2026-10-16" } });
  await user.click(thursday.getByRole("button", { name: "Move placement" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Check disk space, then try again. No records were changed.");
  expect(date).toHaveValue("2026-10-16");
  expect(thursday.getByRole("button", { name: "Move placement" })).toBeEnabled();
  expect(placements).toEqual([placement("p1", existing.id, "2026-10-15")]);
});

test("removing a placement keeps its task accessible and never calls task deletion", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Keep this task");
  const placements = [placement("p1", existing.id, "2026-10-15")];
  const calls = fakeService([project(MATH, "Math 55", true)], [existing], undefined, placements);
  const user = userEvent.setup();
  render(<App />);
  await board().findByLabelText("Keep this task, planned Oct 15, 2026");
  const thursday = within(board().getByRole("region", { name: "Thursday, Oct 15, 2026" }));
  await user.click(thursday.getByText("Move or remove"));
  await user.click(thursday.getByRole("button", { name: "Remove from plan" }));
  expect(await taskPlanner("Keep this task").findByText("Unscheduled")).toBeInTheDocument();
  expect(screen.getByLabelText("Keep this task")).toBeInTheDocument();
  expect(placements).toHaveLength(0);
  expect(calls.filter((call) => call.method === "DELETE").map((call) => call.url)).toEqual(["/api/placements/p1"]);
});

test("task completion stays consistent between its project list and its single planned day", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Read");
  fakeService([project(MATH, "Math 55", true)], [existing], undefined, [placement("p1", existing.id, "2026-10-15")]);
  const user = userEvent.setup();
  render(<App />);
  await user.click(await board().findByLabelText("Read, planned Oct 15, 2026"));
  await waitFor(() => expect(screen.getByRole("checkbox", { name: "Read" })).toBeChecked());
  expect(board().getByLabelText("Read, planned Oct 15, 2026")).toBeChecked();
  await user.click(screen.getByRole("checkbox", { name: "Read" }));
  await waitFor(() => expect(board().getByLabelText("Read, planned Oct 15, 2026")).not.toBeChecked());
});

test("failed placement saves retain the selected date and explain how to retry", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Read");
  fakeService([project(MATH, "Math 55", true)], [existing], { url: "/api/placements", status: 503, error: { code: "storage_unavailable", message: "Check disk space, then try again." } });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByLabelText("Read");
  await user.click(taskPlanner("Read").getByText("Plan task"));
  const date = taskPlanner("Read").getByLabelText("Planned date for “Read”");
  fireEvent.change(date, { target: { value: "2026-11-20" } });
  await user.click(taskPlanner("Read").getByRole("button", { name: "Add to day" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Check disk space");
  expect(date).toHaveValue("2026-11-20");
  expect(taskPlanner("Read").getByRole("button", { name: "Add to day" })).toBeEnabled();
});

test("selected-day controls change the day rendered in the narrow-window layout", async () => {
  fakeService([project(MATH, "Math 55", true)], []);
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Today is Oct 15, 2026 · America/Los_Angeles");
  const selector = within(board().getByRole("group", { name: "Selected day" }));
  await user.click(selector.getByRole("button", { name: /FriOct 16/ }));
  expect(selector.getByRole("button", { name: /FriOct 16/ })).toHaveAttribute("aria-pressed", "true");
  expect(board().getByRole("region", { name: "Friday, Oct 16, 2026" })).toHaveClass("day-selected");
  expect(board().getByRole("region", { name: "Thursday, Oct 15, 2026" })).not.toHaveClass("day-selected");
});

test("a successful save with a failed readback is reported as saved and refresh can be retried without a second write", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Read");
  const calls = fakeService([project(MATH, "Math 55", true)], [existing], undefined, [placement("p1", existing.id, "2026-10-15")]);
  const original = vi.mocked(fetch).getMockImplementation()!;
  let failReadback = false;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.startsWith("/api/planning") && failReadback) {
      failReadback = false;
      throw new TypeError("network interrupted after save");
    }
    const response = await original(input, init);
    if (url.endsWith("/completion")) failReadback = true;
    return response;
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await board().findByLabelText("Read, planned Oct 15, 2026"));
  expect(await screen.findByRole("alert")).toHaveTextContent("Cannot reach");
  expect(screen.getByRole("status")).toHaveTextContent("Saved. Some views could not refresh.");
  expect(screen.getByRole("checkbox", { name: "Read" })).toBeDisabled();
  await user.click(board().getByRole("button", { name: "Retry weekly plan" }));
  await waitFor(() => expect(board().getByLabelText("Read, planned Oct 15, 2026")).toBeChecked());
  expect(screen.getByRole("checkbox", { name: "Read" })).toBeEnabled();
  expect(calls.filter((call) => call.url.endsWith("/completion"))).toHaveLength(1);
});

test("retrying a failed Next navigation keeps its requested week instead of silently reloading the old week", async () => {
  fakeService([project(MATH, "Math 55", true)], []);
  const original = vi.mocked(fetch).getMockImplementation()!;
  let nextAttempts = 0;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input) === "/api/planning?week=2026-10-19") {
      nextAttempts += 1;
      if (nextAttempts === 1) throw new TypeError("offline");
    }
    return original(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByRole("region", { name: "Monday, Oct 12, 2026" });
  await user.click(board().getByRole("button", { name: "Next week" }));
  await screen.findByRole("alert");
  expect(board().getByRole("region", { name: "Monday, Oct 12, 2026" })).toBeInTheDocument();
  await user.click(board().getByRole("button", { name: "Retry weekly plan" }));
  expect(await board().findByRole("region", { name: "Monday, Oct 19, 2026" })).toBeInTheDocument();
  expect(nextAttempts).toBe(2);
});

test("retrying a failed Today navigation asks the service for current Today again", async () => {
  fakeService([project(MATH, "Math 55", true)], []);
  const original = vi.mocked(fetch).getMockImplementation()!;
  let todayRequests = 0;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input) === "/api/planning") {
      todayRequests += 1;
      if (todayRequests === 2) throw new TypeError("offline");
    }
    return original(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByRole("region", { name: "Monday, Oct 12, 2026" });
  await user.click(board().getByRole("button", { name: "Next week" }));
  await screen.findByRole("region", { name: "Monday, Oct 19, 2026" });
  await user.click(board().getByRole("button", { name: "Today" }));
  await screen.findByRole("alert");
  await user.click(board().getByRole("button", { name: "Retry weekly plan" }));
  expect(await board().findByRole("region", { name: "Monday, Oct 12, 2026" })).toBeInTheDocument();
  expect(todayRequests).toBe(3);
});

test("a mutation during slow week navigation refreshes the requested week and ignores the stale response", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Read");
  fakeService([project(MATH, "Math 55", true)], [existing]);
  const original = vi.mocked(fetch).getMockImplementation()!;
  let nextRequests = 0;
  let release: () => void = () => {};
  const hold = new Promise<void>((resolve) => { release = resolve; });
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input) === "/api/planning?week=2026-10-19") {
      nextRequests += 1;
      if (nextRequests === 1) {
        await hold;
        // Simulate an out-of-order service response even if fetch ignores abort.
        return json(planningSnapshot([], [], "/api/planning?week=2026-10-12"));
      }
    }
    return original(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByRole("region", { name: "Monday, Oct 12, 2026" });
  await user.click(board().getByRole("button", { name: "Next week" }));
  await user.click(screen.getByRole("checkbox", { name: "Read" }));
  expect(await board().findByRole("region", { name: "Monday, Oct 19, 2026" })).toBeInTheDocument();
  expect(nextRequests).toBe(2);
  release();
  await waitFor(() => expect(screen.getByRole("checkbox", { name: "Read" })).toBeChecked());
  expect(board().getByRole("region", { name: "Monday, Oct 19, 2026" })).toBeInTheDocument();
});


test("existing multiple dates remain editable without Add controls and synchronize completion", async () => {
  const existing = task("00000000-0000-4000-8000-000000000001", "Read", { deadline: "2026-10-20", notes: "Keep notes" });
  const original = { ...existing };
  const placements = [placement("p1", existing.id, "2026-10-15"), placement("p2", existing.id, "2026-10-16")];
  const calls = fakeService([project(MATH, "Math 55", true)], [existing], undefined, placements);
  const user = userEvent.setup();
  render(<App />);
  await board().findByLabelText("Read, planned Oct 15, 2026");
  await screen.findByRole("checkbox", { name: "Read" });
  await user.click(taskPlanner("Read").getByText("Move or remove plan"));
  expect(screen.queryByText("Add another planned day")).not.toBeInTheDocument();
  expect(taskPlanner("Read").queryByRole("button", { name: "Add to day" })).not.toBeInTheDocument();
  const sourceActions = within(taskPlanner("Read").getByLabelText("Move “Read” from Oct 15, 2026 to").closest("form")!);
  fireEvent.change(sourceActions.getByLabelText("Move “Read” from Oct 15, 2026 to"), { target: { value: "2026-10-17" } });
  await user.click(sourceActions.getByRole("button", { name: "Move placement" }));
  expect(await board().findByLabelText("Read, planned Oct 17, 2026")).toBeInTheDocument();
  expect(board().getByLabelText("Read, planned Oct 16, 2026")).toBeInTheDocument();
  expect(placements).toHaveLength(2);
  expect(placements[0]).toEqual(placement("p1", existing.id, "2026-10-17"));
  expect(placements[1]).toEqual(placement("p2", existing.id, "2026-10-16"));
  expect(existing).toEqual(original);
  expect(board().getByText("Weekly completion: 0 of 1 work items complete (0%).")).toBeInTheDocument();
  expect(calls.filter((call) => call.method !== "GET").map((call) => call.url)).toEqual(["/api/placements/p1"]);
  await user.click(board().getByLabelText("Read, planned Oct 16, 2026"));
  await waitFor(() => expect(board().getByLabelText("Read, planned Oct 17, 2026")).toBeChecked());
  expect(board().getByLabelText("Read, planned Oct 16, 2026")).toBeChecked();
  expect(board().getByText("Weekly completion: 1 of 1 work items complete (100%).")).toBeInTheDocument();
});
