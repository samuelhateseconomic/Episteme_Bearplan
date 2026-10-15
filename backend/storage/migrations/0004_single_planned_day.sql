-- A task/subtask is one work item with one planned date. Multi-day work must be
-- split into subtasks, whose completion continues to derive their parent's state.
-- Never discard legacy multi-day placements to make this constraint fit: an
-- incompatible upgrade rolls back, leaving the prior database usable unchanged.
CREATE UNIQUE INDEX planned_items_one_per_task ON planned_items (task_id);
