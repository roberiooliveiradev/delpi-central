-- Parent explícito da árvore de versões (Timeline layout=tree).
-- Default em novas versões: revisão ativa; baseline permanece NULL.
-- Backfill: parent = revisão com revision_number - 1 no mesmo kaizen.

ALTER TABLE quality.kaizen_revisions
    ADD COLUMN IF NOT EXISTS parent_revision_id UUID NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'fk_kaizen_revisions_parent'
    ) THEN
        ALTER TABLE quality.kaizen_revisions
            ADD CONSTRAINT fk_kaizen_revisions_parent
            FOREIGN KEY (parent_revision_id)
            REFERENCES quality.kaizen_revisions (id)
            ON UPDATE RESTRICT
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_kaizen_revisions_parent
    ON quality.kaizen_revisions (kaizen_id, parent_revision_id);

UPDATE quality.kaizen_revisions child
   SET parent_revision_id = parent.id
  FROM quality.kaizen_revisions parent
 WHERE child.parent_revision_id IS NULL
   AND child.revision_number > 1
   AND parent.kaizen_id = child.kaizen_id
   AND parent.revision_number = child.revision_number - 1;
