import { vi } from "vitest";
import { startTimer } from "./api";

const operationId = "00000000-0000-4000-8000-000000000001";
const taskId = "00000000-0000-4000-8000-000000000002";
const state = { server_now: "2026-10-20T16:00:00.000000Z", active_session: null, last_session: null };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

test("default and explicitly selected Pine remain compatible with the previous strict Start API", async () => {
  const bodies: Record<string, unknown>[] = [];
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    bodies.push(body);
    return Object.keys(body).some((key) => !["operation_id", "task_id", "duration_minutes"].includes(key))
      ? json({ error: { message: "Extra inputs are not permitted." } }, 422) : json(state);
  });
  await expect(startTimer(operationId, taskId, 25)).resolves.toEqual(state);
  await expect(startTimer(operationId, taskId, 25, "pine")).resolves.toEqual(state);
  expect(bodies).toEqual([
    { operation_id: operationId, task_id: taskId, duration_minutes: 25 },
    { operation_id: operationId, task_id: taskId, duration_minutes: 25 },
  ]);
  expect(fetcher.mock.calls.every(([path]) => path === "/api/timer/start")).toBe(true);
});

test.each(["birch", "oak", "cherry"] as const)("new countdowns explicitly send the selected %s species", async (species) => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(state));
  await startTimer(operationId, taskId, 25, species);
  expect(JSON.parse(String(fetcher.mock.calls[0][1]?.body))).toEqual({ operation_id: operationId, task_id: taskId, duration_minutes: 25, species });
});
