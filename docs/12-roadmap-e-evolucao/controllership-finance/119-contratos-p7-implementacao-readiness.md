# 119 — Contratos definitivos P7 e readiness de implementação (PROC-0072)

**EXECUTION_ID:** `CF-PROC0072-P7-IMPLEMENTATION-READINESS-005`
**Natureza:** `DOCUMENTATION_ONLY + DEFINITIVE_TECHNICAL_DISCOVERY + CONTRACT_CLOSURE`
**Base HEAD:** `b385380924c79a3fe717dfcad49dd5f469f90b8a` (preflight) · HEAD na escrita: `6fc0d7cb98` (trabalho concorrente DÉLIA Task 07 — não tocado)
**Data:** 2026-10-28
**Status:** `CONTRATO TARGET` — referência executável da próxima implementação

> Este documento fecha o levantamento técnico do Registro de Inventário P7
> (MATR460) e define os contratos para implementação. **Zero alteração de
> runtime nesta execução.** Cada regra carrega seu estado probatório;
> nenhuma hipótese foi promovida a regra.

---

## 0. Leitura obrigatória

- Base canônica do processo: doc 118 (DEC-12, §9.1, §15.1).
- Contrato operacional anterior: doc 49 (§11 inventário, §12 veredito
  equivalência `mp_pi_pa`).
- Catálogo de regras: doc 85 (`BR-R03-007/008/009`, `BR-R08-009`).
- Evidência-mestre: doc 80 §35 (decomposição das emissões), §41 (paridade
  MATR989 completa), §36 (errata de classificação).
- Paridade monetária: doc 84. Handoff E2: doc 82 §2.1.

**Legenda probatória:** `PROVEN` (demonstrado em dados/artefato/código) ·
`PROVEN_STRUCTURE` (estrutura provada, valores dependentes de estado
temporal) · `PENDING_EXTERNAL` (depende de evidência fora do alcance do
Devin) · `TARGET` (contrato futuro aprovado para desenho) ·
`STALE_EVIDENCE` (estado do banco diverge do estado da emissão).

---

## 1. Matriz de fontes

| Fonte | Estado | Uso nesta execução |
|---|---|---|
| Doc 118 (base canônica) | lido integralmente | origem das decisões DEC-12, gates |
| Doc 80 §35/§36/§41 | reutilizado | modelo poder3, timeline, fórmula MATR989 |
| Doc 82 §2.1 | reutilizado | pacote E2 pendente (owner TI/ERP) |
| Doc 85 BR-R03-* / BR-R08-* | reutilizado+estendido | regras atualizadas |
| Doc 49 §11/§12 | reutilizado | contrato exploratório e veredito |
| `Estoque.pdf` (folha 101) / `Resumo Estoque.pdf` (folha 74) | artefatos oficiais | alvos de paridade |
| `Material em processo.xlsb` (MATR989 analítico) | artefato oficial | decomposição EM PROCESSO (§41) |
| `A460UNIT.prw` | `CODE_PRESENT` | hook de custo, não de escopo (doc 118) |
| `matr460.prx` / RPO | `SOURCE_MISSING` | não bloqueante para `all_products`; residual p/ `mp_pi_pa` |
| `matr989.prx` | `SOURCE_MISSING` | fórmula provada por dados (§41) — não bloqueante |
| SX1 `MTR460` (25 perguntas) | catálogo completo (doc 85 BR-R03-008) | sem parâmetro de tipo; param 02 `Saldo em Poder 3º?` |
| Banco TOTVS `DELPI` (SELECT-only via `delpi-api-delpi`) | **acessível nesta execução** | verificação de esquema, QTNP/QTER, SF4, SB6, totais SB9 |
| api-delpi (código) | inspecionado | contratos, DTO, SQL, owner canônico de tipos, módulo SB6, ponte `as_of` |
| controllership-finance-api (código) | inspecionado | proxy `/closing/stock-inventory`, authz fail-closed, fluxo documental |
| MFE `StockInventoryPage.tsx` | inspecionado | seleção explícita de escopo já existente |
| SSH/hosts remotos | indisponível (sem VPN) | não usado |

---

## 2. Matriz de reutilização

| Item | Herdado de | Verificação nova nesta execução |
|---|---|---|
| `report_scope=all_products\|mp_pi_pa` | doc 49 §9, `constantes.py`, DTO, BFF, MFE | confirmado ponta a ponta (MFE→BFF→api-delpi) |
| `B1_TIPO IN ('MP','PI','PA')` | `constantes.py` + doc 85 BR-R03-009 | SQL e dados conferem |
| Owner canônico de tipos | `domain/totvs/protheus_product_types.py` | sem segunda taxonomia |
| Competência→snapshot (`B9_DATA` último dia) | `stock_inventory_request.py` + use case | idem |
| `source_missing`/`incomplete`/`no_matching_items` | use case + testes | preservado |
| Fórmula EM PROCESSO = MATR989 | doc 80 §41 | **reutilizada integralmente** (validação abaixo) |
| Ponte `as_of` SB9+SD3 | `stock_value_historical_sql.py` | canônica para saldos históricos |
| Módulo poder-de-terceiros SB6 | `protheus_third_party_materials.py` + rota + doc padrão | semântica conferida no banco |
| Regra ROL de exclusão poder3 | `rol-divergencia-protheus.md` (#0001164) | mecanismo confrontado (§6) |
| Modelo QTNP@emissão | doc 80 §35.D | **recomputado** — ver §4/§7 |
| DEC-12 (dois escopos) | doc 118 | não reaberta |

---

## 3. Fatos novos verificados no banco (2026-10-28)

Todas as consultas foram SELECT-only dentro do container `delpi-api-delpi`,
contra `DELPI` (192.168.1.230), `WITH (NOLOCK)`. Nenhum DDL/DML.

1. **SB9 `20260930` existe nas duas filiais** — filial `01`: 4.812 linhas;
   filial `02`: 3.117 linhas. (O smoke anterior de `source_missing` na 01
   era de uma competência/época diferente.)
2. **Filial `01` = MATRIZ** — cabeçalho dos PDFs oficiais (`01 MATRIZ`) e
   `SYS_COMPANY` (DELPI COMPONENTES / DELPI INDÚSTRIA DE COMPONENTES).
3. **Totais SB9@30/09 filial 01** (atuais): todos os locais =
   **3.893.096,17**; ex-99 = **3.599.373,79**; loc 99 = **293.722,38**.
4. **Drift MP `STALE_EVIDENCE` confirmado:** EM ESTOQUE oficial =
   3.591.191,36; SB9 ex-99 atual = 3.599.373,79 → **Δ +8.182,43,
   inteiramente em MP** (MP ex-99 atual 3.079.867,24 vs 3.071.684,80 do
   ciclo 2). PA/PI/II ex-99 atuais **bit a bit iguais ao oficial**
   (190.511,24 / 24.528,60 / 266.321,46). Causa: regravação do SB9@0930
   após a emissão (21/10 19:13, doc 80 §35.F) + revalorização MP
   (mesma classe do residual R05 +8.631,74, doc 80 §30).
5. **`B2_QTNP` só existe em linhas `B2_LOCAL='01'`** — 111 produtos MP,
   710.034,862 u (filial 01). Idem `B2_QTER` — 50 produtos MP, 6.788,40 u.
   Poder-de-terceiros é posição do produto registrada no almoxarifado.
6. **Semântica confirmada:** `B2_QTNP` = material próprio em poder de
   terceiros (em terceiros); `B2_QTER` = material de terceiros em nosso
   poder (de terceiros). `SB9` **não possui campos poder3** — a posição na
   data de fechamento não está no snapshot; é reconstruída por `SB2`
   corrente + movimentos `F4_PODER3` posteriores.
7. **`F4_PODER3` em uso:** valores `N`/`R`/`D` no catálogo SF4 (60+ TES).
   Direção verificada: `SD2 R` = remessa p/ terceiro (QTNP+);
   `SD1 D` = retorno de poder3 (QTNP−); `SD1 R` = entrada de material de
   terceiro (QTER+); `SD2 D` = devolução ao dono (QTER−).
8. **QTNP@emissão = QTNP atual para MP filial 01** — nenhum movimento
   `SD2-R`/`SD1-D` pós-30/09 sobre os produtos QTNP (os movimentos de
   02/10 do timeline §35.F foram direção QTER, não QTNP).
9. **SB6 aberta ⊆ produtos com SB2** — todas as remessas SB6 abertas MP
   pertencem a produtos que têm posição SB2; `B6_SALDO>0` = 221 remessas
   tipo `D` (717.487,62 u) + 80 tipo `E` (5.690,30 u), filial 01.
10. **`B1_TPMAT`** em SB1: valores `1` (53.999 produtos) / `2` (1.351) —
    flag de cadastro, domínio distinto do poder3 (doc padrão
    `materiais-terceiros-sb6.md`). Não é mecanismo do P7.
11. **Exclusão MP do resumo é por PRODUTO, não por quantidade** — a soma
    `VINI1` das linhas SB9 loc 01 dos produtos `QTNP>0` = valor do conjunto
    inteiro (589.427,63 no estado atual), não `QTNP×custo` (748.181 /
    613.065 / 833.596 por custo — todos descartados no ciclo 2).

---

## 4. Poder de terceiros — regras fechadas

### 4.1 Vocabulário canônico (owner: api-delpi)

| Conceito | Fonte Protheus | Semântica | Estado |
|---|---|---|---|
| Material próprio **em** terceiros | `SB2.B2_QTNP` (`B2_LOCAL='01'`) | estoque próprio fisicamente fora | `PROVEN` (dados) |
| Material de terceiros **conosco** | `SB2.B2_QTER` (`B2_LOCAL='01'`) | estoque alheio sob nossa custódia | `PROVEN` (dados) |
| Tracking de beneficiamento | `SB6` + `VW_PD3_BENEF_RETORNOS` | remessas cliente→DELPI e retornos | `PROVEN` (módulo canônico existe) |
| Flag de movimento | `SF4.F4_PODER3` ∈ {N,R,D} | natureza poder3 da TES | `PROVEN` (catálogo extraído) |
| Flag de cadastro | `SB1.B1_TPMAT` | produto "de terceiro" (cadastro) | domínio distinto — **não usar no P7** |

### 4.2 Regras de inclusão/exclusão por escopo

**`all_products` (P7 completo — análise interna + conciliação):**

- EM ESTOQUE = Σ `SB9.B9_VINI1` de **todos os locais exceto `99`**
  (`MV_LOCPROC`), incluindo posições poder3 — `PROVEN` (total oficial
  casa com ex-99 integral no estado de emissão; PA/PI/II exatos hoje).
- EM PROCESSO = fórmula MATR989 (§5) — `PROVEN`.
- Poder3 **entra** nos totalizadores (material próprio em terceiros é
  estoque da empresa; material de terceiro conosco carrega valor
  próprio de registro) — `PROVEN` pelo fechamento do total.

**`mp_pi_pa` (P7 documental DRE):**

- `B1_TIPO IN ('MP','PI','PA')` — `PROVEN` (PA/PI bit a bit).
- **Exclusão adicional em MP:** produtos com posição poder3 na emissão
  — direção e magnitude `PROVEN`; população exata `PENDING_EXTERNAL`
  (E2). Melhor modelo: conjunto de produtos `B2_QTNP>0` no `as_of`.
- Os 19 produtos MP com `QTNP>0` **fora** do SB9 (estoque físico zero)
  não produzem linha — a exclusão atua sobre o estoque físico do
  produto, consistente com `QTNP` ser posição e não armazém.

### 4.3 Pseudocódigo determinístico (TARGET — dependente de E2 para ativação)

```text
poder3_set(branch, as_of) =
    { p ∈ SB1(B1_TIPO='MP') : QTNP_p(as_of, branch) > 0 }

QTNP_p(as_of) = B2_QTNP_now(p)
              − Σ SD2.quant (F4_PODER3='R', emissao > as_of)
              + Σ SD1.quant (F4_PODER3='D', emissao > as_of)

mp_pi_pa.EM_ESTOQUE =
    Σ SB9.VINI1 [filial, data_fechamento, local<>'99', tipo∈{MP,PA,PI}]
  − Σ SB9.VINI1 [linhas de produtos ∈ poder3_set, local<>'99']

mp_pi_pa.EM_PROCESSO =
    MATR989(as_of) filtrado a {MP,PA,PI} \ poder3_set   (medida a definir — §5.3)
```

**Não promovido:** o modelo `QTNP@emissão` permanece `PENDING` como regra
oficial até E2 (linhas de produto da folha 74 ou parâmetros da emissão).
O contrato foi desenhado para aceitar a população poder3 como
**componente de regra plugável** (`ThirdPartyPositionPolicy`), de modo
que a implementação não precise ser refeita quando E2 confirmar a
semântica exata.

### 4.4 Casos de borda registrados

| Caso | Tratamento |
|---|---|
| Produto QTNP>0 sem linha SB9 | não gera linha; entra na reconciliação poder3 como memória de cálculo |
| Produto com QTNP=0 mas QTER>0 | permanece no relatório (material de terceiro não é excluído pelo recorte observado — `PENDING` se oficial inclui QTER) |
| `F4_PODER3` ≠ `N` genérico | **proibido** excluir indiscriminadamente — direção importa (DEC-PO) |
| SB6 aberto sem QTNP | evidência existe (`<PRODUTO-QTNP-A>`, 71,21); não é regra sem E2 |
| Poder3 de PA/PI | QTNP PA = 11 produtos/1.000,36 u — a emissão oficial não os excluiu (PA idêntico) → **a exclusão oficial recai só sobre MP** (`PROVEN` por observação; mecanismo `PENDING`) |

### 4.5 Reconciliação monetária do recorte (atualizada)

| Dimensão | Alvo oficial | Melhor modelo | Residual | Classe |
|---|---|---|---|---|
| MP EM ESTOQUE excluído | 587.698,28 | produtos `QTNP>0` = 587.621,85 (estado 23/10) / 589.427,63 (estado atual) | 76,43 (23/10) | `STALE_EVIDENCE` + `PENDING_EXTERNAL` |
| MP EM PROCESSO excluído | 77.251,73 | loc99-QTNP 62.538,71 + RE-DE-OP-QTNP 10.873,96 = **73.412,67** (modelo novo, medida MATR989 por produto) | **−3.839,06** | `PENDING_EXTERNAL` — medida de processo do resumo não decomposta ao centavo |

> O modelo de processo anterior (79.194,35) somava componentes globais
> (RE9 inteiro = 12.410,85) que não pertencem todos a produtos QTNP —
> a medida correta é **MATR989 por produto** (§5), não loc99 + RE global.

---

## 5. Estoque em processo — contrato fechado

### 5.1 Fórmula canônica (doc 80 §41 — `PROVEN` nos dois sentidos)

```text
EM_PROCESSO(as_of) =
      Σ SB9.VINI1 [filial, B9_DATA=data_fechamento, B9_LOCAL='99']        -- físico sem OP
    + Σ ( Σ SD3.D3_CUSTO1 [CF LIKE 'RE%', emissao<=data_fechamento]
        − Σ SD3.D3_CUSTO1 [CF LIKE 'DE%', emissao<=data_fechamento] )
      por par (produto × OP) tal que a OP está VIVA no as_of:
        ¬∃ SD3.D3_CF LIKE 'PR%' da OP com emissao <= as_of+1dia
        ∧ OP não cancelada-sem-produzir (C2_DATRF vazio na emissão)
```

Decomposição homologada 09/2026 filial 01: 293.273,09 (loc99 sem OP) +
588,50 (RE0) + 254,44 (RE1 loc 01 — fatia PI) + 48.713,64 (RE2) +
12.410,85 (RE9) = **355.240,51 = EM PROCESSO oficial exato**.

### 5.2 Regras derivadas

- `EM_ESTOQUE + EM_PROCESSO = TOTAL_GERAL` — exato, `PROVEN`.
- EM PROCESSO **não é** `SB9 loc 99` (subestima ~17% — 293.722 vs
  355.240). O armazém 99 cobre só o bloco físico sem OP.
- Grão do bloco alocado = linha SD3 (movimento), não documento nem OP.
- `RE1` em loc ≠99 **permanece em EM PROCESSO** (material alocado a OP
  que fisicamente ainda está no almoxarifado) — distinção posição ×
  localização.
- Corte intra-dia não observável: `PR0` no próprio dia da emissão é a
  fronteira conhecida (`as_of`-dia).

### 5.3 Componente de implementação

| Necessidade | Estado | Owner |
|---|---|---|
| Saldo RE−DE por produto×OP `as_of` | **lacuna real — serviço inexistente** (doc 80 §41.G, `BR-R08-009 TARGET`) | api-delpi |
| OP viva no `as_of` (proxy `PR0`) | regra provada, sem repositório canônico | api-delpi |
| `stock_value_historical_sql.py` (SB9+SD3 bridge) | canônico — reusar para base física | api-delpi |
| `_fetch_wip_proxy_rows` (`B2_VATU1` loc 50/98/99) | parcial/corrente — **não usar para P7 oficial** | api-delpi |
| `ops_abertas_sql.py` (`C2_QUANT>C2_QUJE`) | predicado **divergente** — MATR989 exige `QUJE=0`+sem `PR0`; não reusar | api-delpi |

---

## 6. ROL e CPV vs P7 — confronto de equivalência

| Dimensão | ROL (`FinancialRepository.get_rol`) | CPV (`cpv_query_repository`) | P7 |
|---|---|---|---|
| Natureza | faturamento (fluxo) | custo de vendas (fluxo) | posição de inventário (estoque) |
| Fonte | SD2+SD1 (elegibilidade TES) | SD2 CFOP∈{5101,5124,6101,6124} | SB9+SB1+SD3+SC2+SB2 |
| Exclusão poder3 | `F4_DUPLIC='S'` + famílias TES 524/525/534/540/541/550/551/590… (receita) | implícita pelo conjunto de CFOPs de venda | por posição/produto (parâmetro `Saldo em Poder 3º?`) |
| Veredito | **parcial — princípio equivalente, mecanismo distinto** | idem | — |

Conclusão `PROVEN`: nenhuma query de faturamento pode ser copiada para o
P7. O que é reutilizável: o **princípio documentado** (material de
terceiro não integra receita nem estoque próprio do recorte DRE) e os
componentes de classificação (`SF4` já é dimensão conhecida). O incidente
#0001164 prova que remessas/retornos de beneficiamento não são receita —
analogamente, o recorte `mp_pi_pa` prova que posições poder3 não entram
no inventário documental DRE.

---

## 7. Paridade dos dois escopos — matriz final

Artefatos de 09/2026, filial 01, data-base 30/09/2026.

### 7.1 `all_products` (alvo: 3.946.431,87)

| Dimensão | Resultado | Classe |
|---|---|---|
| Filial | 01 MATRIZ | `PASS` |
| Data-base / `as_of` | 30/09/2026 ~16:16 01/10 | `PASS` |
| EM ESTOQUE (estrutura = SB9 ex-99) | 3.591.191,36 | `PASS` estrutura — PA/PI/II/outros **bit a bit hoje** |
| EM ESTOQUE MP | drift +8.182,43 (revalorização pós-emissão, SB9 regravado 21/10) | `STALE_EVIDENCE` |
| EM PROCESSO (= MATR989) | 355.240,51 exato por decomposição | `PASS` |
| TOTAL | = EM ESTOQUE + EM PROCESSO | `PASS` estrutura |
| Paridade monetária centavo hoje | impossível — estado SB9 ≠ estado emissão | `STALE_EVIDENCE` documentado |

### 7.2 `mp_pi_pa` (alvo: 2.976.967,56)

| Dimensão | Resultado | Classe |
|---|---|---|
| Tipos (PA/PI) | valores idênticos ao completo | `PASS` |
| MP EM ESTOQUE | exclusão poder3: alvo 587.698,28; modelo 587.621,85 (23/10) | `INCONCLUSIVE` — residual 76,43 |
| MP EM PROCESSO | alvo 77.251,73; medida por produto 73.412,67 | `INCONCLUSIVE` — residual −3.839,06 |
| Mecanismo oficial de recorte | sem parâmetro de tipo no `MTR460`; poder3 = candidato param 02 | `PENDING_EXTERNAL` (E2) |
| TOTAL | não reproduzido ao centavo | `INCONCLUSIVE` |

### 7.3 Resíduos individualizados (AC-10)

| Residual | Valor | Origem conhecida | Fechável? |
|---|---|---|---|
| EM ESTOQUE MP drift | +8.182,43 | revalorização MP + regravação SB9 21/10 (classe R05) | não — estado emissão irrecuperável; validar por nova emissão |
| Exclusão poder3 estoque | 76,43 | conjunto exato de produtos ambíguo (subset-sum) + drift | E2 (linhas da folha 74) |
| Exclusão poder3 processo | −3.839,06 | medida MATR989-por-produto vs medida do resumo | E2 |
| R05 MP MATR320 | +8.631,74 | mesma revalorização MP (doc 80 §30) | já documentado |

---

## 8. Contratos definitivos

### 8.A — Consulta P7 oficial (`TARGET`)

```text
GET /financeiro/stock-inventory-oficial          (api-delpi — NOVO)
GET /closing/stock-inventory-oficial             (BFF — NOVO proxy)

Query:
  competence      YYYY-MM (obrigatório) → data_fechamento = último dia do mês
  branch          'all' | '01' | '02'   (obrigatório, escopo de dados)
  report_scope    'all_products' | 'mp_pi_pa'   (obrigatório — DEC-12)
  warehouse       opcional (filtro analítico de EM ESTOQUE)
  product_type    opcional (filtro analítico dentro do escopo)
  page, page_size paginação (padrão existente)

Resposta (itens):
  items[]: product_code, description, unit, product_type, warehouse,
           quantity, unit_cost, stock_value, third_party_position
           {qtnp, qter, in_poder3_set} , in_process_flag
  totals:  stock_total (EM ESTOQUE), process_total (EM PROCESSO),
           grand_total, by_product_type[], by_warehouse[]
  status:  available | incomplete | source_missing | no_matching_items
  parity:  parity_state (proven|provisional|unverified), known_residuals[]
  provenance: producer='matr460', emission_id, emitted_at, closing_date,
              effective_parameters{saldo_poder3, saldo_processo, custo},
              folio (quando houver), rpo_version (quando houver),
              snapshot_date, as_of, recipient ('dre' quando aplicável)
```

Decisões de contrato (fechadas):
- **Um único cálculo canônico** parametrizado por `report_scope` — dois
  escopos, uma rotina (DEC-12). O componente poder3 entra como
  `ThirdPartyPositionPolicy` plugável até E2 confirmar a semântica.
- `mp_pi_pa` **não fica disponível** como total oficial até o mecanismo
  poder3 estar `PROVEN` — até lá o escopo responde `status:
  parity_unverified` com a decomposição conhecida, **nunca** total
  fabricado.
- O endpoint exploratório `/financeiro/stock-inventory` (SB9) **permanece
  intacto** e rotulado `officialP7: false` — é a consulta auxiliar
  operacional já homologada.
- `source_missing` nunca é total zero. `incomplete` quando parte das
  filiais pedidas não tem snapshot.
- Filial é escopo de dados, não permissão.

### 8.B — Totalização

```text
EM_ESTOQUE(scope)   = Σ SB9.VINI1 [filial, data_fechamento, local<>'99',
                                   tipos(scope), ¬poder3_set se mp_pi_pa]
EM_PROCESSO(scope)  = MATR989(as_of) [filial, tipos(scope),
                                      ¬poder3_set se mp_pi_pa]
TOTAL_GERAL(scope)  = EM_ESTOQUE + EM_PROCESSO   (sempre igual por construção)
```

Custo: `B9_VINI1`/`B9_CM*` no estado do fechamento (lista de custo =
médio — provada pelo binding PA/PI). Movimentos pós-fechamento não
alteram a competência; regravações do SB9 alteram a reprodução — daí
`parity_state` + `known_residuals` obrigatórios no contrato.

### 8.C — Exportação (`TARGET`)

```text
GET .../stock-inventory-oficial/export?format=csv|xlsx|pdf

Cabeçalho obrigatório: competência, filial, escopo (rótulo PT),
data de fechamento, emission_id/as_of, producer, versão,
hash de conteúdo (SHA-256 do payload), gerado_por, gerado_em.
Layout: itens + totalizadores por tipo e armazém + bloco provenance.
Escopo mp_pi_pa exportável apenas como "documento oficial provisório"
com watermark/flag parity_state até homologação E2.
```

### 8.D — Integração documental DRE (`TARGET` — reusa fluxo existente)

Infra existente (verificada): `closing_document_service.py`,
`closing_document_repository.py`, `closing_document_storage.py`,
`closing_package_repository.py`, `closing_recipient_repository.py`,
rotas `documents_routes`/`packages_routes`/`received_documents_routes`.

```text
1. Controladoria gera export do escopo mp_pi_pa → documento
   {type:'P7-inventory-register', competence, branch, emission_id,
    content_hash, parity_state}
2. Documento é anexado a um closing_package (pacote da competência)
3. Submissão do pacote → estado SUBMITTED → RECIPIENT (Contabilidade/DRE)
4. Recipient com controllership-finance.access.dre consulta o pacote
   submetido — nunca a consulta operacional
5. Snapshot documental imutável: a consulta P7 pode mudar de estado
   (SB9 regravado), o documento submetido não.
Audit trail: document_id, package_id, submitted_by/at, recipient,
   download events — já suportados pelo fluxo existente.
```

**Sem nova permissão, sem nova BFF, sem novo MFE.** `access.dre` não
aciona geração interna.

### 8.E — Segurança/RBAC (verificado no código)

| Camada | Regra vigente | Estado |
|---|---|---|
| api-delpi | S2S-only, scope `stock-inventory.read`, autorização de escopo fail-closed | existente — estender para a rota oficial |
| BFF | `controllership-finance.access` via `has_permission` (Core effective), `principal_type='user'`, `rbac_unavailable`→503, `scope_unavailable`→403 tipado | existente — idem para a rota nova |
| DRE | `controllership-finance.access.dre` somente sobre pacote SUBMITTED | existente — não ampliar |
| Auditoria | provenance no payload + document snapshot + download events | existente — reutilizar |

### 8.F — Erros e indisponibilidade

| Condição | Código/status | Semântica |
|---|---|---|
| Sem snapshot SB9 na competência | `source_missing` | não é zero; não é ausência permanente |
| Parte das filiais sem snapshot | `incomplete` + `missing_branches[]` | parcial explícito |
| Escopo sem itens | `no_matching_items` | população vazia real |
| `as_of` anterior à 1ª snapshot | `reference_unavailable` | sem extrapolação |
| Paridade não verificada | `parity_state=unverified` + `known_residuals[]` | total nunca silenciosamente "oficial" |
| SB9 regravado após emissão | `parity_state=provisional` + drift declarado | `STALE_EVIDENCE` explícito |
| Falha gateway/api-delpi | 502/504 tipado | sem fallback a zero |
| Sem permissão | 403 `access_denied` / `scope_unavailable` | fail-closed |

---

## 9. Plano de implementação (próxima execução)

### 9.1 Sequência e owners

```text
E1 api-delpi  → repo/SQL oficial P7 + regra poder3 plugável + MATR989 as_of
E2 api-delpi  → rota /financeiro/stock-inventory-oficial + OpenAPI + testes
E3 BFF        → proxy /closing/stock-inventory-oficial + authz + erros tipados
E4 MFE        → página oficial P7 (ou evolução da atual) + export + help
E5 BFF        → export endpoint + integração documental (package/submit)
E6 transversal→ smoke E2E + paridade na próxima emissão controlada
```

### 9.2 Arquivos previstos

**api-delpi:**
- `application/dto/financeiro_inventory_p7/{constantes,inventory_p7_request}.py` (novo, espelha padrão do stock-inventory)
- `domain/totvs/protheus_third_party_positions.py` (novo — política poder3 plugável; usa `SB2`/`SF4`/`SD1`/`SD2`)
- `domain/totvs/protheus_product_types.py` (reuso — sem alteração)
- `infrastructure/persistence/totvs/financeiro_inventory_p7/inventory_p7_sql.py` (SB9 ex-99 + filtro tipos + política poder3)
- `infrastructure/persistence/totvs/financeiro_inventory_p7/work_in_process_sql.py` (MATR989: SB9 loc99 + RE−DE por prod×OP + vivência de OP `as_of` — `BR-R08-009`)
- `infrastructure/persistence/totvs/financeiro_inventory_p7/inventory_p7_repository.py`
- `application/use_cases/financeiro_inventory_p7/get_inventory_p7_use_case.py`
- `interface/http/routes/financeiro/inventory_p7_router.py` (+helpers, composer, OpenAPI registry)
- `application/security/` — estender escopo dedicado (`stock-inventory.read` ou `inventory-p7.read`)

**controllership-finance-api:**
- `interface/http/routes/closing_routes.py` → `GET /closing/stock-inventory-oficial` + `/export` (padrão `_call_gateway` existente)
- `application/services/closing_document_service.py` → tipo documental `p7-inventory-register` + integração com pacote
- sem SQL próprio; sem regra de negócio duplicada

**MFE (`plugins/controllership-finance`):**
- `features/closing/StockInventoryPage.tsx` → evoluir: modo `official` com seletor de escopo (já existe), bloco provenance/parity, exportação, memória de cálculo poder3
- `api/stockInventoryApi.ts` + `reportQueryParams.ts` → params da rota oficial
- estados de erro: `source_missing`/`incomplete`/`parity_unverified`
- ajuda contextual (`feature-help-sync`)

**Migrations:** nenhuma justificada no backend de dados (tudo SELECT em
TOTVS). Documento DRE reusa tabelas existentes de closing_documents.

### 9.3 Testes especificados (AC-16)

| Camada | Testes |
|---|---|
| DTO | competence/branch/scope/warehouse validação; `report_scope` enum; rejeição de valores inválidos |
| SQL builder | ex-99, filtro tipos, política poder3 incluída/excluída, joins SB1/SB2/SF4, branch, snapshot key |
| MATR989 | RE−DE por prod×OP, OP sem PR0 `as_of`, corte `D3_EMISSAO<=fechamento`, RE1 loc≠99 entra |
| Use case | status `available`/`incomplete`/`source_missing`/`no_matching_items`/`parity_unverified`; sem falso zero |
| Rotas | OpenAPI registry, operationId EN, authz 403/503, S2S scope |
| BFF | proxy params, erros tipados, `access` fail-closed, DRE nunca executa geração |
| Escopo | `all_products` inclui poder3; `mp_pi_pa` aplica política; totais nunca misturados |
| Poder3 | QTNP-only (em terceiros), QTER-only (conosco), remessa/retorno, produto fora do SB9, `F4_PODER3`≠'N' não-exclusivo |
| Paridade | por linha e total vs artefatos 09/2026: `all_products` ex-99 estrutura PASS + drift declarado; `mp_pi_pa` marca `unverified` até E2 |
| Export | cabeçalho completo, hash, watermark parity, escopo explícito |
| Documental | anexar ao pacote, SUBMITTED, RECIPIENT `access.dre`, snapshot imutável, download audit |
| Negativos | 403 sem permissão, sem token, `rbac_unavailable`, branch inválida |

### 9.4 Smoke (pós-deploy, ambiente de homologação)

1. `GET /closing/stock-inventory-oficial?period=2026-09&branch=01&report_scope=all_products` → `status=available`, `totals.stock_total` ≈ SB9 ex-99 corrente, `provenance.producer='matr460'`.
2. Mesmo com `report_scope=mp_pi_pa` → `parity_state=unverified` + decomposição poder3 (até E2).
3. Filial sem snapshot → `source_missing`, `historicalTotal=null`.
4. Usuário sem permissão → 403.
5. Export CSV → cabeçalho + hash + rótulo de escopo.
6. Anexar export ao pacote → submeter → recipient `access.dre` baixa snapshot.

### 9.5 Deploy e rollback (AC-17)

- Ordem: api-delpi (rotas novas, aditivas) → BFF (proxy aditivo) → MFE
  (feature flag ou rota nova de página). Nenhuma rota/contrato existente
  muda — **deploy de baixo risco, rollback = revert dos commits por
  serviço** (local-first-deploy: local→push→pull; nunca mutar produção).
- Feature flag MFE para a experiência oficial (`p7Official`) enquanto a
  vista operacional permanece padrão.
- Rollback api-delpi: remover rota; nenhum estado persistido → zero
  migração de rollback.
- Risco residual: `parity_unverified` em `mp_pi_pa` — mitigado pelo
  gate E2 e pela flag/watermark; nunca se promove a "oficial" sem
  homologação Controladoria.

---

## 10. Gate final

```text
GATE = PENDING_EXTERNAL_EVIDENCE   (para o conjunto completo)
```

**Subconjunto implementável com segurança agora (`READY` parcial):**
- Contrato e cálculo `all_products` (EM ESTOQUE ex-99 + MATR989
  `as_of`) — estrutura `PROVEN`, componentes comprovados.
- Toda a infraestrutura: rota oficial aditiva, proxy BFF, MFE,
  exportação, integração documental, segurança, erros, provenance.
- `mp_pi_pa` como escopo **declarado** com `parity_state=unverified`
  e política poder3 plugável `ThirdPartyPositionPolicy` — o contrato
  comporta o escopo; a regra oficial de exclusão só é ativada como
  `PROVEN` após E2.

**Bloqueado por evidência externa (`PENDING_EXTERNAL` — pacote E2, owner
TI/ERP, doc 82 §2.1):**
- E2.1 parâmetros efetivos da emissão resumida (`mv_par`/print `MTR460`)
- E2.2 linhas de produto da folha 74 (população exata excluída)
- E2.3 fonte/RPO `matr460.prx` (semântica poder3 + escopo de tipos)

Sem E2, `mp_pi_pa` **não** recebe selo de paridade oficial — o resíduo
76,43/−3.839,06 é pequeno mas a população exata é ambígua (subset-sum)
e a medida de processo do resumo não está decomposta ao centavo.

**Decisões estritamente necessárias (não reabrem DEC-12):**
- D1: implementar `all_products` + infraestrutura completa com
  `mp_pi_pa` em `parity_state=unverified`? (recomendação: SIM)
- D2: nome da rota oficial `/stock-inventory-oficial` (ou
  `/inventory-register`)? (sugestão: `inventory-register` —
  nome do registro oficial, distinto da vista SB9)
- D3: escopo de segurança dedicado `inventory-p7.read` ou reuso de
  `stock-inventory.read`? (sugestão: dedicado — contratos separados)

---

*Fim do documento 119.*
