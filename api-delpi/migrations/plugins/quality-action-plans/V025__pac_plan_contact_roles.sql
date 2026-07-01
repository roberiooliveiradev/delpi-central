-- Papéis de contato separados: cliente vs interlocutores DELPI (8D / rastreabilidade)

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS customer_contact_email VARCHAR(300),
    ADD COLUMN IF NOT EXISTS customer_contact_phone VARCHAR(100),
    ADD COLUMN IF NOT EXISTS delpi_contact_name VARCHAR(300),
    ADD COLUMN IF NOT EXISTS delpi_contact_area VARCHAR(50),
    ADD COLUMN IF NOT EXISTS delpi_sales_rep VARCHAR(300),
    ADD COLUMN IF NOT EXISTS delpi_quality_contact VARCHAR(300);

COMMENT ON COLUMN quality.quality_action_plans.customer_contact IS
    'Pessoa de contato no cliente (ex.: destinatário formal do 8D).';
COMMENT ON COLUMN quality.quality_action_plans.customer_contact_email IS
    'E-mail do contato no cliente para envio do relatório 8D.';
COMMENT ON COLUMN quality.quality_action_plans.customer_contact_phone IS
    'Telefone do contato no cliente.';
COMMENT ON COLUMN quality.quality_action_plans.delpi_contact_name IS
    'Interlocutor DELPI responsável pelo atendimento da NC (ex.: comercial).';
COMMENT ON COLUMN quality.quality_action_plans.delpi_contact_area IS
    'Área DELPI do interlocutor principal: comercial, qualidade, pcp, engenharia, outro.';
COMMENT ON COLUMN quality.quality_action_plans.delpi_sales_rep IS
    'Vendedor DELPI vinculado ao cliente, quando distinto do interlocutor principal.';
COMMENT ON COLUMN quality.quality_action_plans.delpi_quality_contact IS
    'Referência de qualidade DELPI no caso (ex.: analista PAC).';
