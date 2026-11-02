import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { BCourses } from "./BCourses";
import type { BCoursesAssignment, BCoursesState } from "./api";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const item = (over: Partial<BCoursesAssignment>): BCoursesAssignment => ({
  assignment_id: "11", course_id: "1", course_name: "MATH 54", title: "Problem set 5", due_at: "2099-11-07T07:59:00Z",
  due_date: "2099-11-06", html_url: "https://bcourses.berkeley.edu/courses/1/assignments/11", points_possible: 10,
  in_source: true, status: "new", task_id: null, due_changed: false, accepted_due_date: null, ...over,
});
const state = (over: Partial<BCoursesState> = {}): BCoursesState => ({
  configured: true, sync: { last_attempt_at: "2026-11-01T10:00:00Z", last_success_at: "2026-11-01T10:00:00Z", last_error: null },
  courses: [
    { course_id: "1", name: "MATH 54", course_code: "MATH 54", term: "Fall 2026", followed: true, in_source: true, project_id: null },
    { course_id: "2", name: "Old club", course_code: "CLUB", term: "", followed: false, in_source: true, project_id: null },
  ],
  assignments: [
    item({}),
    item({ assignment_id: "12", title: "Reading reflection", due_at: null, due_date: null, html_url: "" }),
    item({ assignment_id: "13", title: "Quiz 1", due_at: "2020-01-01T07:59:00Z", due_date: "2019-12-31" }),
    item({ assignment_id: "14", title: "Midterm review", status: "added", task_id: "t14", due_changed: true,
      due_date: "2099-11-09", accepted_due_date: "2099-11-06" }),
  ], ...over,
});

test("lists upcoming, undated and past assignments separately and links to bCourses", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json(state()));
  render(<BCourses visible />);
  const upcoming = within(await screen.findByRole("list", { name: "Upcoming assignments" }));
  expect(upcoming.getByText("Problem set 5")).toBeVisible();
  expect(upcoming.getByRole("link", { name: "Open in bCourses" })).toHaveAttribute("rel", "noreferrer noopener");
  expect(upcoming.getByText(/10 pts/)).toBeVisible();
  const undated = within(screen.getByRole("list", { name: "Assignments with no due date" }));
  expect(undated.getByText(/^No due date/)).toBeVisible();
  expect(undated.queryByRole("link")).toBeNull();
  expect(screen.getByText("Past due, not added (1)")).toBeInTheDocument();
  const changed = within(screen.getByRole("list", { name: "Due date changed" }));
  expect(changed.getByText(/Your task: .*Nov 6 → bCourses: .*Nov 9/)).toBeVisible();
});

test("Add creates the task, reports where it went and refreshes the app", async () => {
  const addedState = state({ assignments: [item({ status: "added", task_id: "t11" })] });
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(json(state()))
    .mockResolvedValueOnce(json({ assignment: addedState.assignments[0], task: { title: "Problem set 5", deadline: "2099-11-06" }, project_created: true }))
    .mockResolvedValueOnce(json(addedState));
  const changed = vi.fn();
  const user = userEvent.setup();
  render(<BCourses visible onChanged={changed} />);
  await user.click(await screen.findByRole("button", { name: "Add “Problem set 5” as a task" }));
  expect(await screen.findByRole("status")).toHaveTextContent("Added “Problem set 5” to MATH 54, due");
  expect(fetcher.mock.calls[1][0]).toBe("/api/bcourses/assignments/11/add");
  expect((fetcher.mock.calls[1][1] as RequestInit).method).toBe("POST");
  expect(changed).toHaveBeenCalled();
  expect(screen.getByText("Added as tasks (1)")).toBeInTheDocument();
});

test("first visit with a token fetches courses and asks which to follow", async () => {
  const unfollowed = state({ courses: state().courses.map((c) => ({ ...c, followed: false })), assignments: [] });
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(json({ ...unfollowed, sync: { last_attempt_at: null, last_success_at: null, last_error: null } }))
    .mockResolvedValueOnce(json(unfollowed))
    .mockResolvedValueOnce(json(state()));
  const user = userEvent.setup();
  render(<BCourses visible />);
  expect(await screen.findByText("Choose at least one course above, then Save courses.")).toBeVisible();
  expect(fetcher.mock.calls[1][0]).toBe("/api/bcourses/refresh");
  await user.click(screen.getByRole("checkbox", { name: /MATH 54/ }));
  await user.click(screen.getByRole("button", { name: "Save courses" }));
  expect(JSON.parse((fetcher.mock.calls[2][1] as RequestInit).body as string)).toEqual({ course_ids: ["1"] });
  expect(await screen.findByRole("list", { name: "Upcoming assignments" })).toBeVisible();
});

test("missing token and failed refresh are explained without losing the list", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(state({ configured: false, courses: [], assignments: [] })));
  render(<BCourses visible />);
  expect(await screen.findByText(/No bCourses token is set/)).toBeVisible();
  expect(screen.getByRole("button", { name: "Refresh" })).toBeDisabled();
});

test("a refresh error shows the service message and keeps the saved assignments", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(json(state()))
    .mockResolvedValueOnce(json({ error: { code: "bcourses_unreachable", message: "Cannot reach bCourses." } }, 502))
    .mockResolvedValueOnce(json(state()));
  const user = userEvent.setup();
  render(<BCourses visible />);
  await user.click(await screen.findByRole("button", { name: "Refresh" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Cannot reach bCourses.");
  expect(screen.getByRole("list", { name: "Upcoming assignments" })).toBeVisible();
});
