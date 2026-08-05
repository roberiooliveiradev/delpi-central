-- Planejamento Orçamentário — catálogo de categorias de investimento CAPEX (Fase 2A.3)
-- Schema: planejamento_orcamentario
-- Seed idempotente: ON CONFLICT (code) DO NOTHING — não sobrescreve edições administrativas.

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.capex_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(80) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deactivated_by VARCHAR(100),
    deactivated_at TIMESTAMPTZ,

    CONSTRAINT uq_po_capex_categories_code UNIQUE (code),
    CONSTRAINT ck_po_capex_categories_code_nonempty CHECK (length(trim(code)) > 0),
    CONSTRAINT ck_po_capex_categories_name_nonempty CHECK (length(trim(name)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_po_capex_categories_active_order
    ON planejamento_orcamentario.capex_categories (is_active, display_order, name);

CREATE INDEX IF NOT EXISTS ix_po_capex_categories_display_order
    ON planejamento_orcamentario.capex_categories (display_order, name);

-- Seed inicial (24 categorias). Reexecuções não alteram name/description/ordem já existentes.
INSERT INTO planejamento_orcamentario.capex_categories (
    code, name, description, display_order, is_active, is_system_default, created_by, updated_by
) VALUES
    ('COMPUTADORES_PERIFERICOS', 'Computadores e Periféricos', NULL, 10, TRUE, TRUE, 'system', 'system'),
    ('FERRAMENTAS', 'Ferramentas', NULL, 20, TRUE, TRUE, 'system', 'system'),
    ('INSTALACOES', 'Instalações', NULL, 30, TRUE, TRUE, 'system', 'system'),
    ('INSTRUMENTOS_TESTE_CONTROLE', 'Instrumentos de Teste e Controle', NULL, 40, TRUE, TRUE, 'system', 'system'),
    ('MAQUINAS_EQUIPAMENTOS_INDUSTRIAIS', 'Máquinas e Equipamentos Industriais', NULL, 50, TRUE, TRUE, 'system', 'system'),
    ('MOVEIS_UTENSILIOS', 'Móveis e Utensílios', NULL, 60, TRUE, TRUE, 'system', 'system'),
    ('OBRAS_CONSTRUCAO_CIVIL', 'Obras e Construção Civil', NULL, 70, TRUE, TRUE, 'system', 'system'),
    ('SOFTWARES_LICENCAS_SISTEMAS', 'Softwares, Licenças e Sistemas', NULL, 80, TRUE, TRUE, 'system', 'system'),
    ('VEICULOS', 'Veículos', NULL, 90, TRUE, TRUE, 'system', 'system'),
    ('GABARITOS_DISPOSITIVOS_BANCADAS', 'Gabaritos, Dispositivos e Bancadas', NULL, 100, TRUE, TRUE, 'system', 'system'),
    ('EQUIPAMENTOS_CORTE_DOCAPE', 'Equipamentos de Corte e Docape', NULL, 110, TRUE, TRUE, 'system', 'system'),
    ('EQUIPAMENTOS_CRIMPAGEM', 'Equipamentos de Crimpagem', NULL, 120, TRUE, TRUE, 'system', 'system'),
    ('EQUIPAMENTOS_TESTE_ELETRICO', 'Equipamentos de Teste Elétrico', NULL, 130, TRUE, TRUE, 'system', 'system'),
    ('AUTOMACAO_INDUSTRIAL_ROBOTICA', 'Automação Industrial e Robótica', NULL, 140, TRUE, TRUE, 'system', 'system'),
    ('METROLOGIA_CALIBRACAO', 'Metrologia e Calibração', NULL, 150, TRUE, TRUE, 'system', 'system'),
    ('LABORATORIO_CONTROLE_QUALIDADE', 'Laboratório e Controle da Qualidade', NULL, 160, TRUE, TRUE, 'system', 'system'),
    ('MOVIMENTACAO_ARMAZENAGEM', 'Movimentação e Armazenagem de Materiais', NULL, 170, TRUE, TRUE, 'system', 'system'),
    ('SEGURANCA_ERGONOMIA_MEIO_AMBIENTE', 'Segurança, Ergonomia e Meio Ambiente', NULL, 180, TRUE, TRUE, 'system', 'system'),
    ('INFRAESTRUTURA_ELETRICA_UTILIDADES', 'Infraestrutura Elétrica e Utilidades', NULL, 190, TRUE, TRUE, 'system', 'system'),
    ('EFICIENCIA_ENERGETICA_SUSTENTABILIDADE', 'Eficiência Energética e Sustentabilidade', NULL, 200, TRUE, TRUE, 'system', 'system'),
    ('TELECOMUNICACOES_INFRA_TI', 'Telecomunicações e Infraestrutura de TI', NULL, 210, TRUE, TRUE, 'system', 'system'),
    ('EQUIPAMENTOS_MANUTENCAO', 'Equipamentos de Manutenção', NULL, 220, TRUE, TRUE, 'system', 'system'),
    ('EQUIPAMENTOS_LOGISTICA_INTERNA', 'Equipamentos de Logística Interna', NULL, 230, TRUE, TRUE, 'system', 'system'),
    ('CLIMATIZACAO_VENTILACAO_INDUSTRIAL', 'Climatização e Ventilação Industrial', NULL, 240, TRUE, TRUE, 'system', 'system')
ON CONFLICT (code) DO NOTHING;
