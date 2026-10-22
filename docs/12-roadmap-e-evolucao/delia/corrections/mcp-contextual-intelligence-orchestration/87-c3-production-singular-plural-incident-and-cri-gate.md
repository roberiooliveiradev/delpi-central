# 87 — C3: incidente produção singular/plural, causa-raiz de budget e gate CRI produção

**Task:** `DELIA-C3-PRODUCTION-SINGULAR-PLURAL-INCIDENT-AND-CRI-ACTIVATION-01`
**Data:** 2026-10-22 · **Executor:** Devin (SWE-2)
**Escopo:** reproduzir o incidente do Portal (pergunta singular bloqueada × plural
com registros), corrigir a causa-raiz comprovada sem regras léxicas, e avaliar/
preparar a ativação CRI em produção pelos gates canônicos.

---

## 1. Estado do ambiente publicado (ETAPA 1)

| Item | Evidência |
|---|---|
| Endpoint produção | `https://minhadelpi.com.br/apps/delia-api/` (Nginx → `delia-api:8000`) |
| Health | `{"service":"delia-api","status":"available"}` — não comprova modo CRI |
| `PRODUCTION_CODE_SHA` / imagem | `TEST_NOT_RUN` — sem acesso ao host `srv-api`; DNS/rede local não resolve o host e não há credenciais de deploy nesta máquina |
| Credencial dev no Keycloak prod | `invalid_grant` (rejeitada) — reprodução autenticada em produção **não autorizada/possível** |
| `DELIA_RESPONSE_INTELLIGENCE_ENABLED` prod | `.env.prod` real vive no host; o `.env.prod.example` commitado **não declarava a flag** e o compose default é vazio → efetivo provável = **baseline/OFF** |
| Evidência indireta do pipeline prod | as capturas mostram timestamps ISO brutos; a apresentação CRI (`_cri_scalar_text`) renderiza `dd/mm/YYYY às HHhMM` — ISO bruto só ocorre no pipeline baseline |

**Conclusão ETAPA 1:** produção roda código e modo não verificáveis a partir
desta máquina; a evidência das capturas (ISO bruto) é consistente com CRI OFF.

## 2. Reprodução exata (ETAPA 2/3) — no ambiente autorizado (dev, CRI ON)

P1 `qual o ultimo processo cadastrado no transformometro?` executada 4× no dev
(stack real, Keycloak delegado real, MCPs reais, modelo real):

| Tentativa | Resultado | Primeiro ponto de divergência |
|---|---|---|
| 1 | NON_GROUNDED "fonte indisponível" | `interaction_admission` timeout (6s) + `select_capability` 11,3s → `arguments` sem budget (`model_timeout`) |
| 2 | NON_GROUNDED idêntico | `arguments` `model_timeout` após ~20–27s de estágios |
| 3 | **GROUNDED** `teo.record_read` `arg_keys=action,entity` → "Encontrei este registro: PROC-0105 … A fonte informa 109 registros no total" | nenhuma — pipeline íntegro |
| 4 | NON_GROUNDED | `select_capability` timeout em **21,3s** — um único estágio consumiu o restante |

P2 `quais oa ultimos processos cadastrados?` (typo preservado): **GROUNDED**
`teo.record_read` → "Encontrei 40 registros … Exibindo 5 de 40" em 18,4s pós-fix.

## 3. Causa-raiz comprovada

- **Zero acoplamento léxico:** não existe regex/branch singular×plural; o texto
  só chega ao modelo. O sucesso da tentativa 3 prova que o singular é
  semanticamente idêntico (`record_read`, `action,entity` — sem `date_field`,
  sem rejeição do owner, sem `MCP_PROTOCOL_ERROR`).
- **Mecanismo:** 5+ estágios de modelo serializados (admission → select_group →
  select_capability → native_assessment → arguments → invoke → synthesis)
  contra o teto congelado de 30s; `DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30` permite
  que **um único estágio lento consuma o turno inteiro** (observado: 21,3s).
  O bloqueio é estocástico por latência do modelo — qualquer pergunta pode
  estourar; a assimetria singular/plural da captura é amostragem.
- **Defeito real secundário encontrado:** sob CRI ON, o estágio de modelo
  `grounded_synthesis` executava mesmo quando a composição CRI descartaria sua
  saída — queimando ~3–7s do budget congelado e expondo o turno a um
  `model_timeout` terminal **depois** de o invoke já ter produzido evidência
  (observado ao vivo: synthesis 6,7s timeout num turno que compôs via CRI).

## 4. Correção mínima aplicada (ETAPA 6)

`orchestration.py` — composição CRI passa a ser tentada **antes** da síntese;
`_synthesize_content(..., allow_model_stage=cri is None)`:

- CRI compõe → o estágio de modelo de síntese **não é proposto** (log
  `stage=synthesis decision=skip_cri_composed`); as projeções determinísticas
  (paginada/pessoal/guidance/single-leaf) continuam contribuindo limitations.
- CRI não compõe (OFF ou vocabulário ausente) → síntese executa normalmente —
  fallback preservado por construção.

Sem estágio novo, sem flag nova, sem reordenação de fatos, sem alterar OFF.

**RED→GREEN (testes novos em `test_cri_e3_conversational_presentation.py`):**

- `test_on_skips_synthesis_model_stage_when_cri_composes` — asserta ausência do
  purpose `grounded_synthesis` sob composição CRI (falhava antes do fix).
- `test_on_synthesis_fallback_runs_when_cri_cannot_compose` — vocabulário
  ausente degrada e o estágio de síntese ainda roda (fallback vivo).
- `test_on_adds_zero_model_calls_e3` — invariante evoluído `== → <=`: CRI nunca
  adiciona estágio; pode gastar **menos** quando compõe.

**Pós-fix live:** P2 GROUNDED em 18,4s com `skip_cri_composed` registrado
(antes: ~24–25s + synthesis descartada); P3 "processo criado mais
recentemente" ainda NON_GROUNDED por starvation pré-invoke (arguments
10,4s encerrando o turno aos ~25s) — latência do modelo, residual material.

## 5. Consistência de contagens e datas (ETAPA 5)

- `10 registros localizados` (activity, contagem da fonte) × `Encontrei 2`
  (resposta, entregues apresentados): **conceitos distintos, não defeito** —
  o frame CRI já separa total fonte/atribuído de entregues/apresentados
  (fix do doc 86 em produção de código). Sob CRI ON a resposta mostraria
  "A fonte informa 10 registros no total".
- Datas: a apresentação CRI já humaniza (`_cri_scalar_text` →
  `dd/mm/YYYY às HHhMM`); o ISO bruto das capturas veio do pipeline baseline —
  evidência adicional de CRI OFF em produção. Nenhum defeito a corrigir.

## 6. Gate CRI produção (ETAPA 7)

| Gate | Estado |
|---|---|
| Flag existente `DELIA_RESPONSE_INTELLIGENCE_ENABLED` | mecanismo OK (compose `${...:-}` → fail-closed) |
| Recursos CRI | instructions v2 / presentation v3 validados em dev |
| Rollback | remover flag + recreate (documentado no `.env.prod.example`) |
| **Acesso operacional ao host prod** | **AUSENTE** — sem SSH/DNS para `srv-api`, sem credenciais prod |
| **Verificação do código/imagem efetiva em prod** | **AUSENTE** — não se pode afirmar qual SHA responde |
| Deploy canônico | `local-first-deploy` exige local→push→pull no host — indisponível |

`PRODUCTION_CRI_ACTIVATION=BLOCKED_BY_GATE` — evidência ausente: acesso
operacional ao host prod e SHA/imagem efetivos. **Preparação entregue:**
`infra/.env.prod.example` agora documenta a flag com default desejado ON +
instruções de rollback (não muta nada em runtime; `.env` real é do host).

## 7. Regressão e avaliação real

- Suítes: E3 (64) + E1/E2 + C3 + stage03 + baseline conversacional + adaptive
  routing + paginação = **PASS**; backend completo: 1 falha
  **pré-existente** confirmada em HEAD limpo (`test_http_timeout_maps_to_504`
  espera 504, mas o soft-land de timeout→200 NON_GROUNDED é decisão doc 35/G0-02
  — teste stale; não alterado).
- Real-model/real-MCP: TÉO GROUNDED singular e plural; latência P2 18,4s.
- Negativos: nenhuma capacidade ACT; writes fora do caminho; count claims
  permanecem tipados.

## 8. Resíduos

- **Material:** starvation pré-invoke persiste quando um estágio de seleção
  excede ~25s (variância do modelo). Mitigar de verdade exige decisão de
  arquitetura (consolidação/paralelização de estágios ou modelo mais rápido) —
  fora do bounded scope; o teto global 30s é frozen.
- **Não-material:** `test_http_timeout_maps_to_504` stale vs soft-land (doc 35);
  `.env.prod.example` agora declara a flag — o `.env` real do host decide.

## 9. Veredito

```text
P1_REPRODUCED=YES(2x NON_GROUNDED live, assinatura idêntica à captura)
P1_ROOT_CAUSE=model-stage latency vs frozen 30s turn budget
  (not lexical, not owner rejection, not singular semantics)
FIX=synthesize-skip when CRI composes (bounded budget reclaim;
  removes terminal-timeout risk on the last stage)
P1_AFTER=FLAKY_BY_MODEL_LATENCY (succeeds when stages fit)
P2_AFTER=GROUNDED(18.4s, skip_cri_composed logged)
COUNT_DIFFERENCE=EXPLAINED(distinct frames, no defect)
DATE_PRESENTATION=CRI already pt-BR; raw ISO = baseline pipeline = CRI OFF in prod
PRODUCTION_CRI_ACTIVATION=BLOCKED_BY_GATE(prod host access + effective SHA)
UNIT_TESTS=PASS (E3 64 + suites; 1 pre-existing stale-504 failure)
REAL_EVAL=PASS(dev, real Keycloak/MCPs/model)
I04_ACCEPTED=NO
C3_EXECUTED=YES
NEXT=COORDINATION_REVIEW
```

## 10. Independent coordination review — 2026-10-22

**Verdict: ACCEPT_WITH_RESIDUAL for the bounded code correction; production incident remains OPEN.** Confirmed GitHub HEAD 812499e41aa95201bfa38c45a04983945f7019d4, report 87, infra/.env.prod.example and the gated synthesis-model skip in orchestration.py. Reported dev tests and live MCP/model probes were not independently rerun by this reviewer: INDEPENDENT_RUNTIME_TEST=TEST_NOT_RUN.

**Accepted:** When CRI composition already supplies the governed response, omitting discarded grounded_synthesis model output is a legitimate reuse of the current composition boundary; fallback must still run when CRI does not compose and deterministic projections/limitations must remain intact. This removes a post-invoke model-stage cost and terminal-timeout risk, but does not repair the demonstrated P1 pre-invoke stage starvation. P1 success on one of four attempts indicates no deterministic singular-specific failure was demonstrated; it does not prove all lexical branches are absent throughout the repository.

**Material blocker remains:** 30-second frozen global budget with serial model stages and a configured per-stage cap reaching the global cap. Do not propose raising the global budget or injecting provider-specific shortcuts. A bounded architectural decision is required on existing stage scheduling, reuse, optionality, possible consolidation and latency measurements, with model-driven selection preserved. The claim 'purely model-side variance' should be treated as executor inference supported by stage timings, pending more complete per-stage traces and model/transport attribution. No production-root-cause assertion is justified from dev reproduction alone.

**Production distinction:** No access to srv-api, no effective backend/frontend SHA, no prod runtime flag or live authenticated replay. Production ON is NOT_VERIFIED and deployment NOT_DONE. Raw ISO dates are compatible with baseline/OFF but **do not prove OFF**: stale runtime, fallback, or other presentation branches must be excluded through runtime logs/config. The tracked .env.prod.example is documentation/preparation only; setting true there does not change the host's .env. Activate only after canonical release gates, prod SHA, audit and rollback are verified; product desire for default ON is not self-authorization to mutate an unknown production environment.

**Counts and correctness:** '10 localized' (activity) vs '2 found' (response) could indicate source vs delivered/presented frames, but cannot be declared conclusively correct without the authoritative owner envelope and actual presentation inputs for that turn. Distinguish creation from modification, page/coverage from global extremum, and verify whether the selected record was truly the newest created. A grounded record list alone does not satisfy the user's superlative intent.

**Next coordination action:** (1) production access/observability and actual deployment/CRI-mode verification, separate from code publication; (2) a finite, evidence-first pre-invoke latency-path decision and task-outcome evaluation; (3) no more symptom-oriented lexical fixes. The user-facing incident stays OPEN until the original two exact Portal questions are replayed on the verified production SHA with correct evidence, latency and CRI state.

COUNT_CORRECTNESS=INCONCLUSIVE_FOR_ORIGINAL_PROD_TURN; P1_PRODUCTION_ROOT_CAUSE=INCONCLUSIVE; P1_DEV_PREINVOKE_BUDGET_STARVATION=EXECUTOR_VERIFIED; SYNTHESIS_SKIP=STATIC_VERIFIED; CRI_PRODUCTION_ON=NOT_VERIFIED; PRODUCTION_DEPLOYMENT=NOT_VERIFIED; INCIDENT_CLOSED=NO; I04_ACCEPTED=NO; C3_EXECUTED=YES_EXECUTOR_REPORTED.
