# Plano de continuidade — integrações de relatórios e CLARA (29/10/2026)

> **Estado:** TARGET/PLANNED; plano autorizado para preparação e gates, **não** autorização de runtime. **Autoridade:** doc 118 (processo), doc 85 (BR), doc 83/84 (provas), doc 113 (fluxo), HEAD (implementação), TÉO (AS-IS). Revisão de roadmap não equivale a homologação de relatórios nem publicação do corpus CLARA.

## 1. Baseline (verificar novamente no HEAD antes da execução)

- **R01/R02:** consultas de baixas financeiras operacionais existentes; R02 permanece com lacuna do produtor custom E1. Não confundir consulta SE5 com equivalência oficial.
- **R03/P7:** consulta operacional com escopos `all_products` e `mp_pi_pa`; CSV/PDF; paridade MATR460 pendente (E2).
- **R05/MATR320:** consulta operacional e CSV/PDF; paridade oficial pendente.
- **R08/MATR989/H02:** consulta operacional e CSV/PDF; paridade oficial pendente (E8).
- **Conciliação analítica:** composição de saldos SB9 classificada `IDENTITY_ONLY`; não comprova paridade entre emissões independentes nem conclui P3.
- **P3 governado:** registro e validação próprios, não dependentes de cadastro documental; análises, filtros e exportações são independentes da superfície Documentos e interações.
- **Frontend:** REWORK-013 é somente refinamento pontual de cartões, indicadores, matriz, navegação e Help; PDF terá verificação final separada. Não presumir entrega do 013 antes do relatório e SHA.

## 2. Sequência recomendada dos próximos gates

| Ordem | Pacote | Escopo operacional proposto | Reuso e evidências | Condição de entrada / bloqueio |
|---|---|---|---|---|
| 014 | R06 CPV/Kardex + R07 INVENT | Consulta por competência/filial/produto/armazém; movimentos, resumos, investigação de custos e inventário; exportação só após contrato | MATR910, regras BR-R06/BR-R07 e DR-09/DR-10, `matr910_dlp.prx`, SD1/SD2/SD3, saldo SB9 anterior; CPV existente `REUSE_PARTIAL` | Gate transversal: owner, grão, filtros, custos, `as_of`, produtores/consumidores, authz e comparação com artefatos `cpv 09 26 matriz.xlsb`/`Invent.xlsb`. Não equiparar paridade histórica a G6 |
| 015 | R10 Centro de Custo + R11 NF a desconsiderar | Consultas analíticas separadas, sem exclusões automáticas em relatórios vizinhos | EDAPP/SD1/SD2; DR-11/DR-12; view CC `REUSE_PARTIAL` | E10 (classificação manual Direto/Ind/Adm) e E11 (finalidade/exclusões) verificados; não inventar classificação |
| 016 | R09 Faturamento × MOD | Faturamento, tempos, horas e custos por filial com proveniência e ausências explícitas | DLP204; SD2/SHY/SG2/SH1/SBZ; DR-13 | E9 (SP/producer), lacunas dos tempos/custos e G5 `INCONCLUSIVE`; sem custo zero substituto |
| 017 | R12 estado de custos + R15 cutoff | Painel READ de MATA320/MATA300/MATA330/MATA280, `MV_ULMES`/SB9 por filial; nada de executar ERP | doc 118 OPS-01..04, doc 85 BR-R12/R15; T03/owner canônico | Confirmar contrato existente de estado e proveniência; sem execução de rotinas/write no Portal |
| Depois | R04, R13, R14 | Consumo por OP e fontes financeiras/externas | R04 produtor/artefato ausente; R13 bancos/aplicações; R14 importação/câmbio | `DECISION_REQUIRED` se owner, fonte, contrato ou integração externa não estiver decidido |

**Cada pacote exige:** HEAD + git status, instructions/.cursor, inspeção dos contratos e producers/consumers atuais, owner+RQ/AC, gate documental e de segurança antes de runtime, implementação mínima page-by-page, testes, smoke, evidências, SHA e revisão GPT. Nada está autorizado a instalar nova permissão por relatório; somente `controllership-finance.access`, `controllership-finance.manage` e `controllership-finance.access.dre` (esta apenas documentos DRE autorizados).

## 3. Análises transversais vinculadas

1. CPV e evolução de custo por produto/filial, com divergências e encadeamento de movimentos (R06).
2. Inventário/ajustes de estoque, sem exclusão ou retificação automática (R07).
3. Despesas por centro de custo e tratamento explícito das classificações manuais (R10).
4. NF a desconsiderar como seleção investigativa, sem propagação de exclusão implícita (R11).
5. Faturamento versus mão de obra direta, custos e tempos não disponíveis como nulos explícitos (R09).
6. Estado de fechamento de custo, virada e cutoff por filial (R12/R15).
7. Paridade independente das emissões oficiais MATR320/MATR460/MATR989: frente de homologação distinta do controle `IDENTITY_ONLY`; comparar mesmo período, filial, escopo, versão e `as_of`.

## 4. CLARA — atualização de conhecimento e responsabilidades

**Verificação READ de 29/10/2026:** `get_catalog` informa corpus `5d546360-ab37-410c-80e8-e1a5748ed56e`, publicado em **27/10/2026 09:11:19 -03**, com 56 fontes e 1.713 itens. É anterior aos REWORK-010/011/012 e a este plano. **Corpus atualizado: NÃO COMPROVADO / sincronização PENDING.** As ferramentas CLARA disponíveis nesta sessão são de leitura, análise e operações governadas do fechamento; nenhuma ferramenta de refresh/publicação do corpus foi exposta.

**Handoff ao owner do pipeline CLARA:** incluir este documento, doc 118/113/119 e evidências técnicas atuais no processo oficial de ingestão; gerar versão/hash novos; publicar por caminho governado; verificar `get_catalog` + `list_knowledge_sources` + buscas com citações após a publicação. Não atualizar hashes/versões à mão e não afirmar que a CLARA já sabe do plano antes dessa prova.

**Diretrizes funcionais para CLARA após publicação:** explicar a fila 014→017 e os bloqueios; diferenciar `consulta operacional`, `paridade oficial`, `conciliação analítica IDENTITY_ONLY` e `P3 governado`; não recalcular divergência na CLARA (usar owner/BFF READ); não associar análise/exportação a documento cadastrado; não executar Protheus; exigir evidências e permissão efetiva nas leituras. Para novas consultas, fonte de runtime = tools READ, conhecimento = corpus com `citation_locator` e classificação de evidência.

## 5. Próximo passo autorizado

**Próximo gate proposto:** `CF-PROC0072-R06-R07-CONTRACT-GATE-014` — READ/VERIFY do reuso MATR910 e CPV existente, contratos, grão, `as_of`, autorizações, provas dos XLSB e RQ/AC; entregar gate documental, não scaffold/runtime automático. Em paralelo, encaminhar refresh CLARA ao owner. A homologação humana G6 continua `PENDING` quando não executada.

**ATUALIZAÇÃO — 29/10/2026:** o gate `CF-PROC0072-R06-R07-CONTRACT-GATE-014` foi **executado** — contratos TARGET, RQ/AC (doc 23), matriz de segurança, matriz de paridade e plano conjunto Portal×CLARA registrados em **[doc 122](./122-gate-contratual-r06-r07-matr910-2026-10-29.md)**.

**ATUALIZAÇÃO 2 — 29/10/2026:** `CF-PROC0072-R06-R07-IMPLEMENTATION-015` **executado** — D-O1..D-O4 aprovadas pelo PO em sessão (doc 122 §9). Implementado: engine `stock-kardex` (api-delpi, UNION SD1/SD2/SD3 + custo `as_of` TTAT + saldo SB9 anterior), `/financeiro/stock-kardex` (+`/summary`, `/products/{code}`, `/export`), `/financeiro/inventory-adjustments` (+`/summary`, `/export`), `/financeiro/cpv` dedicado; proxies BFF `/closing/competences/{period}/reports/*`; páginas MFE + Help + matriz R01–R15; CLARA 43→48 tools READ; export CSV/PDF com watermark «PARIDADE OFICIAL PENDENTE». **PENDENTE:** paridade × XLSB (E8), deploy governado + smoke (E9) e homologação humana G6.

**ATUALIZAÇÃO 3 — 30/10/2026:** a fila **015** (R10 centro de custo + R11 NF a desconsiderar) avançou com `CF-PROC0072-R10-R11-CLARA-COMPARISON-CONTRACT-GATE-019` **executado como gate documental** — inventário `PROVEN` dos produtores EDAPP/SD1/SD2, matriz de reuso, contratos TARGET, arquitetura de comparação universal R01–R15, matriz de compatibilidade semântica, segurança, modelo de conhecimento CLARA e decisões D-01..D-08 (`DECISION_REQUIRED`) registrados em **[doc 126](./126-gate-contratual-r10-r11-comparacao-clara-2026-10-30.md)**; ledger em doc 23 §gate-019. **Zero runtime/migration/deploy** — implementação aguarda pacote de decisões do PO (E10/E11).

**ATUALIZAÇÃO 4 — 30/10/2026:** `CF-PROC0072-R10-R11-DECISION-EVIDENCE-GATE-020` **executado** — D-01..D-08 **formalizadas pelo PO** (D-03 `controllership-finance-api` como owner da comparação; D-04 comparação como capability `analyze` da CLARA, sem tela genérica; D-05 três resultados funcionais; D-06 fichas R01–R15; D-07 sem export comparativo; D-08 parciais honestos fail-closed). Vídeo e artefatos **verificados diretamente**: R10 Reg 17/18 `CONFIRMED_BY_VIDEO_AND_DOC` (casos `0401`/`0404` provados no artefato); **R11 sem demonstração no vídeo** — `PENDING_EVIDENCE`. Catálogo de divergências DV-R10-01..06/DV-R11-01..04, contratos revisados com `findings[]` e modelo de fichas no [doc 126 §14–§19](./126-gate-contratual-r10-r11-comparacao-clara-2026-10-30.md); ledger doc 23 §gate-020. Próximo gate: autorização de implementação (E1–E10) quando o PO aprovar.

**ATUALIZAÇÃO 5 — 31/10/2026 (stage-04):** handoff de corpus **executado no ambiente local** — `CF-PROC0072-CLARA-KNOWLEDGE-R01-R15-IMPLEMENTATION-STAGE-04` ingeriu este plano, a base canônica, as fichas R01–R15 e a ficha de processo no pipeline vigente: corpus local `f9857be6` (88 fontes / 2.170 itens; rollback `57109de5`). **Publicação produtiva permanece `PENDING_APPROVAL`** — a nota de handoff §4 segue valendo para o gate produtivo: verificar `get_catalog`/`list_knowledge_sources` + buscas com citação após o publish autorizado.


## Adendo — Estado de integracao produtivo (30/10/2026)

release stage-05 (30/10/2026, host `srv-api`, checkout `297068f1b7` — inclui `9f66f8b8e0`) publicado por `up-prod-sequential.sh`: api-delpi `sha256:d46e307ad3e6`, BFF `sha256:7f0e7db69114`, MFE `sha256:8530bbc8f797`; corpus produtivo `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (88 fontes / 2.186 itens, 17 fichas, 100% `PORTAL_ACCESS`). Cadeia api-delpi -> BFF -> Portal -> CLARA verificada live para
R10/R11 e comparacao; regressao R03/R05/R06/R07/R08/CPV em producao: 200.

**ATUALIZAÇÃO 6 — 31/10/2026 (Ciclo 3, execução master PO):** pacote **017 (R12/R15)** avançou — inventário consolidado em **[doc 128](128-ciclo3-inventario-consolidado-r04-r09-r12-r13-r14-r15.md)** e gate contratual em **[doc 129](129-ciclo3-gate-contratual-r12-r15-estado-fechamento.md)** com contrato TARGET aprovado (projeção governada de estado, C3-D02=A). Implementada a cadeia api-delpi `/financeiro/closing-state` → BFF `/closing/competences/{period}/cost-closing-state` → MFE `cost-closing-state` → CLARA `read(report.cost_closing_state)`; matriz R12/R15 → `STATE_VIEW`. **PENDENTE:** enablement gate `FINANCEIRO_CLOSING_STATE_ENABLED`, smoke/paridade live, homologação G6. Pacotes R04 (GAP-01), R09 (E6-D1..D6/E9), R13/R14 (D-5) permanecem `DECISION_REQUIRED`/`BLOCKED_BY_EVIDENCE`.
