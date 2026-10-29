-- Synthetic seed for the isolated NC sandbox. Fictional data only;
-- no production/legitimate records are copied.

WITH a AS (
  INSERT INTO engineering.lmp_nonconformities
      (registered_at, occurrence_date, sale_number, lmp_number,
       customer_name, launch_date, last_revision_date,
       executed_by, released_by, status,
       defect_description, corrective_actions, technical_opinion,
       created_by, updated_by)
  VALUES ('2026-01-05T10:00:00Z', '2026-01-05', '004101', 'LMP-778',
          'Cliente Sintético Alfa', '2026-01-02', '2026-01-04',
          'Eng. Silva', 'Insp. Costa', 'open',
          'Furo de terminal fora da tolerância (0,4 mm).',
          'Rebarbar furo e reinspecionar lote.',
          'Desvio dimensional crítico para montagem.',
          'seed', 'seed')
  RETURNING id
),
b AS (
  INSERT INTO engineering.lmp_nonconformities
      (registered_at, occurrence_date, sale_number, lmp_number,
       customer_name, launch_date, last_revision_date,
       executed_by, released_by, status,
       defect_description, corrective_actions, technical_opinion,
       created_by, updated_by)
  VALUES ('2026-01-12T09:30:00Z', '2026-01-12', '004118', NULL,
          'Cliente Sintético Beta', '2026-01-09', NULL,
          'Eng. Souza', NULL, 'in_progress',
          'Desenho sem a última revisão liberada.',
          'Emitir revisão C e refazer checagem.',
          NULL, 'seed', 'seed')
  RETURNING id
),
c AS (
  INSERT INTO engineering.lmp_nonconformities
      (registered_at, occurrence_date, sale_number, lmp_number,
       customer_name, launch_date, last_revision_date,
       executed_by, released_by, status,
       defect_description, corrective_actions, technical_opinion,
       created_by, updated_by)
  VALUES ('2026-01-20T14:15:00Z', '2026-01-20', '004101', 'LMP-778',
          'Cliente Sintético Alfa', '2026-01-02', '2026-01-04',
          'Eng. Silva', 'Insp. Costa', 'done',
          'Acabamento com risco superficial na face B.',
          'Reprocesso de acabamento concluído e liberado.',
          'Sem impacto funcional.', 'seed', 'seed')
  RETURNING id
)
INSERT INTO engineering.lmp_nonconformity_products
    (nonconformity_id, product_code, product_description)
SELECT id, 'PRD1001X', 'PRODUTO SINTÉTICO CONJUNTO A' FROM a
UNION ALL
SELECT id, 'PRD2002Y', 'PRODUTO SINTÉTICO CHAPA B'   FROM b
UNION ALL
SELECT id, 'PRD1001X', 'PRODUTO SINTÉTICO CONJUNTO A' FROM c;

WITH tagged AS (
  SELECT id, LOWER(TRIM(label)) AS label_key
    FROM engineering.lmp_problem_tags
   WHERE LOWER(TRIM(label)) IN ('medida', 'desenho', 'acabamento')
)
INSERT INTO engineering.lmp_nonconformity_problem_tags (nonconformity_id, tag_id)
SELECT n.id, t.id
  FROM engineering.lmp_nonconformities n
  JOIN tagged t ON true
 WHERE n.defect_description LIKE 'Furo%' AND t.label_key = 'medida'
    OR n.defect_description LIKE 'Desenho%' AND t.label_key = 'desenho'
    OR n.defect_description LIKE 'Acabamento%' AND t.label_key = 'acabamento';
