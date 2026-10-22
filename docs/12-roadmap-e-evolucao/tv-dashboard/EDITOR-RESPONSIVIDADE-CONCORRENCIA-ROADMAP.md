# TV Dashboard — Responsividade do editor e concorrência entre editores

> **Status:** ROADMAP / TARGET — não autoriza implementação ou deploy.
> **Data:** 2026-10-22. **Base inspecionada:** `main` no GitHub, após `93849c67c1`; HEAD encontrado na revisão: `4a6d85286c66`.
> **Owner:** TV Dashboard / `tv-dashboard-api` para mutations, revisão, AuthZ e persistência; MFE `plugins/tv-dashboard` para UX e projeção; `tv-dashboard-presentation` para palco canônico; `public-hub` apenas host público.
> **Fontes superiores:** Project Instructions, `.cursor/rules`, responsibility-map, `tv-dashboard-api/README.md`, VISTA capability matrix, contratos/ADRs e código do HEAD. Revalidar todos antes de cada diff.

## 1. Objetivo e não objetivos

Tornar os comandos do editor perceptivelmente imediatos sem perder autorização, persistência, histórico, revisão, undo/redo ou alterações de outros usuários. Separar **resposta visual local**, **commit autoritativo** e **reconciliação da confirmação**.

Não criar segunda mutation boundary, segundo renderer, GPT-local RBAC, executor paralelo, CRDT/OT novo, auto-merge irrestrito ou lock global da playlist. Não usar atualização local como confirmação de gravação. Não antecipar operação cujo resultado não seja deterministicamente projetável conforme contrato. Viewer público não participa da edição.

## 2. Fatos atuais e limites da evidência

| Item | Estado | Evidência / limite |
| --- | --- | --- |
| PresentationMutation compartilhada | PROVEN | `PresentationMutationCommitService.commit` prepara patch e persiste por `TvPresentationWriteService.update_slide` |
| Gate de fingerprint por classe de operação | PROVEN | `mutation_ops_require_data_fingerprint(ops)` é consultado no commit; evita resolver fonte em alteração puramente geométrica |
| Read-back autoritativo | PROVEN | ack contém `nativeConfig` persistido e `appliedOps`, carimbo de formatação |
| Revisão esperada e erro de concorrência | PROVEN | `expected_revision`, `RevisionConflictError` 409 |
| CAS de revisão no repositório | PROVEN | `TvPresentationWriteService._persist` traduz conflito de repositório; comentário documenta `FOR UPDATE` transacional; revalidar teste do CAS real |
| Notificação por playlist | PROVEN | `notify_presentation_changed` publica `presentation_updated` via realtime hub |
| Presença de editor e destinatário específico | PROVEN | `PresentationRealtimeHub` mantém `clientId`/`userId`, `canEdit`, TTL 90 s e envio direto; não prova UX de reconciliação |
| Invalidação de cache no notifier | PROVEN | `reset_comunicado_data_block_cache()` é invocado; efeito/custo de invalidar por geometria ainda TO_INVENTORY |
| Atualização local para mover/tamanho/grupo | REPORTED | Relatório `VISTA-TV-EDITOR-MUTATION-LATENCY-020`; revalidar os handlers efetivos no HEAD |
| UI consistente com dois editores simultâneos | TO_INVENTORY | Presença + WS + CAS não provam ausência de perdas visuais/pending overwrite |
| Latência total clique → pintura → ack | TEST_NOT_RUN | Medições anteriores cobrem preview in-process, não browser/rede/fila/read-back |

### Incidente de referência

`VISTA-TV-EDITOR-MUTATION-LATENCY-020`: `align_blocks` aguardava fingerprint que resolvia `get_weg_rol_target_pct`; 18.568 ms em preview frio, dos quais 18.506 ms de fonte. Após gate, cinco previews in-process: 48,3–77,1 ms, mediana 52,5 ms, zero resoluções de blocos. **Não extrapolar para latency end-to-end.**

### Invariantes

- `backend = source of truth`; `capability_surface` informa, backend autoriza.
- `READ CURRENT STATE → PREPARE → CONFIRM quando exigido → COMMIT → AUTHORITATIVE READ-BACK → VERIFY`.
- `expected_revision`/CAS, AuthZ efetiva fresca, playlist scope e boundary canônica preservados.
- Projeção visual local **não** persiste nem autoriza e deve ser reversível.
- Não sobrescrever silenciosamente alterações remotas ou descartar rascunho local.
- `editor ≡ preview ≡ TV` para geometria autorada confirmada; diferenças transitórias de projeção pendente devem ser visíveis no editor e nunca publicadas como commit.
- Mudanças de dados continuam executando validação/fingerprint necessários; somente categorias comprovadamente independentes os dispensam.

## 3. Pipeline e investigação de performance

Mapear, com correlação por request/op/revisão e sem logs de segredos:

`interação → comando local → fila do editor → request → AuthZ/validação → patch → DB/CAS → read-back → ack → reconciliação/store → primeiro frame correto`.

Coletar `click→first_visual`, `click→ack`, `click→confirmed_visual`; tempos de fila, rede, auth, reducer, persistência, serialização, cache e render React. Testar cold/warm, slide pequeno/grande, fontes lentas, dois editores e conflito. Baseline p50/p95 com amostra suficiente, sem confundir mediana de cinco execuções com p95.

Hipóteses a **testar**, não assumir: fila serial bloqueante, refetch redundante, invalidação global de cache operacional em geometria, payload/read-back muito amplo, renderização de todos os blocos, recomputação de dados, acoplamento do primeiro frame ao ack, mensagens WS obsoletas ou desordenadas.

**Orçamento TARGET inicial, não SLA comprovado:** comandos geométricos elegíveis produzirem feedback local no próximo frame útil, idealmente <100 ms; definir orçamento de ack/confirm a partir do baseline real, segmentado por ambiente e tipo de operação.

## 4. Roadmap executável (gates sequenciais)

### Fase 0 — Reancoragem e inventário (P0, primeira entrega)

1. Confirmar HEAD/git status, regras, READMEs, responsibility-map, docs de apresentação, VISTA matrix, frontend e testes.
2. Traçar handlers de `align_blocks`, `reorder_block_z`, distribuir, agrupar/desagrupar, mover, tamanho, estilo, texto, undo/redo; quem projeta local e quem aguarda ack.
3. Inventariar fila de escrita, revisão-base, ids estáveis, rollback, fluxo 409, eventos WS `presentation_updated`, presença e refresh/reconnect.
4. Instrumentar ponta a ponta e reproduzir com um editor e dois editores em sessões diferentes, em ambiente de teste autorizado.
5. Documentar `EXISTING_EQUIVALENT = YES|NO|TO_INVENTORY` por capability, `REUSE_DECISION = REUSE|EXTEND|NEW`, owners, baseline e riscos.

**Gate:** nenhuma mudança de semântica sem causa raiz, contrato e teste que falha antes do patch. **Entrega:** matriz de comandos, traces, lacunas e plano mínimo da Fase 1.

### Fase 1 — Remover trabalho redundante e aliviar o pipeline (P0)

1. Corrigir gargalos comprovados: fingerprint apenas onde dados mudam (já implementado para mutações geométricas, verificar cobertura); reconsultas/serializações/invalidações sem necessidade.
2. Avaliar especificamente `reset_comunicado_data_block_cache`: não relaxar invalidação se apresentação/dados puderem mudar; otimizar somente com prova de dependência e testes de TV/preview.
3. Avaliar read-back escopado apenas se contrato fornecer revisão autoritativa, estado afetado suficiente e recuperação segura de divergência; sem omitir verificação.
4. Manter ordenação/idempotência, segurança, audit trail, eventos e conflitos.

**Gate:** redução mensurada de `click→ack` e `click→confirmed_visual`, sem degradação de casos com dados e sem mudança de AuthZ. **Entrega:** patch mínimo no owner, testes funcionais e de performance antes/depois.

### Fase 2 — Projeção visual local segura (P1)

1. Reutilizar mecanismo local já presente no MFE para operações **determinísticas e reversíveis**, priorizando alinhar/distribuir/z-order; identificar comandos que exigem backend antes de projetar.
2. Apresentar estado pendente discreto por operação/revisão; não anunciar “salvo” antes do ack.
3. Reconciliar com `nativeConfig` do ack e revisão; lidar com rejeição, timeout, navegação, retry, seleção, histórico e undo/redo sem perda silenciosa.
4. Não duplicar reducer de domínio: mapear projeção exclusivamente ao contrato compartilhado já existente ou ao equivalente comprovado. Se faltar equivalência segura, parar e propor contrato mínimo no owner.
5. Não aplicar operação local sobre estado remoto desatualizado sem gate de revisão.

**Gate:** `click→first_visual` perceptivelmente imediato nos comandos elegíveis, confirmação correta, rollback visível e consistente, replay de conflitos sem corrupção. **Entrega:** UX + testes de corrida, falha de rede e reconciliação.

### Fase 3 — Concorrência entre editores e sincronização (P1)

1. Reusar revisão/CAS `409 REVISION_CONFLICT`, presença e WS de playlist. Inventariar se editor já consome os eventos e como identifica eco do próprio commit.
2. Informar “revisão remota disponível” e atualizar editor sem descartar modificações locais pendentes.
3. Com conflitos na mesma entidade/slide, impedir overwrite silencioso; fornecer estado atual e recuperação explícita (reload/reaplicar após revisão do usuário). **Não** auto-merge sem contrato seguro.
4. Com alterações em entidades diferentes, a política default continua a revisão da playlist inteira; aceitar ambos somente quando houver revalidação/merge explicitamente autorizado no backend, com atomicidade, teste e ADR.
5. Testar mudança remota durante projeção, exclusão de bloco, reconexão, múltiplas abas, falhas WS/polling, corrida de commits, 409, revogação de acesso e ordem de eventos.
6. Não bloquear toda a playlist por padrão, não usar presence como autorização e não publicar estado especulativo na TV.

**Gate:** dois usuários reais/sessões isoladas, conflitos detectados e recuperáveis, nenhuma perda silenciosa, autorização fail-closed. **Entrega:** testes E2E multiusuário + manual de UX de conflito.

### Fase 4 — Qualidade de renderização e otimização residual (P2)

Inventariar componentes lentos/store e recomputação de palco, implementar memoização/render seletivo somente com React profiling. Auditar lista de blocos, miniaturas, overlays e hotspots de zoom. Verificar paridade editor/preview/public, sem segundo renderer.

**Gate:** melhoria perceptível medida em slides representativos, preservando geometria autorada e FPS/responsividade.

## 5. Matriz de comando, segurança e sincronização

| Família | Projeção local | Fila/commit | Concorrência | Status |
| --- | --- | --- | --- | --- |
| Mover/redimensionar | reported existing; verificar | canônica | CAS | TO_INVENTORY |
| Agrupar/desagrupar | reported existing; verificar | canônica | CAS | TO_INVENTORY |
| Alinhar/distribuir | candidate após contrato | canônica | CAS + rollback | TARGET |
| Reordenar z | candidate após contrato | canônica | CAS + rollback | TARGET |
| Alterar dados/binding/transform | não assumir | canônica + fingerprint | CAS, AuthZ | PRESERVE |
| Undo/redo | inventariar efeito remoto | confirmar no boundary | colisões entre autores | TO_INVENTORY |
| Sync externa / WS | não grava | refresh/reconcile | stale event/echo | TO_INVENTORY |

As classes `PROVEN/TO_INVENTORY/PLANNED/TARGET` descrevem conhecimento, não estado de teste.

## 6. Testes e evidência exigidos em cada fase

- Backend: AuthZ fresca, scope playlist, CAS sob concorrência, conflito 409, rollback, side effects, fingerprint de dados e geometria, regressão de cache.
- Frontend: seleção/grupos, geometria, ack, 409, retry, offline, navegação, undo/redo, estado pendente, fila e ordem de promises.
- E2E: editor A e B em sessões distintas; mesmo bloco versus blocos diferentes; deleção remota; reconnect; conflito de revisão, não sobrescrita; paridade preview/TV após commit.
- Performance: cold/warm, duração do primeiro frame e ack, p50/p95, logs de trace redigidos e screenshots quando cabível.
- Resultado: `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`; não tratar HTTP 200, build ou arquivo existente como aceite.

## 7. Segurança, rollout e rollback

Writes humanos: usuário final com bearer, RBAC efetivo fresco e resource access validado no backend; principal de serviço não vira editor. Projeções pendentes não circulam pelo público. WebSocket/presença não substituem AuthZ. Não registrar token/cookie, não persistir draft especulativo como canônico. Mudanças de protocolo/revisão precisam compatibilidade e testes de clientes antigos. Preferir feature gate e rollout gradual **somente se o HEAD mostrar gate existente ou o custo for justificado**. Definir rollback e recuperação de estados pendentes antes da publicação. Deploy via Git da `main` apenas com autorização operacional explícita, reconstruindo somente os consumidores impactados; comparar SHA servido e read-back.

## 8. Dependências, decisões pendentes e STOP CONDITIONS

- **D1:** Confirmação do protocolo de presença/WS e consumo pelo editor. Sem isso, não prometer colaboração em tempo real.
- **D2:** Existe projeção geométrica canônica reutilizável sem duplicar reducer? Se não, voltar para Architecture/Coordination antes de nova abstração.
- **D3:** Política de conflito atual é CAS por playlist. Merge seletivo requer ADR, autorização e testes; não implementar como consequência implícita de UI otimista.
- **D4:** Invalidação global de dados em `notify_presentation_changed` pode ter custo; medir antes de alterar para evitar dados stale.
- **D5:** Fila serial e ack após persistência podem ser necessários para consistência. Medir e preservar sua ordem.
- **D6:** Read-back incremental só com contrato de verificação autoritativa e evidência de ganho.

Parar e reportar `INCONCLUSIVE` se causa/owner/contrato não puderem ser provados; `DOCUMENTATION_DRIFT`, `CONTRACT_DRIFT` ou `EXECUTION_DRIFT` quando fontes divergirem.

## 9. Handoff obrigatório para Cursor/Devin por entrega

`GOAL / OWNER / AUTHORITIES / CURRENT FACTS / ROOT CAUSE OR HYPOTHESIS / EXISTING_EQUIVALENT / REUSE_DECISION / ALLOWED SCOPE / FORBIDDEN SCOPE / CONTRACT IMPACT / SECURITY / TESTS / ACCEPTANCE / EVIDENCE TO RETURN / STOP CONDITION`.

Todo patch relevante deve entregar **VISTA/TV EXECUTION REPORT**: HEAD/base, arquivos inspecionados/modificados, causas, contratos, segurança, paridade, métricas antes/depois, residual search, resultado visível, gaps, SHA/deploy e veredito `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

## 10. Critério de conclusão da iniciativa

- Editor reage no próximo frame útil aos comandos geométricos elegíveis, com estado pendente explícito.
- ACK/commit/revisão/read-back continuam autoritativos.
- Dois editores simultâneos não perdem alterações silenciosamente.
- Conflitos são informados e recuperáveis; sem auto-merge indevido.
- TV/preview mostram somente versão confirmada e geometria correspondente.
- Performance e segurança comprovadas por teste de ponta a ponta, não apenas por benchmark in-process.

**Princípio:** HEAD before memory · owner before patch · contract before coupling · root cause before fix · reuse before invention · parity before workaround · evidence before assertion.
