-- Distinct planned dates reference the same task. The original table constraint
-- still rejects duplicate (task_id, planned_date) pairs. No saved rows change.
DROP INDEX IF EXISTS planned_items_one_per_task;
