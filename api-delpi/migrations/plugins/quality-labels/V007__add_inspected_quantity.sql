ALTER TABLE quality_labels.inspection_labels
    ADD COLUMN IF NOT EXISTS inspected_quantity INTEGER;
