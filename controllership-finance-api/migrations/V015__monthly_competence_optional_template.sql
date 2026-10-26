-- V015 — Abertura de fechamento mensal sem checklist publicado
--
-- Decisão de produto (Plano 113 §10, GO PO 26/10/2026; DR-C1 do doc 112
-- §32): um usuário com `controllership-finance.access` pode abrir o
-- fechamento de um mês mesmo sem versão PUBLISHED do checklist e sem
-- documentos exigidos cadastrados.
--
-- Mudança de schema:
--   * `monthly_competence.template_version_id` passa a admitir NULL.
--     NULL = fechamento aberto sem checklist vigente → snapshot P2
--     legitimamente vazio (zero itens em `competence_checklist_item`),
--     sem template fictício e sem exigências inventadas.
--   * FK `template_version_id → checklist_template_version` permanece:
--     quando preenchida, a referência continua validada.
--   * `competence_checklist_item.source_template_item_id` segue
--     NOT NULL — itens excepcionais continuam exigindo origem
--     rastreável; a abertura sem template simplesmente não cria itens.
--
-- Compatibilidade: competências existentes mantêm sua versão de
-- template e snapshots intactos — a alteração só alarga o domínio,
-- nunca reescreve linhas. Conclusão segue impossível por vacuidade:
-- `derive_closing_state` exige pacotes aplicáveis e conciliações P3
-- oficiais, independentemente do checklist.
--
-- Rollback seguro (somente quando nenhuma competência NULL existir):
--   ALTER TABLE controllership_finance.monthly_competence
--       ALTER COLUMN template_version_id SET NOT NULL;
-- Se já houver competências sem template, o rollback manual exige
-- decisão de dados (associar versão vigente ou remover fechamento) —
-- por isso a migration não contém caminho destrutivo automático.

BEGIN;

ALTER TABLE controllership_finance.monthly_competence
    ALTER COLUMN template_version_id DROP NOT NULL;

COMMENT ON COLUMN controllership_finance.monthly_competence.template_version_id IS
    'Versão publicada do checklist copiada no snapshot da abertura. NULL = fechamento aberto sem checklist vigente (Plano 113 §10): lista de exigências legitimamente vazia.';

COMMIT;
