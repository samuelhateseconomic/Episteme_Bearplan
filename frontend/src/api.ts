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
  readonly status?: number;

  constructor(message: string, field?: string, status?: number) {
    super(message);
    this.field = field;
    this.status = status;
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
    throw new ApiError(message, typeof error?.field === "string" ? error.field : undefined, response.status);
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

export interface Placement {
  id: string;
  task_id: string;
  planned_date: string;
  created_at: string;
  updated_at: string;
  revision: number;
}

export interface Planning {
  today: string;
  timezone: string;
  week_start: string;
  week_end: string;
  tasks: Task[];
  /** Current open-week placements, including dates outside the displayed week. */
  placements: Placement[];
  closed_week?: ClosedWeek | null;
  closed_weeks?: ClosedWeekSummary[];
}

export interface HistoricalTask extends Task {
  project_name: string;
  parent_title: string | null;
}

export interface ClosedWeek {
  snapshot_version: 1;
  week_start: string;
  week_end: string;
  closed_at: string | null;
  timezone: string;
  tasks: HistoricalTask[];
  placements: Placement[];
  completed: number;
  total: number;
}

export interface ClosedWeekSummary {
  week_start: string;
  week_end: string;
  closed_at: string;
  completed: number;
  total: number;
}

export interface ClosePreview { preview_token: string; snapshot: ClosedWeek }
export interface CarryoverCandidate {
  task_id: string;
  snapshot_task: HistoricalTask;
  task: Task | null;
  eligible: boolean;
  reason: string | null;
  existing_planned_date: string | null;
}
export interface CarryoverOptions {
  week_start: string;
  destination_start: string;
  destination_end: string;
  candidates: CarryoverCandidate[];
}
export interface CarryoverSelection { task_id: string; planned_date: string }
export interface CarryoverPreview {
  preview_token: string;
  week_start: string;
  destination_start: string;
  destination_end: string;
  items: (CarryoverSelection & { task: Task; project_name: string; parent_title: string | null })[];
}

const weekPath = (week: string) => `/api/weeks/${encodeURIComponent(week)}`;
export function previewCloseWeek(week: string): Promise<ClosePreview> {
  return request<ClosePreview>(`${weekPath(week)}/close-preview`);
}
export function closeWeek(week: string, previewToken: string): Promise<ClosedWeek> {
  return request<ClosedWeek>(`${weekPath(week)}/close`, json("POST", { preview_token: previewToken }));
}
export function getCarryover(week: string): Promise<CarryoverOptions> {
  return request<CarryoverOptions>(`${weekPath(week)}/carryover`);
}
export function previewCarryover(week: string, selections: CarryoverSelection[]): Promise<CarryoverPreview> {
  return request<CarryoverPreview>(`${weekPath(week)}/carryover-preview`, json("POST", { selections }));
}
export function applyCarryover(week: string, operationId: string, previewToken: string, selections: CarryoverSelection[]): Promise<{ operation_id: string; week_start: string; placements: Placement[] }> {
  return request(`${weekPath(week)}/carryover`, json("POST", { operation_id: operationId, preview_token: previewToken, selections }));
}

export function getPlanning(week?: string, signal?: AbortSignal): Promise<Planning> {
  return request<Planning>(`/api/planning${week ? `?week=${encodeURIComponent(week)}` : ""}`, { signal });
}

export function assignTask(taskId: string, plannedDate: string): Promise<Placement> {
  return request<Placement>("/api/placements", json("POST", { task_id: taskId, planned_date: plannedDate }));
}

export function movePlacement(id: string, plannedDate: string): Promise<Placement> {
  return request<Placement>(`/api/placements/${encodeURIComponent(id)}`, json("PATCH", { planned_date: plannedDate }));
}

export function removePlacement(id: string): Promise<{ removed: string }> {
  return request<{ removed: string }>(`/api/placements/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export interface TimerRecovery {
  id: string;
  kind: "service_restart" | "sleep" | "clock_change" | "checkpoint_gap";
  reason: string;
  checkpoint_at: string;
  detected_at: string;
  confirmed_active_seconds: number;
  measured_sleep_seconds: number | null;
  resolved_at: string | null;
  resolution: "resume" | "finish" | null;
}

export interface TreeProgress {
  id: string;
  species: "pine";
  stage: "seedling" | "sapling" | "mature";
  progress: number;
  outcome: "mature" | "unfinished" | null;
}

export interface ForestTree extends TreeProgress {
  session_id: string;
  task_title: string;
  project_name: string;
  parent_title: string | null;
  started_at: string;
  finished_at: string;
  duration_minutes: number;
  active_seconds: number;
}

export async function getForest(signal?: AbortSignal): Promise<ForestTree[]> {
  return (await request<{ trees: ForestTree[] }>("/api/forest", { signal })).trees;
}

export interface TimerSession {
  id: string;
  start_operation_id: string;
  task_id: string;
  task_title: string;
  project_id: string;
  project_name: string;
  parent_title: string | null;
  state: "running" | "paused" | "needs_review" | "finished";
  duration_minutes: number;
  requested_seconds: number;
  active_seconds: number;
  remaining_seconds: number;
  started_at: string;
  checkpoint_at: string;
  deadline_at: string | null;
  finished_at: string | null;
  outcome: "completed" | "finished_early" | "interrupted" | null;
  review_reason: string | null;
  recovery?: TimerRecovery | null;
  tree: TreeProgress | null;
  revision: number;
}

export interface TimerState {
  server_now: string;
  active_session: TimerSession | null;
  last_session: TimerSession | null;
}

export interface TimerControl {
  operation_id: string;
  expected_revision: number;
  discard_uncertain?: boolean;
}

export function getTimer(signal?: AbortSignal): Promise<TimerState> {
  return request<TimerState>("/api/timer", { signal });
}

export function startTimer(operationId: string, taskId: string, durationMinutes: number): Promise<TimerState> {
  return request<TimerState>("/api/timer/start", json("POST", { operation_id: operationId, task_id: taskId, duration_minutes: durationMinutes }));
}

export function controlTimer(id: string, action: "pause" | "resume" | "finish", control: TimerControl): Promise<TimerState> {
  return request<TimerState>(`/api/timer/${encodeURIComponent(id)}/${action}`, json("POST", control));
}

export function recoverTimer(id: string, resolution: "resume" | "finish", control: TimerControl): Promise<TimerState> {
  return request<TimerState>(`/api/timer/${encodeURIComponent(id)}/recover`, json("POST", { ...control, resolution, discard_uncertain: true }));
}
