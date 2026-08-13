-- Remove operational group seeds from V010. Managers create groups via API/UI.
-- Members cascade via FK ON DELETE CASCADE.

DELETE FROM commercial.commercial_groups
 WHERE kind IN ('sellers', 'sales_assistants', 'billing', 'estimators');
