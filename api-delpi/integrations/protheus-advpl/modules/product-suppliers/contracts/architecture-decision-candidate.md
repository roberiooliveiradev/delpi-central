# Candidato de decisão — arquitetura SA5

| Critério | DMATA061 (independente) | Model061/MATA010 | MATI060/EAI | SQL/RecLock |
|---|---|---|---|---|
| Reuso rotina oficial | Modelo oficial do cadastro SA5 | Grid dentro do cadastro de produto | Canal EAI oficial | — |
| CREATE | header produto + linha grid — encaixa | exige modelo MATA010 inteiro | indisponível (não configurado) | proibido |
| READ | **PROVEN_RUNTIME** (VIEW op + posição de alias + grade — 0.7.0) | idem acoplado | n/a | fora do .PRW |
| UPDATE | **PROVEN_RUNTIME** (UPDATE op + linha localizada — 0.7.0) | acoplado ao produto | n/a | proibido |
| DELETE | **PROVEN_RUNTIME** (`DeleteLine` — 0.7.0); **último vínculo bloqueado por `a060VldGrv`** (desenho oficial) | idem | n/a | proibido |
| Acoplamento | baixo — recurso independente | alto — SA5 dentro de SB1 | alto (infra EAI) | n/a |
| Dependências | FWMVCDEF, modelo 'DMATA061' no RPO | MATA010 completa + `MV_CADPROD`+acessos | app/integração/adapter/canal | n/a |
| Riscos | `M->` em `a060LinOk`; ciclo de vida REST | `SetUniqueLine` sem REFGRD (colisão c/ grade) | custo de infra EAI | violação de invariante |
| Evidência | PROVEN_SOURCE (Dmata061.prx) | PROVEN_SOURCE (MATA010M_DLP) | PROVEN_LIVE não configurado | — |

## Emitir: **EXTEND** (recomendação, não implementação)

Façada `.PRW` (`DLP04I02`, nome pendente de colisão no repo ERP) que
instancia `FWLoadModel('DMATA061')` — o modelo oficial já carrega
validações, triggers e PEs do cadastro. Model061/MATA010 descartado por
acoplamento e pela `SetUniqueLine` incompleta; EAI descartado (infra
ausente); SQL/RecLock fora de cogitação.

`ARCHITECTURE_DECISION_REQUIRED` permanece: ratificação pelos owners
(Integrações TOTVS + ERP + Coordination) — mesma pendência do G0-C —
antes de qualquer `src/DLP04I02.PRW`.

## Bloqueios objetivos p/ handoff TOTVS

1. ~~`VALIDAR NO TST01` — ciclo FWLoadModel em REST~~ — **RESOLVIDO**:
   `MATA061` ativa headless (SetVldActivate bypassa o browse) — CRUD
   completo PROVEN_RUNTIME TST01 `:8701` (build 0.7.x, 2026-11-19).
2. ~~`a060LinOk` com `M->A5_*` vazio~~ — superado: POST provou a inclusão;
   comportamento exato do dup-check não bloqueou o ciclo.
3. `VALIDAR NO TST01` — DELETE do último vínculo (`a060VldGrv`): regra
   de negócio oficial (rejeição por desenho, fail-closed). Remoção do
   último vínculo = semântica de exclusão do documento — TO_INVENTORY.
4. ~~`TO_INVENTORY` — commit/activate do MPFormModel~~ — **RESOLVIDO**:
   `CommitData()` retorna lógico `.T.`; `Activate`/`GetValue`/`DeleteLine`
   comprovados em runtime.
5. ~~`TO_INVENTORY` — 'DMATA061'/'MATA061' compilados~~ — **RESOLVIDO**:
   ambos presentes; `MATA061` em uso como primário.
6. READ — **decidido**: GET ADVPL implementado via modelo (PROVEN);
   api-delpi SQL segue leitura canônica dos consumidores (FABR/FALOJA/
   REFGRD já projetados).
