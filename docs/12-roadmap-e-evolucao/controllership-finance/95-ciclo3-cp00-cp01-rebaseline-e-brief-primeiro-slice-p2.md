# Documento 95 — Ciclo 3 · CP00/CP01 verificados e brief do primeiro slice P2

**Rodada:** `CF-C3-E2E-CP00-CP01-REBASELINE-VERIFY-001` (2026-10-24)
**Base:** `b445ecf969` (main, worktree limpa). **Modalidade:** READ → VERIFY →
INVENTORY → TEST (não destrutivo) → DOCUMENT. `IMPLEMENTATION_AUTHORIZED=NO`.
**Authorities:** instruções oficiais, `.cursor` aplicáveis, docs 08–13, 23,
37, 39–42, 45, 47–49, 59, 76, 79, 84–94. Roadmap vigente: [93](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md)
(atualizado com as evidências desta rodada, não substituído).

> Proteção: a planilha original do PO foi lida localmente em modo somente
> leitura e **não** foi versionada. Instituições bancárias, contas, pessoas e
> valores não são reproduzidos; linhas usam referência estável `aba!linha`.

---

## 1. CP00 — Matriz do checklist original

### 1.1 Fonte e estrutura (PROVEN — leitura direta)

Arquivo privado `Arquivos de envio - contabil para fechamento mensal.xlsx`
(cópia local do PO). Abas e dimensões: `Eletronico` A1:J46, `Fisico` A1:J42,
`Planilha1` A1:N71. Cabeçalho de colunas (linhas 1–2): **D = Componentes ·
Matriz**, **E = Componentes · Filial**, **F = Indústria · Matriz (legado,
excluído por decisão do PO — doc 59 CK-F)**, **G = destinatário**
(`Contabil`/`Fiscal`), legenda **I2 verde = "Enviar"**. Verde = envio
esperado no contexto, **não** entrega executada nem aceite.

Lacunas da própria fonte (aplicáveis a todos os itens): a planilha **não
registra responsável de produção, validador, prazo, formato obrigatório nem
regra de validação** — esses campos ficam `TO_INVENTORY` com owner
Controladoria. Uma única célula contém um nome de pessoa em vez de `x`
(Eletronico!D3) — tratada como anotação de responsável, não publicada.
Células com preenchimento de tema (não-RGB) em Eletronico!E28, E29, linha 25
e Fisico!D4 são **sinais auxiliares não decodificados** — `TO_INVENTORY`
(CK-B), nunca convertidos em N/A.

### 1.2 Aba Eletrônico — 30 itens em escopo

Legenda Escopo: `M` = verde em Matriz; `F` = verde em Filial. Portal: P2
(item/evidência), P3 (estoque/cutoff), P5 (pacote por destinatário).

| ID | Ref | Item (sanitizado) | Escopo | Dest. | Origem | R-ID | Portal | Automação | Estado |
|---|---|---|---|---|---|---|---|---|---|
| CK-E-01..12 | Eletronico!3–14 | Extratos bancários, aplicações, conta capital e fatura de cartões — **12 linhas, uma por conta/instituição** (aliases `EXT-BANK-01..12`) | M | Contábil | externa (banco) | R13 | P2 anexo · P5 | **bloqueada** — documento externo, não vira SQL | `TO_INVENTORY` (G2–G4 R13 PENDING) |
| CK-E-12n | Eletronico!16 | Nota: aplicações devem detalhar tarifas IR/IOF | — | — | regra de conteúdo | R13 | P2 requisito do item | — | `PROVEN` (texto) |
| CK-E-13 | Eletronico!20 | Relação de baixas a receber — PDF | M | Contábil | TOTVS `DLP06R01` | R02 | P2 · P5 | candidata (paridade de artefato PROVEN; fonte ausente E1) | `PROVEN` artefato / API `NOT_EQUIVALENT` (§2.A) |
| CK-E-14 | Eletronico!21 | Relação de baixas a receber — Excel | M | Contábil | TOTVS `DLP06R01` | R02 | P2 · P5 | idem | idem |
| CK-E-15 | Eletronico!22 | Relação de baixas a pagar — Excel | M | Contábil | TOTVS `FINR190` | R01 | P2 · P5 | candidata (G1–G5 PASS) | `PROVEN` artefato / API `NOT_EQUIVALENT` |
| CK-E-16 | Eletronico!23 | Baixas a pagar — PDF ordenado por natureza | M | Contábil | TOTVS `FINR190` | R01 | P2 · P5 | candidata (layout por natureza) | idem |
| CK-E-17 | Eletronico!24 | Baixas a pagar — PDF ordenado por data | M | Contábil | TOTVS `FINR190` | R01 | P2 · P5 | candidata | idem |
| CK-E-18 | Eletronico!28 | Importações — Swift | M | (sem G) | externa | R14 | P2 anexo | bloqueada | `TO_INVENTORY` (destinatário em branco na fonte) |
| CK-E-19 | Eletronico!29 | Contrato de câmbio | M | Contábil | externa | R14 | P2 anexo | bloqueada | `TO_INVENTORY` |
| CK-E-20 | Eletronico!30 | Encontro de contas | M+F | Contábil | externa/mista | R14 | P2 anexo | bloqueada | `TO_INVENTORY` |
| CK-E-21 | Eletronico!31 | Fechamentos de importação (planilha de cálculo + arquivo ACSI) | M+F | Contábil | externa (ACSI) | R14 | P2 anexo | bloqueada | `TO_INVENTORY` |
| CK-E-22 | Eletronico!35 | Valor de estoque — Entradas e Saídas **ou** P7 (layout bloco H) | M+F | Contábil | TOTVS `MATR320` / `MATR460` | R05 / R03 | P2 · P3 | R05 G1–G5 PASS; R03 G4/G5 PENDING (E2) | parcial |
| CK-E-23 | Eletronico!36 | CPV — Kardex armazém 01 | M+F | **Fiscal** | TOTVS `MATR910` | R06 | P2 · P3 | candidata (G1–G5 PASS; E7) | `PROVEN` artefato |
| CK-E-24 | Eletronico!37 | Inventários — Kardex 01 e 99 (doc = INVENT) | M+F | Contábil | TOTVS `MATR910` | R07 | P2 · P3 | candidata (G1–G5 PASS; E7) | `PROVEN` artefato |
| CK-E-25 | Eletronico!38 | Faturamento × MOD | M+F | Contábil | TOTVS `DLP204` | R09 | P2 | candidata (G5 INCONCLUSIVE; E9) | parcial |
| CK-E-26 | Eletronico!39 | Material em processo | M+F | Contábil | TOTVS `MATR989` | R08 | P2 · P3 | candidata (G1–G5 PASS; E8) | `PROVEN` artefato |
| CK-E-27 | Eletronico!40 | Relatório de faturamento da filial (chicotes e plugues separados) | **F** | Contábil | TOTVS (produtor não identificado) | **nenhum** | P2 | **sem investigação C2** | `TO_INVENTORY` — **gap novo** |
| CK-E-28 | Eletronico!41 | Itens de NF por centro de custo (chicotes e plugues separados) | M+F | Contábil | EDAPP→SD1 | R10 | P2 | candidata (G1–G5 PASS; E10) | `PROVEN` artefato |
| CK-E-29 | Eletronico!42 | Relação de NF de venda a desconsiderar (grupo 9035) | M | **Fiscal** | EDAPP→SD2 | R11 | P2 | candidata (G1–G5 PASS; E11) | `PROVEN` artefato |
| CK-E-30 | Eletronico!43 | Conferência: itens com valor 0 no relatório CPV | M+F | **Fiscal** | verificação sobre R06/R11 | R06/R11 | P2 requisito de validação | regra BR-R11 (CPV-zero estrutural) | `PROVEN` regra; aceite G6 PENDING |
| CK-E-n45 | Eletronico!45 | Nota: CPV da filial consolidado **e** separado chicotes/plugues (grupo 9048) | — | — | regra de conteúdo | R06 | P2 requisito | — | `TO_INVENTORY` (regra não reconstruída no C2) |
| CK-E-n46 | Eletronico!46 | Nota: P7 para a contabilidade com layout H | — | — | regra de conteúdo | R03 | P2 requisito | — | `PROVEN` (texto) |

### 1.3 Aba Físico — 23 itens em escopo

Todos são **documentos comprobatórios externos** (sem R-ID, sem automação
SQL), destino P2 (anexo + validação) e P5. Escopo M+F verde em todos,
exceto CK-F-02 (MP: verde só em Filial; Matriz com sinal de tema
`TO_INVENTORY`).

| IDs | Ref | Grupo | Itens |
|---|---|---|---|
| CK-F-01..11 | Fisico!3–13 | Notas Fiscais (Fiscal) | consumo*, MP, insumo, embalagem*, frete s/ vendas e remessas, devoluções de venda, Simples Nacional, ativo imobilizado, energia elétrica, telecomunicações, notas de serviço |
| CK-F-12..23 | Fisico!29–40 | Contábil | faturas*, planos de saúde/odontológico, coparticipação, seguros, guias com comprovante, relatório de recebidos de cliente específico (PDF), pagamentos antecipados, viagens e movimentação veicular, rescisões e férias, invoices, associações, boletos/pagamentos sem NF |
| CK-F-n16/n23/n42 | Fisico!16, 23, 42 | Notas | consumo exige classificação de finalidade na NF física; embalagem comum × apresentação; faturas exceto energia/telecom |

Estado comum: `TO_INVENTORY` para responsável, validador e regra de
satisfação; destinatário da aba Físico **não** está na coluna G (vazio) —
`TO_INVENTORY` por item.

### 1.4 Planilha1

69 linhas de vocabulário (categorias de materiais/consumo/despesas).
Classificação mantida: **catálogo candidato P6**, não item de envio (doc 59).

### 1.5 Achados CP00

1. **53 itens em escopo** (30 eletrônicos + 23 físicos) — todos registrados;
   nenhum item removido.
2. **Não há 1:1 com R01–R15**: 37 itens não têm R-ID (12 extratos R13
   agrupados, 4 importação R14 agrupados, 23 físicos sem R-ID; 1 item
   eletrônico **sem nenhuma investigação** — CK-E-27 faturamento da filial).
3. **R04, R12 e R15 não são entregáveis do checklist** — são etapas de
   processo (consumo por OP, fechamento de custos, cutoff). Devem aparecer
   em P3/P1, não como itens P2.
4. Destinatário Fiscal ≠ Contábil em CK-E-23/29/30 — relevante para P5.
5. Campos responsável/validador/prazo/regra de validação **inexistentes na
   fonte** → owner Controladoria (pedido individualizado §6).

**Saída CP00:** matriz completa com lacunas individualizadas →
**CP00 = PASS (rastreabilidade de itens)**; preenchimento de
responsável/validador/regra = `TO_INVENTORY` com owner.

## 2. CP01 — Auditoria das páginas existentes

### 2.0 Testes executados (HEAD `b445ecf969`, 2026-10-24 06:50–06:54 -03)

| Suíte | Comando / ambiente | Resultado |
|---|---|---|
| MFE vitest | `npx vitest run` (WSL, node) | **91/91 PASS** (12 arquivos; inclui Settlements 16, StockInventory 19) |
| MFE estruturais | `node --test src/**/*.structural.test.mjs` | **25/25 PASS** (manifest, apiBoundary, closingTablePanel, homeHonesty, helpCoverage) |
| MFE typecheck | `tsc -p tsconfig.app.json --noEmit` | **PASS** |
| BFF | `pytest tests` em `infra-controllership-finance-api:latest`, `--network none`, código do HEAD montado | **83/83 PASS** |
| api-delpi | 12 arquivos settlements/stock-inventory/closure em `infra-api-delpi:latest`, `--network none`, HEAD montado | **72/72 PASS** |
| Build MFE (`vite build`) | — | `TEST_NOT_RUN` |
| Smoke humano E2E (Portal→BFF→api-delpi com JWT real) | sem usuário/token humano autorizado nesta sessão | `TEST_NOT_RUN` |
| Smoke de dados read-only (SQL do HEAD, SELECT agregado, `db_datareader`) | container api-delpi local | executado — §2.A/§2.B |

Cobertura BFF verificada por nome de teste: bearer ausente → 401;
`manage` sem `access` → 403; sem permissões → 403; service principal → 403;
`rbac_unavailable` → 503; `scope_unavailable` → 403 tipado; S2S scope/client
negado → código tipado; upstream 401/403/timeout/5xx/corpo inesperado →
mapeados; `source_missing`/`incomplete` propagados; filial `02` como filtro
simples.

### 2.A FinancialSettlementsPage

Cadeia: MFE `FinancialSettlementsPage` → BFF `GET /closing/financial-settlements`
(`side=payable|receivable`, período, natureza, tipo, ordenação, paginação) e
`/summary` → api-delpi `/financeiro/settlements/*` (S2S + Bearer delegado,
`settlement_scope` fail-closed).

**Errata de premissa (EXECUTION_DRIFT documental):** a fonte do contrato
**não é SE5**. `settlements_sql.py` lê **`FK2010`/`FK1010`** (eventos de baixa)
+ `FK7010` + `SE2/SE1` + `SED`. O doc 88 §1.1/§2 registrou "SE5" — corrigido
por errata no próprio doc 88. A paridade oficial R01/R02 do Ciclo 2 foi
reconstruída sobre **SE5** com o WHERE do `FINR190`/`DLP06R01` (doc 84 §1–§2).

Smoke read-only set/2026 (contrato do HEAD) × artefato oficial (doc 84):

| Lado | API (FK) eventos | API Σ | Oficial linhas | Oficial Σ Total Baixado | Δ |
|---|---|---|---|---|---|
| Pagar | 978 | 6.833.994,25 | 948 | 6.019.825,92 | +30 / +814.168,33 |
| Receber | 676 | 5.255.121,66 | 657 | (VO 5.301.533,30; Total Baixado não totalizado no doc 84) | +19 / não comparável |

Qualidade retornada pela API: `unresolved_branch` = **978/978** e
**676/676** (filial não resolvida em 100% dos eventos), `missing_document`
3, `missing_nature` 7 (pagar).

| Pergunta | Resposta |
|---|---|
| Consulta operacional implementada? | **Sim** (código + 3 camadas de testes PASS) |
| Comportamento testado? | **Sim** — unit/contract; E2E humano `TEST_NOT_RUN` |
| Smoke real autorizado? | dados read-only **sim**; usuário humano **não** |
| Totais oficiais? | **Não** — DTO declara `officialTotals=false` |
| Reproduz FINR190/DLP06R01? | **Não** — população FK ≠ população SE5 filtrada (Δ quantificado acima) |
| Atende item do checklist? | **Não diretamente** — CK-E-13..17 exigem o artefato oficial |
| Evidência automatizada P2 sem novo contrato? | **Não** |
| Gaps | (1) contrato oficial R01 sobre SE5 com WHERE do fonte (regras PROVEN doc 85); (2) R02 depende de E1; (3) filial não resolvida; (4) layouts PDF por data/natureza |

Classificação: **consulta auxiliar preservada** (`REUSE_PARTIAL`); não é
entregável P2.

### 2.B StockInventoryPage

Cadeia: MFE `StockInventoryPage` → BFF `GET /closing/stock-inventory`
(`period`, `branch all|01|02`, `report_scope all_products|mp_pi_pa`,
`warehouse`) → api-delpi `/financeiro/stock-inventory` (S2S
`stock-inventory.read`, cliente allow-listed, scope fail-closed) →
`SB9010`+`SB1010` por `B9_DATA` = último dia da competência.

Smoke read-only (SQL do HEAD):

| Competência | Presença por filial | Total `all_products` | Total `mp_pi_pa` |
|---|---|---|---|
| 2026-08 | 01=4.720 · 02=3.093 | 14.620.961,79 | — |
| 2026-09 | 01=4.812 · 02=3.117 | 14.469.584,01 | f01 3.588.581,88 · f02 10.002.994,97 |
| 2026-10 | nenhuma | 0 linhas → use case retorna `source_missing` | — |

Presença por filial **idêntica** às cardinalidades SB9 do Ciclo 2 (R15).
P7 oficial set/2026 (doc 84 §3): EM ESTOQUE 3.591.191,36 + EM PROCESSO
355.240,51. O P7 é emitido por saldo `as_of` da emissão excluindo armazém
99 + MATR989 por OP; o contrato lê SB9 (inclui armazém 99, sem MATR989).

| Pergunta | Resposta |
|---|---|
| Consulta histórica funciona? | **Sim** — presença, totais e `source_missing` verificados em dados |
| Snapshot confiável no escopo demonstrado? | **Sim** para SB9 (cardinalidade = C2); writer interno pendente E5 |
| Corresponde ao MATR460/P7? | **Não** — DTO `officialP7=false`, `parityStatus=TEST_NOT_RUN` |
| Parâmetros/abrangência equivalentes? | **Não** — base SB9 ≠ `as_of` emissão; armazém 99 e EM PROCESSO tratados diferente |
| Evidência de conciliação? | Não pelo contrato; a conciliação P7 do C2 foi por reconstrução própria (doc 84 §3) |
| Contribui para o fechamento? | Sim, como **visão auxiliar de snapshot persistido** (P3/P1: "persistido por filial") |
| Preservar como auxiliar? | **Sim** |
| Delta até o oficial | contrato P7 (`as_of` emissão, exclusão loc 99, EM PROCESSO MATR989, layout H) + E2 (parâmetros/fonte MATR460) + P3 conciliação `E/S − P7 − H02 = 0,00` |

**Saída CP01:** (A) consultas operacionais funcionais, seguras e testadas →
**PASS(A) com E2E humano `TEST_NOT_RUN`**; (B) entregável oficial →
**FAIL(B) para ambas** (não equivalentes, já declaradas pelo DTO). PASS(A)
não implica PASS(B).

## 3. Brief do primeiro slice P2 (proposta para GO)

### 3.1 Escopo mínimo proposto — `P6-MIN + P2-READ`

1. **P6-min (catálogo/template versionado):** template v1 com os **53 itens
   do §1** (id estável `CK-*`, aba, finalidade, escopo M/F, destinatário,
   origem TOTVS/externa/mista, R-ID opcional, applicability). Publicação
   somente por `manage` efetivo + escopo administrativo (RQ-P6-01/02/09).
   **Sem UI P6 completa** — carga controlada por migration/seed versionado.
2. **P2-read:** abrir competência = **snapshot** do template vigente
   (RQ-P2-01); listar itens da competência por filial/destinatário/origem
   com estado inicial `EXPECTED` (verde ≠ entregue); detalhe do item com
   requisitos e vínculos (R-ID, notas CK-*n*); deep link/F5; Help no
   mesmo gate (RQ-P2-12).
3. **Fora do slice:** upload/storage (C04), validação/rejeição (C05),
   automação de relatórios (C06), P3/P4/P5, CLARA tools, página
   Contabilidade (doc 91).

### 3.2 Contratos (candidatos, não aprovados)

- BFF (owner do estado do Portal): `GET /closing/competences`,
  `POST /closing/competences` (abertura → snapshot), `GET
  /closing/competences/{period}/items`, `GET .../items/{itemId}`;
  admin: `GET/POST /admin/checklist-templates` (draft/publish). Nomes
  finais no gate de contrato.
- Sem mudança na api-delpi; Core apenas como authority de effective
  permissions (sem permission nova).

### 3.3 RQ/AC do slice (ledger doc 23)

| RQ | AC verificável | Teste |
|---|---|---|
| RQ-P6-01 | draft não publica; publish exige `manage`+escopo | positive + negative (`access` → 403) |
| RQ-P6-02 / RQ-P2-01 | publicar v2 não altera competência aberta em v1 | sibling: 2 competências, 2 snapshots |
| RQ-P6-03 | inativação prospectiva, sem delete | negative delete |
| RQ-P2-02 | REQUIRED não pode virar N/A (server-side) | negative |
| RQ-P2-12 | Help do item e da competência | helpCoverage estrutural |
| (novo, a registrar) RQ-P2-13 | item verde do template aparece como `EXPECTED`, nunca `DELIVERED/VALIDATED` | positive + negative |
| (novo) RQ-P2-14 | itens sem R-ID (externos) não exibem automação | negative |
| AuthZ | `access` lista; sem `access` 403; RBAC indisponível 503; filial é filtro | positive/negative/sibling |

### 3.4 Stop conditions

`DECISION_REQUIRED` abaixo não resolvida; necessidade de permission nova;
escrita no ERP; storage de arquivo; alteração de manifest além de rota
aprovada no gate; divergência entre template e planilha sem owner.

## 4. Decisões materiais reais

| ID | Decisão | Evidência | Opções | Recomendação |
|---|---|---|---|---|
| **CP-D01** | Owner físico e persistência de competência/template (doc 45 **D3=C DEFERRED**) | BFF C&F hoje sem banco; BFFs irmãos (supplies, commercial, requests, travel-expenses) têm schema próprio no `postgres-plugins` + `migrations_runner` | (A) schema próprio da `controllership-finance-api` no `postgres-plugins`, padrão irmão; (B) catálogo declarativo versionado em repositório sem persistência (só leitura; inviabiliza snapshot por competência); (C) outro owner | **A** — único que atende RQ-P2-01/RQ-P6-02 sem inventar padrão |
| **CP-D02** | Preenchimento de responsável/validador/regra por item | ausente na planilha (§1.1) | (A) Controladoria fornece antes do slice; (B) slice 1 entra sem esses campos (`TO_INVENTORY` visível) e C05 os exige | **B** — não bloqueia leitura; bloqueia C05 |
| **CP-D03** | CK-E-27 (faturamento da filial) sem R-ID | §1.5 | (A) abrir R16 de investigação; (B) tratar como anexo manual até investigação | **B** agora + abrir investigação |

Decisões **não reabertas**: CLARA-D01=B; doc 91 (adiada); CPV vivo; E6=C;
permissions atuais.

## 5. CLARA — coerência do trilho paralelo

Doc 93 §0/§4 e doc 94 coerentes. Capacidades READ reais hoje expostas
futuramente como tools (M02): `viewer-context`, settlements (+summary),
stock-inventory — **com rótulo auxiliar** (`officialTotals=false`,
`officialP7=false`). Nenhuma PREPARE/ACT possível: não há operação de
escrita no Portal. Dependências: CLARA-D02..D05 + slice P2 para qualquer
tool de checklist. Nada criado.

## 6. Pedidos a owners (sem duplicar E1–E12)

| Owner | Pedido | Critério de aceite |
|---|---|---|
| Controladoria | responsável de produção, validador, regra de satisfação e prazo para os 53 itens; destinatário dos itens Físico; significado dos sinais de tema (E28, E29, linha 25, Fisico!D4) | planilha/registro por `CK-*` |
| Controladoria + TI/ERP | produtor de CK-E-27 (faturamento da filial chicotes/plugues) | rotina + artefato de set/2026 |
| TI/ERP | E1 (fonte DLP06R01), E2 (MATR460) — já existentes | conforme doc 82 |

## 7. Estado dos checkpoints (para doc 93)

- **CP00:** `PASS` — 53/53 itens rastreados com lacunas individualizadas
  (responsável/validador `TO_INVENTORY`).
- **CP01:** (A) `PASS` com E2E humano `TEST_NOT_RUN`; (B) `FAIL` —
  não equivalentes aos oficiais, quantificado. Páginas preservadas como
  auxiliares.
- **CP02/CP03:** `PENDING` — brief pronto; bloqueado por **CP-D01**.


## 8. Decisão expressa do PO — CP-D01=A (2026-10-24)

**CP-D01=A — APPROVED para owner/persistência e design contratual:** manter o estado próprio do workflow de competência, template versionado e snapshot no bounded context **`controllership-finance-api`**, com **schema próprio isolado no `postgres-plugins`**, seguindo o padrão vigente da plataforma, sujeito ao inventário de migrations, runners e conectividade existentes. O PO selecionou a opção A após GPT REVIEW do relatório CP00/CP01.

**Alcance:** esta aprovação fecha a escolha de **ownership/persistência**, anteriormente adiada pelo D3=C no doc 45 para o contexto P1; não revisa permissões, não escolhe tabelas/DDL detalhados, não homologa contrato HTTP, nem confere autorização de implementação. `IMPLEMENTATION_AUTHORIZED=NO` para `P6-MIN + P2-READ` até gate transversal explícito e GO específico por slice.

**Próximo gate:** `CF-C3-P6-MIN-P2-READ-CONTRACT-GATE-001` — inventariar padrão real `postgres-plugins`, migrations runner, schemas e BFF; definir versão/template/competência/snapshot, migrations reversíveis, portas/adapters, fail-closed Core, contratos DTO/BFF, RQ/AC e testes positive/sibling/negative. O gate deverá produzir design e solicitação de autorização; não implementar runtime nesta rodada. CP-D02 (responsável/validador) e CP-D03 (CK-E-27) permanecem pendentes, sem autoaprovação.
