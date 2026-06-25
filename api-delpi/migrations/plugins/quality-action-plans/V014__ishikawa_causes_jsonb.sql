-- Ishikawa 6M: múltiplas causas por categoria (JSONB array de strings).

CREATE OR REPLACE FUNCTION quality._ishikawa_text_to_causes_json(raw_text TEXT)
RETURNS JSONB
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT COALESCE(
    (
      SELECT jsonb_agg(btrim(line) ORDER BY ord)
      FROM unnest(string_to_array(COALESCE(raw_text, ''), E'\n')) WITH ORDINALITY AS t(line, ord)
      WHERE btrim(line) <> ''
    ),
    '[]'::jsonb
  );
$$;

ALTER TABLE quality.quality_ishikawa_analysis
  ALTER COLUMN machine TYPE JSONB USING quality._ishikawa_text_to_causes_json(machine),
  ALTER COLUMN method_process TYPE JSONB USING quality._ishikawa_text_to_causes_json(method_process),
  ALTER COLUMN material TYPE JSONB USING quality._ishikawa_text_to_causes_json(material),
  ALTER COLUMN manpower TYPE JSONB USING quality._ishikawa_text_to_causes_json(manpower),
  ALTER COLUMN measurement TYPE JSONB USING quality._ishikawa_text_to_causes_json(measurement),
  ALTER COLUMN environment TYPE JSONB USING quality._ishikawa_text_to_causes_json(environment);

ALTER TABLE quality.quality_ishikawa_analysis
  ALTER COLUMN machine SET DEFAULT '[]'::jsonb,
  ALTER COLUMN method_process SET DEFAULT '[]'::jsonb,
  ALTER COLUMN material SET DEFAULT '[]'::jsonb,
  ALTER COLUMN manpower SET DEFAULT '[]'::jsonb,
  ALTER COLUMN measurement SET DEFAULT '[]'::jsonb,
  ALTER COLUMN environment SET DEFAULT '[]'::jsonb;

DROP FUNCTION quality._ishikawa_text_to_causes_json(TEXT);
