// Typed client for the local BearPlans service. Paths are same-origin.

export const TITLE_MAX_LENGTH = 200;

export interface Task {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  revision: number;
}

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { Accept: "application/json", ...(init?.body ? { "Content-Type": "application/json" } : {}) },
    });
  } catch (error) {
    if (init?.signal?.aborted) throw error;
    throw new ApiError("Cannot reach the BearPlans service. Is it still running?");
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message = (body as { error?: { message?: unknown } } | null)?.error?.message;
    throw new ApiError(typeof message === "string" ? message : `The service returned an error (${response.status}).`);
  }
  return body as T;
}

export async function listTasks(signal?: AbortSignal): Promise<Task[]> {
  const body = await request<{ tasks: Task[] }>("/api/tasks", { signal });
  return body.tasks;
}

export function createTask(title: string): Promise<Task> {
  return request<Task>("/api/tasks", { method: "POST", body: JSON.stringify({ title }) });
}
