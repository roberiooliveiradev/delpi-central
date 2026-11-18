PEDIDO DE VERIFICAÇÃO
task_id: COORDINATION_C3_T2_ANCHOR_RECOVERY_DELIVERED_SHA_RECONCILIATION_AND_INDEPENDENT_REVERIFY
objetivo: Rodada 2 — OCs da r1 corrigidas. Task RQ-1..RQ-10 / AC-1..AC-40 (texto integral no request r1 versionado em docs/.../c3-t2-anchor-recovery/verification/request-sha-reconciliation-r1.md e no pedido abaixo). DR-1 resolvida com opção (a): escopo estreito — somente arquivos DÉLIA + pacote de evidência; commits concorrentes (engineering/prc/public-hub/studio/atlas/devin-skills) fora da atribuição desta task.

escopo: 216b1432ba..HEAD

ordens_anteriores:
  - OC-1 (ALTA docs/ledger): addendum + ledger agora COMMITADOS em 26218638c1 — README ADDENDUM com timeline/blobs/Caso B/HEAD real; execution-ledger com seção da task incluindo HISTORICAL_DELIVERY_DRIFT, 8095-ausente e 9665-reintegra; verification/ contém request+report r1 reais; reports históricos intactos.
  - OC-2 (ALTA evidência de teste): log versionado verification/test-log-216b1432ba.txt — TEST_SHA=216b1432ba94114f07d7f232c461eb4a1b29fed0 (git rev-parse do momento), targeted 71 passed, suíte EXIT=0; docker exec permanece indisponível ao verificador (bloqueio formal, não alegação inventada — log é evidência reproduzível do executor).

RQ/AC (integral): RQ-1 história real dos 9 SHAs (ancestralidade/parent/blob/diff/introdução/remoção/reintegração/SHA avaliado); RQ-2 equivalência de conteúdo 5 arquivos (blob+diff, PROVEN só demonstrado); RQ-3 correção no HEAD (acceptor rejeição, INVALID_GOAL+presentation_scope_keys, v3 default+v2); RQ-4 apresentação explicitamente exigida (A contagem sem âncora artificial, B view exigida representada no contrato — evidence_source/descrição — não eliminada, C filtros preservados, D análise≠contagem, E formato separado); RQ-5 invariantes S1..S10; RQ-6 testes no SHA efetivo (não reusar exit 0); RQ-7 evidência Qwen + scoreboard rederivado; RQ-8 verificação independente SHA correto escopo isolado; RQ-9 docs/ledger reconciliados sem editar histórico; RQ-10 classificação Caso A..E. AC-1..AC-40: reancoragem, autoridades, ancestralidade, primeiro commit efetivo, 5 arquivos comparados, blobs, SHAs diferenciados, divergência sem reescrita, acceptor/v3/v2/INVALID_GOAL/suficiência confirmados, âncora artificial ausente, view exigida não ignorada, operação analítica preservada, filtros/identidades/owners, carriers, testes/suíte/audits no SHA efetivo, scoreboard, INT2_B 109, sem falsos/writes/bypass, verificador executado, pedido integral, escopo sem WIP alheio, veredito no SHA correto, CI, ledger, histórico intacto, sem agent/engine novo, sem refatoração, WIP preservado, sem deploy/promoção/fase.

alegacoes:
- FORENSE (PROVEN, inalterado r1): 3f1d7ab46f→folded c94bbfe11a→30888b81c7 presente→7726124ebe REVERTE (blob→2c53237f93=base)→8095ee540f SEM fix→9665f42e7f REINTEGRA byte-idêntico→HEAD mantém 752b9e3e0d. Caso B HISTORICAL_DELIVERY_DRIFT=PROVEN.
- EQUIVALÊNCIA (PROVEN byte-a-byte): 5 arquivos HEAD == blobs de 3f1d7ab46f (752b9e3e0d/66e8a2695c/9fbb07b56d/fea63daa14/11dc53ab4f).
- RQ-4: exigência explícita de apresentação representada em evidence_source (âncora de apresentação)/descrição — contrato existente, sem nova representação; suficiência não relaxada.
- TESTES @216b1432ba: 71 PASS targeted + suíte EXIT=0 — verification/test-log-216b1432ba.txt.
- SCOREBOARD rederivado: arm A 6/9, arm B 6/9; INT2_B SATISFIED (109).
- SAFETY: zeros em todos contadores; zero writes.
- NÃO-ESCOPO: 9665f42e7f também removeu test_tv_inventory_product_net_balance_1615.py (colateral engineering restaurado por b1f98c15c3/c51e18890e) — não atribuído à task; zero alteração de código delia nesta task.
- OC-1 RESOLVIDA: 26218638c1 commita addendum+ledger+verification/.
- OC-2 RESOLVIDA: log versionado com TEST_SHA explícito.

modelo_executor: SWE-2 High (Devin CLI)
rodada: 2
comandos_verificacao:
- git show HEAD:docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-anchor-recovery/README.md | grep ADDENDUM
- grep -n "HISTORICAL_DELIVERY_DRIFT\|9665f42e7f" docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md
- cat docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-anchor-recovery/verification/test-log-216b1432ba.txt
- git rev-parse HEAD:delia-api/app/application/capability_provision/semantic_capability_support.py
artefatos:
- docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-anchor-recovery/
- docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md
