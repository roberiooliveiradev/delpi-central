-- Template padrão do checklist do Certificado de Qualidade (RQ-032).
-- Os itens são copiados (snapshot) para cada certificado no momento da criação,
-- permitindo adicionar linhas custom sem alterar o template.

CREATE TABLE IF NOT EXISTS quality_labels.checklist_template_items (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position     INTEGER NOT NULL,
    description  TEXT NOT NULL,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ql_checklist_template_pos
    ON quality_labels.checklist_template_items (position);

-- Seed idempotente dos 17 itens do RQ-032 (só insere se a tabela estiver vazia).
INSERT INTO quality_labels.checklist_template_items (position, description)
SELECT * FROM (VALUES
    (1,  'Identificação e Embalagem do Produto'),
    (2,  'Dados Específicos do Desenho'),
    (3,  'Bitola dos Cabos (mm/ AWG)'),
    (4,  'Coloração dos Cabos'),
    (5,  'Gravação/ Numeração dos Cabos'),
    (6,  'Concentricidade dos Cabos'),
    (7,  'Aspecto/ Aparência da Isolação'),
    (8,  'Comprimento total'),
    (9,  'Comprimento dos Decapes'),
    (10, 'Marcas ou Cortes no Condutor'),
    (11, 'Tipo e Aplicação do Terminal/ Termostato'),
    (12, 'Fixação dos Terminais/ Termostatos/ Termistores'),
    (13, 'Aspecto de solda'),
    (14, 'Pontas Estanhadas'),
    (15, 'Aplicação do Conector'),
    (16, 'Teste de tração – (terminal do cliente, sem parâmetros)'),
    (17, 'Aspecto do Tubo Isolante/Termoencolhível')
) AS seed(position, description)
WHERE NOT EXISTS (SELECT 1 FROM quality_labels.checklist_template_items);
