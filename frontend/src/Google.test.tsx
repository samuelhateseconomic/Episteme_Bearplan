import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Google } from "./Google";
import type { GoogleState } from "./api";

const base: GoogleState = {
  configured: true, connected: true, sign_in_pending: false, sign_in_error: null, missing_permissions: [],
  tasks: { last_attempt_at: null, last_success_at: null, last_error: null, synced_lists: 0, synced_tasks: 0, synced_events: 0 },
};

function reply(body: unknown, status = 200, url = "") {
  if (url.endsWith("/api/google/calendars") || url.endsWith("/calendars/refresh")) body = [];
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

afterEach(() => vi.restoreAllMocks());

describe("Google", () => {
  it("explains setup when no sign-in file exists", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => reply({ ...base, configured: false, connected: false }));
    render(<Google visible />);
    expect(await screen.findByText(/No Google sign-in file was found/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Connect Google" })).toBeNull();
  });

  it("opens Google sign-in in a new tab", async () => {
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith("/connect")) return reply({ url: "https://accounts.google.com/o/oauth2/auth?x=1" });
      return reply({ ...base, connected: false, sign_in_pending: url.endsWith("/connect") });
    });
    render(<Google visible />);
    await userEvent.click(await screen.findByRole("button", { name: "Connect Google" }));
    await waitFor(() => expect(open).toHaveBeenCalledWith("https://accounts.google.com/o/oauth2/auth?x=1", "_blank", "noopener"));
    expect(await screen.findByText(/sign-in opened in a new tab/)).toBeTruthy();
  });

  it("syncs now and shows counts", async () => {
    const changed = vi.fn();
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => String(input).endsWith("/tasks/sync")
      ? reply({ ...base, tasks: { ...base.tasks, synced_lists: 2, synced_tasks: 7, last_success_at: "2026-11-02T20:00:00Z" } })
      : reply(base, 200, String(input)));
    render(<Google visible onChanged={changed} />);
    await userEvent.click(await screen.findByRole("button", { name: "Sync now" }));
    expect(await screen.findByText(/7 tasks in 2 lists/)).toBeTruthy();
    expect(screen.getByRole("status").textContent).toContain("up to date");
    expect(changed).toHaveBeenCalled();
  });

  it("shows a failed sync and missing permissions", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => String(input).endsWith("/tasks/sync")
      ? reply({ error: { code: "google_unreachable", message: "Cannot reach Google." } }, 502)
      : reply({ ...base, missing_permissions: ["tasks"], tasks: { ...base.tasks, last_error: "Cannot reach Google." } }, 200, String(input)));
    render(<Google visible />);
    expect(await screen.findByText(/Some permissions were not given \(tasks\)/)).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Sync now" }));
    expect((await screen.findAllByRole("alert")).some((node) => node.textContent?.includes("Cannot reach Google."))).toBe(true);
  });
});

describe("Google calendars to show", () => {
  it("lists calendars and saves the chosen ones", async () => {
    const calendars = [
      { calendar_id: "me", summary: "Me", color: "#9fc6e7", is_primary: true, followed: false },
      { calendar_id: "work", summary: "Lab job", color: "", is_primary: false, followed: false },
    ];
    const fetch = vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/api/google/calendars") && init?.method === "PUT") return reply(calendars.map((c) => ({ ...c, followed: c.calendar_id === "work" })));
      if (url.endsWith("/api/google/calendars")) return reply(calendars);
      return reply(base);
    });
    render(<Google visible />);
    await userEvent.click(await screen.findByRole("checkbox", { name: /Lab job/ }));
    await userEvent.click(screen.getByRole("button", { name: "Save calendars" }));
    expect(fetch).toHaveBeenCalledWith("/api/google/calendars", expect.objectContaining({ method: "PUT", body: JSON.stringify({ calendar_ids: ["work"] }) }));
    expect(await screen.findByText(/Saved your calendars/)).toBeTruthy();
    expect((screen.getByRole("checkbox", { name: /Lab job/ }) as HTMLInputElement).checked).toBe(true);
  });
});
