# CF-PROC0072 — Gate 042: R09 — recuperação Git, engenharia temporal SHY/OP, taxa MOD e paridade final

Data: 2026-11-01. Autoridade: DR-1/DR-2 APPROVED; D3 S2S APPROVED; DR-3 PENDING.

## ETAPA A — Git

- `HEAD` = `d199686f92` = `origin/main` (sync — último fetch). Commits do Gate 041 (`6b6a845458` local) publicados como `0acdf32b6a` por outro canal credenciado — conteúdo íntegro na main.
- `git fetch`/`git push` via SSH falha `publickey` nesta estação; `credential.helper=manager`, `gh` ausente — sem credencial legítima alternativa neste shell. **Bloqueio formal mantido**; código recuperado segue em main (publicado por canal existente), novos commits locais aguardam a mesma via.
- WIP de terceiros preservado (untracked, worktrees, stashes).

## ETAPA B — Seleção temporal SHY/OP

Investigação live (SC2/SHY/SG2/SG1/SH1/SB1 — nomes reais verificados no schema: `HY_RECURSO`, `C2_DATRF`, `C2_STATUS`, `BZ_COD`, `BZ_DATREF`):

| Hipótese | Resultado |
|---|---|
| Última OP com roteiro SHY (sem bound) | **ADOTADA** — melhor correspondência empírica e semanticamente defensável ("roteiro vigente na execução"); rotas congeladas são cópias estáveis entre OPs da mesma revisão |
| `C2_EMISSAO ≤ data de geração do artefato` (~07/10) | **REJEITADA** — medida pior (3.493 vs 3.694 chaves); produtos cujo único OP é posterior (ex.: `90264258`, OPs 202610) perderiam SHY, mas o artefato traz valores de roteiro — indica geração posterior a ~07/10 |
| OP dentro da competência | descartada — `70260033` (componente) tinha ops no artefato com OPs só de set/out |
| SG2 fallback quando sem SHY | **CONFIRMADA** — produtos sem OP/roteiro congelado usam cadastral; estado da fonte declarado por linha (`stdTime.state`) |

Causa da divergência residual: **drift temporal de revisão de roteiro** — OPs criadas entre a geração do artefato (~fim out) e hoje (nov) carregam revisões diferentes; o snapshot histórico não é reconstruível sem a SP/backups. Medido e com owner, não inventado.

## ETAPA C — Quantidade/horas/multiplicidade

- Grão por âncora agregada (soma SD2 `D2_TIPO<>'D'`) confirmado por linhas do componente `70260033` (QtdFat = soma por pai: 0,001/0,002/0,001).
- `Horas = QtdFat × Quantidade` revalidada (ex.: 0,001×8,66=0,0087 idêntico ao artefato).
- `propagatedQty` = próprio faturado do produto no período, fallback faturado da âncora (BR-R09-006) — 99,5% correto nas chaves.
- `qtdfat_bad` residual (16): casos de desdobramento de serial — divisor `÷C2_QUANT` sem evidência de aplicação exata (E9) — não inventado.
- Ausentes/excedentes residuais = drift de revisão de roteiro (Etapa B) + possível drift `H1_CCUSTO` (SH1 sem data — não verificável sem backup; residual).

## ETAPA D — Taxa histórica MOD

- `BZ_CUSTD` corrente: **REJEITADO** no Gate 041 (0/120; `BZ_DATREF` vazio = sem histórico).
- `SB9010.B9_CM1`: sem linhas para itens MOD (não estocáveis).
- Tabelas custom (`ZD*`, `*MOD*`, `SHU*`, `*TAXA*`): **nenhuma** no catálogo acessível.
- Escopo buscado e exaurido: SBZ, SB9, SH1, SHB, tabelas custom, schema. Fonte da taxa vive na SP ausente (`STP_DELPI_FORMA_PRECO_*`, E9) — provável rateio hora-MOD por centro de custo mensal calculado dentro da SP. **`SOURCE_MISSING` mantido** (DR-2); owner: Controladoria/DBA; próxima alça: RPO/backups + entrevista Controladoria.

## ETAPA E — Paridade informacional final (2026-09)

| Indicador | G040 | G041 | **G042** |
|---|---|---|---|
| Linhas geradas | 1.465 | 4.659 | **4.659** |
| Chaves | 1.395 | 3.694 | **3.694 (82,5%)** |
| QtdFat | 100% | 99,5% | **99,6% (3.678/3.694)** |
| Quantidade | 84,5% | ~77,5% | **82,2% (3.038/3.694)** |
| Horas | 84,5% | ~77,5% | **81,9% (3.024/3.694)** |
| Ausentes | 3.081 | 983 | **782** |
| Excedentes | 70 | 1.165 | **965** |

Variante `run_date=20261007` medida e rejeitada: 3.493 chaves/983 ausentes/1.165 excedentes — hipótese "OP ≤ data de geração" descartada com evidência.

Performance: ~6–8 min, ~10 queries set-based (chunks ≤500), sem N+1, read-only `NOLOCK`, zero escrita ERP. Testes: 26 R09 + regressões = 50/50 PASS (reexecutados, venv Windows; WSL/Docker indisponível na sessão).

## DR-3 — Pacote de homologação preparado

Conteúdo: competência 2026-09 ambas filiais; artefato 4.476 linhas; algoritmo (âncoras SD2/SF4 → SG1 compartilhada 02/04/06 → SHY última OP/SG2 → `H1_CCUSTO`→`MOD*` → QtdFat×tempo); matriz de correspondência; divergências por campo com causa; limitações (taxa `source_missing`, drift roteiro, divisor serial); `OPERATIONAL_VIEW` ≠ paridade oficial. Manifestação da Controladoria: **aguardada**.

## Prontidão BFF

**NOT_READY** — pendente: homologação DR-3, fonte da taxa MOD e delimitação final do drift de roteiro. Tecnicamente integrável já: contrato estável, envelope/meta/registry, S2S aprovado, ausência tipada — mas não promovível a relatório oficial.

## Resíduos / owners

SSH `publickey` (usuário) · taxa MOD sem fonte localizada (Controladoria/DBA — RPO/backup) · divisor `÷C2_QUANT` (E9) · drift temporal roteiro e `H1_CCUSTO` (Controladoria) · SP ausente (DBA) · vídeo `TEST_NOT_RUN` · BFF/MFE/deploy (não autorizados).

## Parecer

**`ACCEPT_WITH_RESIDUAL`** — modelo reconstruído por evidência até o limite técnico acessível (82,5% de chaves, 99,5% QtdFat); divergências quantificadas com causa e owner; nada inventado. Próximo: Gate 043 — DR-3 homologação + caça à base da taxa.
