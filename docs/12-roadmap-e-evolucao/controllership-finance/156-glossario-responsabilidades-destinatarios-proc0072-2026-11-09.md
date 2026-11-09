# PROC-0072 — Glossário funcional e vínculo de destinatário documental (decisão PO 2026-11-09)

**Natureza:** decisão funcional/documental; **DOCUMENTATION_ONLY** para GitHub. Não altera aplicação, manifesto, grants, contratos, migrations, deploy nem base curada CLARA por si só.
**Estado:** decisão PO aprovada para os 14 itens do rascunho V2; aplicação no checklist é evidência operacional separada (read-back CLARA). Antes de publicar requer revisão da versão e testes dos caminhos de entrega.
**Autoridade de contexto:** docs 118 (base canônica PROC-0072), 83/85 (produtores), 113/115 (destinatários, acesso e pacote), 09 (P2 checklist); fichas R01/R02/R03/R13 e processo-fechamento.

## 1. Vocabulário controlado (não misturar dimensões)

| Termo | Definição operacional | Distinção |
|---|---|---|
| **Financeiro** | Origem operacional dos relatórios de títulos pagos/recebidos e dados financeiros. Módulo 06 Protheus `02.9.0006`; relatórios de envio à Contabilidade em visão **consolidada filiais 01+02**. | Área/fonte de dados; não é automaticamente destinatário. |
| **Estoque/Custos** | Origem operacional de Registro de Inventário P7/Bloco H (MATR460) e demais controles de estoque. Módulo 04 `02.9.0004`; evidência P7/Resumo **individual por filial 01 e 02**. | Área/fonte de dados; não é permission code. |
| **Controladoria (interna)** | Responsável pela coleta, conferência, conciliação, preparação e acompanhamento do fechamento da competência; efetua a entrega. | Responsável funcional/emitente, não público destinatário. |
| **Contabilidade externa** | Equipe/prestador externo que **recebe e trata** documentos de fechamento disponibilizados pela Controladoria para análises contábeis e providências conforme contratação. | No PROC-0072, **destinatário funcional** dos 14 documentos atuais. Responsabilidades legais/tributárias específicas do prestador não inferidas. |
| **Fiscal/Tributário** | Finalidade/especialidade de obrigações e tratamento fiscal. | Pode atuar no mesmo prestador, mas entrega `FISCAL` somente quando houver destinatário e fluxo fiscal específico confirmado; não classificar como fiscal apenas pela origem/documento. |
| **DRE** | Em contabilidade, Demonstração do Resultado do Exercício. No vocabulário operacional do Portal, **apelido do público externo consumidor de documentos** que apoia esse tratamento contábil. | Não é módulo ERP, permission por documento nem nova área `recipient_area`. |
| **Área destinatária** | `recipient_area` do item e do pacote, com enum atual `CONTABIL`/`FISCAL`. | Define agrupamento e seleção dos documentos por pacote, não a identidade da pessoa. |
| **Permissão de acesso DRE** | `controllership-finance.access.dre` no manifesto/guard atuais: acesso restrito à experiência documental. | Capability ≠ área `CONTABIL`; não substitui atribuição `RECIPIENT`, pacote `SUBMITTED` e autorização fail-closed. |

## 2. Decisão funcional aprovada (2026-11-09)

1. **Emitente/responsável:** Controladoria interna coordena o fechamento; produz/reúne relatórios dos módulos Estoque/Custos, Financeiro e fontes bancárias externas.
2. **Destinatário dos 14 itens atuais do rascunho V2:** Contabilidade externa, equipe operacionalmente chamada “DRE”; configurar **`recipient_area=CONTABIL` para todos os 14 itens**, mantendo demais propriedades e V2 em `DRAFT`.
3. Reservar **`FISCAL` exclusivamente para futuras entregas fiscais específicas**, mediante validação da finalidade e do consumidor. Não duplicar itens entre `CONTABIL` e `FISCAL` automaticamente.
4. Preservar **`EST-`** (2 P7 por filial), **`FIN-`** (3 relatórios consolidados) e **`EXT-`** (9 extratos por conta/aplicação); cada documento tem entrega individual no checklist. Nenhum pacote/subpacote novo.
5. O cadastro da área é **necessário para selecionar os itens no pacote por área**. **Não** concede acesso automaticamente: acesso efetivo = permissão DRE + vínculo `RECIPIENT` válido na área/pacote + versão `SUBMITTED` contendo a versão documental, conforme contrato vigente. `ATTACHED != VALIDATED`; `FINALIZAR != ENVIAR`.
6. Não publicar V2 nem alterar V1, runtime ou direitos de usuário por esta decisão. Não guardar nomes pessoais, dados bancários, PDFs financeiros ou gravações neste repositório público.

## 3. Vínculos verificáveis

- **Fontes/produtores:** doc 118 §§2/6 e doc 83: P7 `MATR460` módulo 04; pagos `FINR190` módulo 06; recebidos `DLP06R01` custom (fonte ainda faltante); documentos bancários R13 externos (não módulo 06).
- **Contrato UI:** `plugins/controllership-finance/src/features/closing/checklistAdminShared.tsx` expõe `CONTABIL`/“Contábil” e `FISCAL`/“Fiscal”. `ChecklistVersionPage.tsx` apresenta `null` como “A definir”.
- **Contrato HTTP:** `controllership-finance-api/controllership_finance_app/interface/http/routes/admin_checklist_routes.py` aceita `recipient_area: CONTABIL|FISCAL|null`.
- **Pacote:** `closing_package_repository.py::_applicable_areas` deriva áreas de itens não cancelados com destinatário; a seleção de itens do pacote filtra `i.recipient_area = area`.
- **Autorização:** manifesto do MFE, BFF `authz.py` e doc 115 §11 (RW03/RW04) distinguem `access.dre` de `access`/`manage`. A permissão DRE existente é um fato do HEAD, mas **diverge da instrução-base do projeto que enumera apenas duas permissões**: manter esse conflito marcado para reconciliação de authority, **sem introduzir/revogar grants** por este registro.

## 4. Verificação e lacunas (gates)

- **CHECKLIST_WRITE:** após alteração da V2, reler versão/metadata da CLARA e confirmar `status=DRAFT`, 14 itens, os mesmos 14 `item_key`, 14× `recipient_area=CONTABIL` e V1 `PUBLISHED`; caso contrário **INCONCLUSIVE/REWORK**.
- **CLARA_KNOWLEDGE:** o corpus atualmente recupera Controladoria (origem) e DRE/Contabilidade (consumo), mas não diferencia explicitamente Controladoria interna, Contabilidade externa, Fiscal, DRE como demonstração e apelido do público. Este documento é **fonte candidata a ingestão** pelo fluxo governado de curadoria/manifests/publicação; **commit GitHub ≠ conhecimento produtivo CLARA**.
- **P5_RUNTIME:** read-back da configuração do rascunho **não** comprova entrega real; exigem teste com competência efetivamente aberta, snapshot vigente, pacote `CONTABIL`, `RECIPIENT` correto, submissão, projeção DRE e autorização negativa. Não executar smoke real/produção sem gate.
- **DOCUMENTAL:** conferir a exigência bancária por conta/filial e BNB; confirmar as adições de Contas a Pagar/Receber em Aberto e Ajustes de Inventário. Confirmar PDFs financeiros efetivamente consolidados e P7 separado por filial; `branch_scope=BOTH` não prova população do PDF.
- **GOVERNANÇA:** não criar permissão, área `DRE`, contrato ou tipo de pacote sem decisão material e gate transversal. Reconciliar divergência do freeze de permissions com mudanças comprovadas no HEAD (docs 115/manifesto).
- **CÓDIGO/TESTES:** nenhuma alteração nesta etapa; `TEST_NOT_RUN` para suíte/smoke. `git status` local não disponível via conector GitHub; não inferir árvore de trabalho limpa.

## 5. Conhecimento recomendado para CLARA (curadoria futura)

Quando questionada “Quem é a DRE?” ou “Quem é o Contábil?” no PROC-0072, responder **com contexto e fonte**, sem equiparar nomes:
- “DRE” pode significar a demonstração contábil, mas **neste fluxo de documentos** identifica o público externo que recebe a entrega.
- A **Controladoria interna** prepara/valida; a **Contabilidade externa** consome; `CONTABIL` classifica o pacote; `access.dre` determina capability, sem acesso irrestrito.
- `FISCAL` é outra **finalidade destinatária**, não automática mesmo se o P7 tenha função fiscal.
- Evitar afirmar que a CLARA já assimilou este glossário até publicação de corpus curado + recuperação citada validada.

**Registro de decisão:** PO aprovou modelo nesta conversa em 2026-11-09. **Execução técnica do rascunho:** auditar separadamente via CLARA `checklist.draft_update` + `template.version` read-back.
