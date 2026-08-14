-- Invoice issuance — snapshot de contato SA4 (razão, CNPJ, endereço, telefone)
-- Aplicar somente com `up`. Nunca editar V001–V003.

ALTER TABLE invoice_issuance.invoice_issuance_requests
    ADD COLUMN IF NOT EXISTS carrier_legal_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS carrier_tax_id VARCHAR(20),
    ADD COLUMN IF NOT EXISTS carrier_address VARCHAR(400),
    ADD COLUMN IF NOT EXISTS carrier_phone VARCHAR(40);

COMMENT ON COLUMN invoice_issuance.invoice_issuance_requests.carrier_legal_name IS
    'Razão social SA4.A4_NOME no momento da solicitação.';
COMMENT ON COLUMN invoice_issuance.invoice_issuance_requests.carrier_tax_id IS
    'CNPJ SA4.A4_CGC no momento da solicitação.';
COMMENT ON COLUMN invoice_issuance.invoice_issuance_requests.carrier_address IS
    'Endereço formatado (rua, bairro, município-UF, CEP) no momento da solicitação.';
COMMENT ON COLUMN invoice_issuance.invoice_issuance_requests.carrier_phone IS
    'Telefone SA4.A4_TEL no momento da solicitação.';
