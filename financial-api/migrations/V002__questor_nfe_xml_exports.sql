CREATE TABLE IF NOT EXISTS financial.questor_nfe_xml_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_key VARCHAR(44) NOT NULL,
    branch_code VARCHAR(2) NOT NULL,
    provider_document_id VARCHAR(64),
    provider_file_id VARCHAR(64),
    invoice_number VARCHAR(20),
    series VARCHAR(10),
    emission_date DATE,
    filename VARCHAR(80),
    status VARCHAR(20) NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error_code VARCHAR(64),
    last_error_message VARCHAR(500),
    exported_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT questor_nfe_xml_exports_access_key_key UNIQUE (access_key),
    CONSTRAINT questor_nfe_xml_exports_branch_check CHECK (branch_code IN ('01', '02')),
    CONSTRAINT questor_nfe_xml_exports_status_check CHECK (
        status IN ('processing', 'success', 'failed', 'ignored')
    ),
    CONSTRAINT questor_nfe_xml_exports_attempts_check CHECK (attempts >= 0)
);

CREATE INDEX IF NOT EXISTS idx_questor_nfe_xml_exports_status
    ON financial.questor_nfe_xml_exports (status);

CREATE INDEX IF NOT EXISTS idx_questor_nfe_xml_exports_branch_emission
    ON financial.questor_nfe_xml_exports (branch_code, emission_date);

COMMENT ON TABLE financial.questor_nfe_xml_exports IS
    'Ledger da exportação de XML de NF-e modelo 55 para o importador do Protheus. A chave de acesso é a identidade fiscal global. success não é reexportado, mesmo se o arquivo sumir da pasta.';

COMMENT ON COLUMN financial.questor_nfe_xml_exports.access_key IS
    'Chave da NF-e com 44 dígitos. Única em todas as filiais.';

COMMENT ON COLUMN financial.questor_nfe_xml_exports.provider_file_id IS
    'XmlFilename do Questor, parâmetro Id do download interno.';

COMMENT ON COLUMN financial.questor_nfe_xml_exports.provider_document_id IS
    'Id da linha NF-e no Questor, parâmetro IdEntity do download interno.';

COMMENT ON COLUMN financial.questor_nfe_xml_exports.status IS
    'processing, success, failed ou ignored. success é terminal para a automação.';
