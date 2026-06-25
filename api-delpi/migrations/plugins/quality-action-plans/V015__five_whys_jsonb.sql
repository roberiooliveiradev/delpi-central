-- Porquês: trilhas dinâmicas (ocorrência e detecção) em JSONB.

ALTER TABLE quality.quality_five_whys
  ADD COLUMN IF NOT EXISTS occurrence_whys JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS detection_whys JSONB NOT NULL DEFAULT '[]'::jsonb;

UPDATE quality.quality_five_whys
   SET occurrence_whys = (
         SELECT COALESCE(jsonb_agg(btrim(val) ORDER BY ord), '[]'::jsonb)
           FROM (
             SELECT 1 AS ord, why_1 AS val
             UNION ALL SELECT 2, why_2
             UNION ALL SELECT 3, why_3
             UNION ALL SELECT 4, why_4
             UNION ALL SELECT 5, why_5
           ) AS legacy
          WHERE btrim(COALESCE(val, '')) <> ''
       ),
       detection_whys = (
         SELECT COALESCE(jsonb_agg(btrim(val) ORDER BY ord), '[]'::jsonb)
           FROM (
             SELECT 1 AS ord, detection_why_1 AS val
             UNION ALL SELECT 2, detection_why_2
             UNION ALL SELECT 3, detection_why_3
             UNION ALL SELECT 4, detection_why_4
             UNION ALL SELECT 5, detection_why_5
           ) AS legacy
          WHERE btrim(COALESCE(val, '')) <> ''
       );

ALTER TABLE quality.quality_five_whys
  DROP COLUMN IF EXISTS why_1,
  DROP COLUMN IF EXISTS why_2,
  DROP COLUMN IF EXISTS why_3,
  DROP COLUMN IF EXISTS why_4,
  DROP COLUMN IF EXISTS why_5,
  DROP COLUMN IF EXISTS detection_why_1,
  DROP COLUMN IF EXISTS detection_why_2,
  DROP COLUMN IF EXISTS detection_why_3,
  DROP COLUMN IF EXISTS detection_why_4,
  DROP COLUMN IF EXISTS detection_why_5;
