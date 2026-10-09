BEGIN;

-- Renomeia o tipo general-request para deixar claro o destino: departamento
-- de Processos. Apenas apresentação (name/description) — sem mudança de
-- workflow, schema ou permissões.
UPDATE my_requests.request_types
SET
    name = 'Processos — Abertura de Chamado',
    description = 'Abertura de chamados e demandas gerais direcionadas ao departamento de Processos, criada pelo portal com título e descrição.',
    updated_at = NOW()
WHERE code = 'general-request';

COMMIT;
