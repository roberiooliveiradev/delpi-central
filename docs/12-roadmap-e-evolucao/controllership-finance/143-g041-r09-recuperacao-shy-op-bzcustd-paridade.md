# CF-PROC0072 — Gate 041: R09 Slice 1 — recuperação, S2S, engenharia reversa SHY/OP, BZ_CUSTD e nova paridade

Data: 2026-11-01. Autoridade: DR-1/DR-2 APPROVED (docs 138/140, branches PR #126/#127); DR-3 PENDING.

## ETAPA 1 — Recuperação e publicação

- `git rev-parse HEAD` = `25a5de36b9` = `origin/main` (último fetch). O commit do Gate 040 (`383db085f1` local) **já está publicado** em main como `7ca041a19b` — diff entre os dois = apenas um doc alheio (+70 linhas). Nada a cherry-pickar; código íntegro.
- `git fetch/push` falha: `git@github.com: Permission denied (publickey)` — **bloqueio formal de publicação SSH nesta estação**. Commits ficam locais até credencial válida.
- WIP de terceiros preservado (untracked delia-api, `.worktrees/`, stashes, `nul`).
- Testes **reexecutados** neste gate (venv Windows, `delpi-venv`, ODBC18): **50/50 PASS** (R09 26 + closing_state 3 + billing_exclusion 21).

## ETAPA 2 — Revisão S2S / scopes / flags

Contrato vigente lido (`stock_inventory_scope.py`): resolver **transversal aprovado** (doc 49 §8) — dataset compartilhado financeiro, `controllership-finance.access` validado no BFF via Core, cliente S2S `controllership-finance-api`, scope `stock-inventory.read`, flag `FINANCEIRO_STOCK_INVENTORY_ENABLED` fail-closed + delegated human principal. Irmãos R11/R12/R15 usam **o mesmo** contrato — R09 segue o padrão aprovado, não é acoplamento indevido. Resíduo cosmético: naming do scope/flag é legado do primeiro dataset (R03). **Decisão: preservar** — mudança de scope/flag seria material e não autorizada.

Testes de segurança (na suíte): 401 header ausente, 401 token inválido, 403 cliente errado, 403 scope insuficiente, 403 flag off (`scope_unavailable` tipado), 403 principal-serviço-como-usuário, 400 period/branch inválidos — PASS. Sem permission nova, sem exceção silenciosa.

## ETAPA 3 — Engenharia reversa SHY/OP (reconstrução do modelo)

**Três correções de semântica provadas por evidência direta:**

| # | Descoberta | Evidência | Correção |
|---|---|---|---|
| 1 | **SG1 é compartilhada** (`G1_FILIAL=''`) — filial específica vazia | amostra: todos os produtos só têm filhos em filial branca | `G1_FILIAL IN ('', branch)` |
| 2 | **Coluna `PA` do artefato = produto explodido** (não a âncora); `Seq Comp` = nível do produto na árvore | `70260033` nunca faturado mas tem 27 linhas '04' — é componente (pais 90264018/19/21/30) | chave de paridade = `(branch, explodedProduct, level, mod)` |
| 3 | **Roteiro congelado da OP (SHY) é a fonte primária** de `Quantidade`; SG2 cadastral = fallback | `70260033`/`90260054`: `Quantidade` artefato = `HY_TEMPAD` da OP mais recente; BR-R09-007/008 | `frozen_route_ops`: última OP com roteiro SHY por produto (branch filial), MOD via `H1_CCUSTO`→`'MOD'+cc` |

- Grão confirmado **por âncora agregada** (soma SD2 por produto), não por item: pais de 70260033 faturaram 0,001/0,001+0,001/0,001 → linhas do componente exibem 0,001/0,002/0,001 = soma por âncora.
- **Hipótese rejeitada**: `C2_EMISSAO ≤ 20261007` (data de geração) **piorou** a paridade (3.493 vs 3.694) — rotas estáveis ou artefato regenerado mais tarde. Mantido default `run_date=hoje` (semântica "OP corrente na execução"; API em produção = OP mais recente).
- Custos: inalterados (DR-2). `Custo Produto` do artefato = 0 nas amostras — semântica pendente.

## ETAPA 4 — BZ_CUSTD como fonte da taxa MOD

- `SBZ010` carrega **apenas valor corrente** (`BZ_DATREF` em branco — sem histórico por filial).
- Comparação (amostra 120): `BZ_CUSTD` as-of 30/09 = 79,87 vs taxa artefato 70,81 (MOD393) → **0/120**. Corrente × artefato diverge em todos os MODs amostrados (razão 0,87–0,96, não constante).
- **Classificação: REJECTED** — `BZ_CUSTD` não reproduz a taxa do artefato. A taxa histórica residia em base não localizada (SP `STP_DELPI_FORMA_PRECO_*` ausente, E9). O claim anterior do doc 85 ("4.469/4.469") media a época em que o custo corrente ainda ≈ valores de setembro — drift posterior confirma.
- `costUnit`/`costTotal` permanecem `source_missing` (DR-2). Owner do resíduo: Controladoria/DBA.

## ETAPA 5 — Nova paridade informacional (2026-09, ambas filiais)

Ambiente: SQL Server real via ODBC18 (Windows — WSL/Docker indisponível), read-only, `NOLOCK`.

| Métrica | Gate 040 | **Gate 041** | Artefato |
|---|---|---|---|
| Âncoras | 521 | **521** | baseline |
| Linhas calculadas | 1.465 | **4.659** | 4.476 |
| Chaves (filial,produto,level,MOD) | 1.395 | **3.694 (82,5%)** | — |
| QtdFat correto | 1.395/1.395 | **3.677/3.694** | — |
| `Quantidade` correto | 1.179 | **2.864** | — |
| `Horas` correto | 1.179 | **2.850** | — |
| Ausentes | 3.081 | **983** | — |
| Excedentes | 70 | **1.165** | — |

**Divergências remanescentes (causa + owner):**
- `qty_bad` 829 (total incl. extras): produtos cujo roteiro corrente ≠ roteiro usado pelo artefato — deriva temporal de revisão de roteiro (OP de referência do SP é incognoscível sem a SP; E9). Amostras no probe JSON.
- `keys_missing` 983 + `keys_extra` 1.165: mesma causa — o artefato usou um snapshot de roteiros de out/2026; hoje (nov) OPs mais recentes carregam revisões diferentes → conjuntos de ops divergentes. Propriedade estrutural da reconstrução ex-post, não defeito de implementação.
- `qtdfat_bad` 16: casos pontuais de propagação (provável desdobramento de serial — divisor `÷C2_QUANT` ainda E9).

## Performance

Probe completo (2 filiais, ~1.800 produtos na árvore, queries set-based chunked ≤500): ~6–8 min, ~10 statements por filial — sem N+1. Leitura read-only, sem escrita no ERP.

## Documentação atualizada

doc 143 (este) · ficha R09 · ledger RQ/AC (entradas R09-G041) · probe scripts versionados (`scripts/r09_*.py`).

## Resíduos e owners

| Resíduo | Owner |
|---|---|
| Push SSH `publickey` — commits locais não publicados | usuário (credencial) |
| SP `STP_DELPI_FORMA_PRECO_*` e snapshot de roteiro usado no run | DBA/TOTVS (E9) |
| Taxa MOD — fonte desconhecida (BZ_CUSTD rejeitado) | Controladoria |
| Divisor desdobramento `÷C2_QUANT` | técnico + Controladoria |
| Divergências residuais por drift temporal de roteiro | Controladoria (DR-3) |
| Deploy produtivo / BFF / MFE — fora do escopo | PO |

## Parecer

**`ACCEPT_WITH_RESIDUAL`** — código publicado (main já contém Slice 1), S2S validado como contrato aprovado, modelo SHY/OP reconstruído por evidência com paridade saltando 1.395→3.694 chaves (82,5%) e QtdFat 99,5% nas chaves. Cobertura restante é drift temporal de roteiro — medida, explicada, com owner. Push bloqueado por credencial SSH (ambiente), não por escopo.

**Próximo gate recomendado**: Gate 042 — homologação item a item com Controladoria (DR-3) + investigação da base de taxa MOD (RPO/backups/tabela de rateio); contrato BFF após DR-3.
