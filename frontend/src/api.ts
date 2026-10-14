// Typed client for the local BearPlans service. Paths are same-origin.

export const TITLE_MAX_LENGTH = 200;
export const NOTES_MAX_LENGTH = 2000;
export const NAME_MAX_LENGTH = 100;
export const ESTIMATE_MIN_MINUTES = 1;
export const ESTIMATE_MAX_MINUTES = 10080;

export interface Project {
  id: string;
  name: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  revision: number;
}

export interface Task {
  id: string;
  project_id: string;
  parent_id: string | null;
  title: string;
  notes: string;
  deadline: string | null;
  estimate_minutes: number | null;
  /** Derived for a task with subtasks: true only when every subtask is complete. */
  completed: boolean;
  completed_at: string | null;
  subtask_count: number;
  completed_subtask_count: number;
  created_at: string;
  updated_at: string;
  revision: number;
}

/** Fields a task edit may change. Omit one to leave it alone; null clears it. */
export interface TaskEdit {
  title?: string;
  notes?: string | null;
  deadline?: string | null;
  estimate_minutes?: number | null;
}

export interface NewTask extends TaskEdit {
  title: string;
  project_id?: string;
  parent_id?: string;
}

export class ApiError extends Error {
  readonly field?: string;

  constructor(message: string, field?: string) {
    super(message);
    this.field = field;
  }
}

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
    const error = (body as { error?: { message?: unknown; field?: unknown } } | null)?.error;
    const message = typeof error?.message === "string" ? error.message : `The service returned an error (${response.status}).`;
    throw new ApiError(message, typeof error?.field === "string" ? error.field : undefined);
  }
  return body as T;
}

const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) });

export async function listProjects(signal?: AbortSignal): Promise<Project[]> {
  return (await request<{ projects: Project[] }>("/api/projects", { signal })).projects;
}

export function createProject(name: string): Promise<Project> {
  return request<Project>("/api/projects", json("POST", { name }));
}

export function renameProject(id: string, name: string): Promise<Project> {
  return request<Project>(`/api/projects/${encodeURIComponent(id)}`, json("PATCH", { name }));
}

export interface TaskList {
  tasks: Task[];
  progress: { completed: number; total: number };
}

export async function listTasks(projectId?: string, signal?: AbortSignal): Promise<TaskList> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return request<TaskList>(`/api/tasks${query}`, { signal });
}

export function createTask(task: NewTask): Promise<Task> {
  return request<Task>("/api/tasks", json("POST", task));
}

export function updateTask(id: string, edit: TaskEdit): Promise<Task> {
  return request<Task>(`/api/tasks/${encodeURIComponent(id)}`, json("PATCH", edit));
}

export function setTaskCompletion(id: string, complete: boolean): Promise<Task> {
  return request<Task>(`/api/tasks/${encodeURIComponent(id)}/completion`, json("PUT", { complete }));
}

export function removeSubtask(id: string): Promise<Task> {
  return request<Task>(`/api/tasks/${encodeURIComponent(id)}`, { method: "DELETE" });
}
