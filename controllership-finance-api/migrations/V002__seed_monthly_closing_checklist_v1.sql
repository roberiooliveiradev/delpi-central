-- V002 — seed do checklist mensal PROC-0072: 53 itens (doc 95).
-- CP-D04=A: versão inicial permanece DRAFT; publicação é operação
-- administrativa autorizada, nunca automática na migration.
-- Conteúdo sanitizado: sem bancos, contas, pessoas ou valores.
BEGIN;

INSERT INTO controllership_finance.checklist_template
    (code, name, description, created_by)
VALUES
    ('monthly-closing-checklist', 'Checklist de Fechamento Mensal',
     'Checklist mestre do fechamento mensal da Controladoria (PROC-0072).',
     '00000000-0000-4000-8000-000000000001');

INSERT INTO controllership_finance.checklist_template_version
    (template_id, version, status, created_by)
SELECT template_id, 1, 'DRAFT', '00000000-0000-4000-8000-000000000001'
  FROM controllership_finance.checklist_template
 WHERE code = 'monthly-closing-checklist';

INSERT INTO controllership_finance.checklist_template_item
    (version_id, item_key, sort_order, sheet, name, purpose,
     origin_kind, recipient_area, applicability, branch_scope,
     totvs_report_ref, requirement_notes)
SELECT v.version_id, i.item_key, i.sort_order, i.sheet, i.name,
       i.purpose, i.origin_kind, i.recipient_area, i.applicability,
       i.branch_scope, i.totvs_report_ref, i.requirement_notes
  FROM (VALUES
       ('CK-E-01', 1, 'ELETRONICO', 'Extratos bancários — conta 01', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-02', 2, 'ELETRONICO', 'Extratos bancários — conta 02', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-03', 3, 'ELETRONICO', 'Aplicações financeiras — conta 02', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', 'Aplicações devem detalhar tarifas IR/IOF.'),
       ('CK-E-04', 4, 'ELETRONICO', 'Extratos bancários — conta 03', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-05', 5, 'ELETRONICO', 'Aplicações financeiras — conta 03', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', 'Aplicações devem detalhar tarifas IR/IOF.'),
       ('CK-E-06', 6, 'ELETRONICO', 'Fatura de cartões', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-07', 7, 'ELETRONICO', 'Extratos bancários — conta 04 (agência 1)', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-08', 8, 'ELETRONICO', 'Extratos bancários — conta 04 (agência 2)', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-09', 9, 'ELETRONICO', 'Extratos bancários — conta 04 (agência 3)', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-10', 10, 'ELETRONICO', 'Extratos bancários — conta 05', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-11', 11, 'ELETRONICO', 'Extratos bancários — conta capital', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', NULL),
       ('CK-E-12', 12, 'ELETRONICO', 'Aplicações financeiras — conta 05', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R13', 'Aplicações devem detalhar tarifas IR/IOF.'),
       ('CK-E-13', 13, 'ELETRONICO', 'Relação de baixas a receber (PDF)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R02', NULL),
       ('CK-E-14', 14, 'ELETRONICO', 'Relação de baixas a receber (Excel)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R02', NULL),
       ('CK-E-15', 15, 'ELETRONICO', 'Relação de baixas a pagar (Excel)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R01', NULL),
       ('CK-E-16', 16, 'ELETRONICO', 'Relação de baixas a pagar (PDF, por natureza)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R01', NULL),
       ('CK-E-17', 17, 'ELETRONICO', 'Relação de baixas a pagar (PDF, por data)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R01', NULL),
       ('CK-E-18', 18, 'ELETRONICO', 'Importações — Swift', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'MATRIX', 'R14', NULL),
       ('CK-E-19', 19, 'ELETRONICO', 'Contrato de câmbio', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R14', NULL),
       ('CK-E-20', 20, 'ELETRONICO', 'Encontro de contas', NULL, 'MIXED', 'CONTABIL', 'REQUIRED', 'BOTH', 'R14', NULL),
       ('CK-E-21', 21, 'ELETRONICO', 'Fechamentos de importação (planilha de cálculo + arquivo ACSI)', NULL, 'EXTERNAL', 'CONTABIL', 'REQUIRED', 'BOTH', 'R14', NULL),
       ('CK-E-22', 22, 'ELETRONICO', 'Valor de estoque — Entradas e Saídas ou P7 (layout bloco H)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'MATRIX', 'R05', 'Aceita alternativa P7 em layout bloco H (R03).'),
       ('CK-E-23', 23, 'ELETRONICO', 'CPV — Kardex armazém 01', NULL, 'TOTVS', 'FISCAL', 'REQUIRED', 'BOTH', 'R06', NULL),
       ('CK-E-24', 24, 'ELETRONICO', 'Inventários — Kardex armazéns 01 e 99 (doc INVENT)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'BOTH', 'R07', NULL),
       ('CK-E-25', 25, 'ELETRONICO', 'Faturamento × MOD', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'BOTH', 'R09', NULL),
       ('CK-E-26', 26, 'ELETRONICO', 'Material em processo', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'BOTH', 'R08', NULL),
       ('CK-E-27', 27, 'ELETRONICO', 'Relatório de faturamento da filial (chicotes e plugues separados)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'BRANCH', NULL, 'Produtor R-ID pendente (CP-D03 / TO_INVENTORY).'),
       ('CK-E-28', 28, 'ELETRONICO', 'Itens de NF por centro de custo (chicotes e plugues separados)', NULL, 'TOTVS', 'CONTABIL', 'REQUIRED', 'BOTH', 'R10', NULL),
       ('CK-E-29', 29, 'ELETRONICO', 'Relação de NF de venda a desconsiderar (grupo 9035)', NULL, 'TOTVS', 'FISCAL', 'REQUIRED', 'MATRIX', 'R11', NULL),
       ('CK-E-30', 30, 'ELETRONICO', 'Conferência de itens com valor 0 no relatório CPV', NULL, 'TOTVS', 'FISCAL', 'REQUIRED', 'BOTH', 'R11', NULL),
       ('CK-F-01', 31, 'FISICO', 'Notas Fiscais — consumo', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, 'Classificação de finalidade na NF física pendente de detalhamento (CP-D02 / TO_INVENTORY).'),
       ('CK-F-02', 32, 'FISICO', 'Notas Fiscais — MP', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BRANCH', NULL, 'Obrigatório na Filial; aplicabilidade na Matriz pendente (TO_INVENTORY).'),
       ('CK-F-03', 33, 'FISICO', 'Notas Fiscais — insumo', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-04', 34, 'FISICO', 'Notas Fiscais — embalagem', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, 'Distinguir embalagem comum × embalagem de apresentação.'),
       ('CK-F-05', 35, 'FISICO', 'Notas Fiscais — frete (sobre vendas e remessas)', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-06', 36, 'FISICO', 'Notas Fiscais — devoluções de venda', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-07', 37, 'FISICO', 'Notas Fiscais — Simples Nacional (todos, inclusive MP)', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-08', 38, 'FISICO', 'Notas Fiscais — ativo imobilizado', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-09', 39, 'FISICO', 'Notas Fiscais — energia elétrica', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-10', 40, 'FISICO', 'Notas Fiscais — telecomunicações', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-11', 41, 'FISICO', 'Notas Fiscais — notas de serviço', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-12', 42, 'FISICO', 'Faturas', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, 'Exceto energia elétrica e telecomunicações.'),
       ('CK-F-13', 43, 'FISICO', 'Relatório de planos de saúde e odontológico', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-14', 44, 'FISICO', 'Relatório de coparticipação', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-15', 45, 'FISICO', 'Seguros', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-16', 46, 'FISICO', 'Guias com comprovante de pagamento', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-17', 47, 'FISICO', 'Relatório de recebidos de cliente específico (PDF)', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-18', 48, 'FISICO', 'Pagamentos antecipados', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-19', 49, 'FISICO', 'Relatório de viagens e movimentação veicular', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-20', 50, 'FISICO', 'Rescisões e pagamento de férias', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-21', 51, 'FISICO', 'Invoices', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-22', 52, 'FISICO', 'Associações (mensalidade)', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL),
       ('CK-F-23', 53, 'FISICO', 'Boletos e pagamentos sem nota fiscal', NULL, 'EXTERNAL', NULL, 'REQUIRED', 'BOTH', NULL, NULL)
       ) AS i(item_key, sort_order, sheet, name, purpose,
             origin_kind, recipient_area, applicability,
             branch_scope, totvs_report_ref, requirement_notes)
  JOIN controllership_finance.checklist_template_version v
    ON v.version = 1
  JOIN controllership_finance.checklist_template t
    ON t.template_id = v.template_id
   AND t.code = 'monthly-closing-checklist';

COMMIT;
