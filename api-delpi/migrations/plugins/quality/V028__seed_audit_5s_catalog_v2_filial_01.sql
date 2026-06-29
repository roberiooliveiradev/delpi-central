-- Catálogo Auditoria 5S v2 — filial 01 (15 critérios, 3 por senso)
-- Filial 02 permanece em catalog_version = 1 (48 critérios).

CREATE TABLE IF NOT EXISTS quality.audit_5s_branch_catalog (
    branch_code VARCHAR(2) PRIMARY KEY,
    catalog_version INTEGER NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_audit_5s_branch_catalog_branch CHECK (branch_code IN ('01', '02')),
    CONSTRAINT ck_audit_5s_branch_catalog_version CHECK (catalog_version >= 1)
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_catalog_senso_names (
    catalog_version INTEGER NOT NULL,
    senso_sort_order SMALLINT NOT NULL,
    name VARCHAR(100) NOT NULL,

    PRIMARY KEY (catalog_version, senso_sort_order),
    CONSTRAINT ck_audit_5s_catalog_senso_sort CHECK (senso_sort_order BETWEEN 1 AND 5)
);

INSERT INTO quality.audit_5s_branch_catalog (branch_code, catalog_version)
VALUES
    ('01', 2),
    ('02', 1)
ON CONFLICT (branch_code) DO UPDATE
    SET catalog_version = EXCLUDED.catalog_version,
        active = TRUE;

INSERT INTO quality.audit_5s_catalog_senso_names (catalog_version, senso_sort_order, name)
VALUES (2, 5, 'Autodisciplina')
ON CONFLICT (catalog_version, senso_sort_order) DO UPDATE
    SET name = EXCLUDED.name;

-- Senso 1 — Utilização
INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U01', 'Existem materiais, ferramentas ou equipamentos sem uso no local?', 1, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U02', 'Os materiais e ferramentas estão em boas condições de uso?', 2, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U03', 'Há falta de ferramentas, equipamentos ou recursos necessários para o trabalho?', 3, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

-- Senso 2 — Ordenação
INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O01', 'Os materiais, armários, bancadas, mesas e ferramentas estão organizados e de fácil acesso?', 1, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O02', 'Os locais dos materiais e equipamentos estão identificados e sinalizados corretamente?', 2, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O03', 'Os itens mais utilizados estão em locais de fácil acesso?', 3, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

-- Senso 3 — Limpeza
INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L01', 'Piso, paredes e estruturas estão limpos e conservados?', 1, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L02', 'Máquinas, ferramentas e bancadas estão limpas e organizadas?', 2, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L03', 'Corredores e áreas comuns estão limpos e organizados?', 3, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

-- Senso 4 — Padronização
INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P01', 'As identificações, etiquetas, demarcações e centros de trabalho estão padronizadas e atualizadas?', 1, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P02', 'As proteções e identificações de segurança estão visíveis e em boas condições?', 2, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P03', 'Os resíduos estão identificados e separados corretamente? (terminais, fios, palhas, borra de estanho, papel, plástico)', 3, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

-- Senso 5 — Autodisciplina (rótulo via audit_5s_catalog_senso_names)
INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D01', 'As pendências do 5S estão sendo tratadas dentro do prazo?', 1, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D02', 'A equipe conhece e pratica as regras do 5S?', 2, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D03', 'O setor mantém o 5S conforme os padrões definidos pela Delpi?', 3, 2
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;
