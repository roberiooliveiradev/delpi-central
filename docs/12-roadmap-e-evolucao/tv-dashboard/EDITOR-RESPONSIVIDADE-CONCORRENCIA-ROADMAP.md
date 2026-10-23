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
| Gate de fingerprint por classe de operação | PROVEN | Geometria não resolve fonte. `upsert_block` continua no conjunto de dados e só dispensa a consulta quando o diff persistido é exclusivamente visual; vínculo, parâmetro, transformação e chave não classificada continuam resolvendo |
| Read-back autoritativo | PROVEN | ack contém `nativeConfig` persistido e `appliedOps`, carimbo de formatação |
| Revisão esperada e erro de concorrência | PROVEN | `expected_revision`, `RevisionConflictError` 409 |
| CAS de revisão no repositório | PROVEN | `TvPresentationWriteService._persist` traduz conflito de repositório; comentário documenta `FOR UPDATE` transacional; revalidar teste do CAS real |
| Notificação por playlist | PROVEN | `notify_presentation_changed` publica `presentation_updated` via realtime hub |
| Presença de editor e destinatário específico | PROVEN | `PresentationRealtimeHub` mantém `clientId`/`userId`, `canEdit`, TTL 90 s e envio direto; não prova UX de reconciliação |
| Invalidação de cache no notifier | PROVEN | `reset_comunicado_data_block_cache()` é invocado; efeito/custo de invalidar por geometria ainda TO_INVENTORY |
| Atualização local para mover/tamanho/grupo | REPORTED | Relatório `VISTA-TV-EDITOR-MUTATION-LATENCY-020`; revalidar os handlers efetivos no HEAD |
| UI consistente com dois editores simultâneos | TO_INVENTORY | Presença + WS + CAS não provam ausência de perdas visuais/pending overwrite |
| Latência total clique → pintura → ack | TEST_NOT_RUN | Preview in-process revalidado em 2026-10-22 (seção 11). Browser, fila, rede e read-back continuam sem amostra |

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

## 11. Fase 0 — evidência `VISTA-TV-EDITOR-E2E-LATENCY-CONCURRENCY-022`

**HEAD:** `2ed5b53022` (`main`, limpo). Reancorado em 2026-10-22. Não marca Fase 1, 2 ou 3 como concluídas. Não houve deploy nesta tarefa.

### Pipeline comprovado no código

```text
comando
→ updateBlocks (move, tamanho, grupo, estilo, prefixo/sufixo) ou espera do ack (alinhar, distribuir, z-order)
→ enqueuePlaylistWrite (FIFO por playlist + Web Lock same-origin)
→ POST presentation-mutations com If-Match
→ require_playlist_access(edit) → preview → update_slide (CAS FOR UPDATE)
→ nativeConfig carimbado no ack
→ notify_presentation_changed (sem clientId) → reset_comunicado_data_block_cache + WS presentation_updated
→ o editor recarrega a playlist; draft/pending local cobre o slide aberto
→ 409 REVISION_CONFLICT → server-wins, draft marcado conflitado, aviso
```

Autosave de slide (debounce 400 ms) e `slide_draft` (120 ms) são um segundo caminho de escrita, também sob a revisão da playlist. O Web Lock não coordena dois usuários.

### Baseline desta sessão

Ambiente: processo da API em execução, preview sem persistir, playlist `028b0aa6-6619-46ba-96ea-c60f54eef3f8`, slide `323a2e78-1423-46c9-b940-6450ba39724b`, n=3. Não é tempo de browser.

| Operação | Preview (ms) | `resolve_blocks` | `enrich_data_models` |
|---|---|---|---|
| `align_blocks` | 60,8 / 42,9 / 40,5 (mediana 42,9) | 0 | 0 |
| `upsert_block` só de prefixo | 41,0 / 41,3 / 42,4 (mediana 41,3) | 0 | 0 |

`CLICK_TO_FIRST_VISUAL_MS`, fila, rede, persistência, read-back e `CLICK_TO_CONFIRMED_VISUAL_MS` continuam `TEST_NOT_RUN`. Os 18 568 ms e 15 139 ms citados nas tarefas 020/021 são amostras históricas in-process, não baseline de navegador.

Alinhar/distribuir/z-order só chamam `updateBlocks` se o ack falhar. Mover, tamanho, grupo, cor, fonte e prefixo pintam antes do HTTP. A confirmação visual desses comandos ainda espera o ack e, em seguida, o reload disparado pelo próprio `presentation_updated`.

### Concorrência — comportamento do código, sem sessão dupla

| Cenário | Comportamento atual | E2E |
|---|---|---|
| Componentes diferentes | CAS é da playlist inteira. A segunda escrita com a mesma revisão recebe 409. Não há merge. | TEST_NOT_RUN |
| Mesmo componente | O commit vencedor grava o `nativeConfig` inteiro. O perdedor é rejeitado e avisado. | TEST_NOT_RUN |
| Exclusão concorrente | Mesmo CAS. Quem tem a revisão corrente confirma. | TEST_NOT_RUN |
| Commit pendente | `slide_draft` remoto não cobre slide com edição local. O reload preserva pending. O save seguinte com revisão velha cai em 409 e o server-wins descarta o pending. | TEST_NOT_RUN |
| Reconexão | Ao conectar, o editor chama o mesmo reload. Presença expira em 90 s. | TEST_NOT_RUN |
| Undo após mudança remota | Undo do slide é local. Mudança remota aceita entra na pilha. Um undo seguinte pode desfazer o remoto na tela e o autosave pode gravá-lo. | TEST_NOT_RUN |

`presentation_updated` não traz `clientId`. Receber o evento não prova que o palco do outro editor ficou correto. Presença e seleção remota existem; não autorizam escrita.

### Execução — VISTA-TV-EDITOR-MULTIUSER-UNDO-SAFETY-023 (P0, integridade)

**Comportamento anterior (reproduzido, não só inspecionado).** `shouldStackRemoteComunicadoUndo` empilhava o config pré-remoto na pilha local de undo quando uma baseline externa era aceita. O undo do slide reaplica snapshot do `nativeConfig` **inteiro** e dispara persistência com `If-Match` da revisão corrente — o CAS passa porque a revisão é a corrente, então o lost update é silencioso. Prova end-to-end na API local (playlist isolada, dois usuários reais): rev2 base → A edita `blk_x` (rev3) → B edita `blk_y` (rev4) → "undo" de A envia o snapshot pré-remoto com `If-Match:4` → **HTTP 200 → rev5 com `blk_y` revertido**. RESULT=FAIL SILENT_LOST_UPDATE.

**Causa raiz / owner.** O defect não está no CAS (a revisão confere) nem no backend — está na costura de histórico do editor: snapshots de slide inteiro de baseline anterior eram reaplicáveis sobre baseline nova. Owner: MFE `plugins/tv-dashboard` — `comunicadoEditorValueSync.ts` (predicado de decisão) + `comunicadoEditorContext.tsx` (efeito de sync) + `PlaylistEditorPage.tsx` (sinal de baseline externa).

**Contrato do histórico definido.** Ações locais empilham normalmente. Baseline externa aceita (outro editor, copiloto, `slide_draft` de peer, restore do deck) **invalida** past+future locais: undo/redo fica indisponível em vez de reaplicar snapshot incompatível. Desfazer mudança remota pertence ao restore governado do deck (`restorePlaylistHistorySnapshot`, `expectedRevision` + 409 + server-wins), que continua intacto.

**Discriminador próprio × estrangeiro.** `presentation_updated` não carrega `clientId` — a distinção usa a revisão: baseline externa = `remoteRevision > knownPlaylistRevision` **e** `> readSharedPlaylistRevision` (write-head compartilhado publica commits próprios/de abas irmãs no ack). Acks da própria escrita sobem `remoteConfigRevision` (aceita projeções do servidor) mas **não** `foreignConfigRevision` — assim a pilha local não é zerada pelo eco do próprio save nem por normalização de read-back.

**Correção mínima.** `shouldStackRemoteComunicadoUndo` → `shouldInvalidateLocalComunicadoHistory` (mesmo predicado, semântica invertida: `resetLocalHistory()` no lugar de `pushPast`). Novo prop `foreignRemoteRevision` no provider; contador `foreignConfigRevision` na página, bumpeado em reload com baseline externa e em `slide_draft` de peer (já filtrado por clientId próprio). Proteções existentes preservadas: gate `dirty`/`hasLocalComunicadoEdits` não aplica remoto sobre pending; 409 → `applyServerWinsConflict` (explícito + aviso); Web Lock/fila FIFO/CAS intactos.

**Cenários A–F — veredito pós-fix.** A (componentes distintos): remoto aceito → pilha zerada → undo no-op → `blk_y` preservado. B (mesmo componente): idem. C (commit pendente): gate `dirty` bloqueia aceite remoto; save seguinte com revisão velha → 409 explícito → server-wins + aviso. D (redo): future também zerado. E (exclusão remota): sem recriação — pilha vazia. F (reconexão): reload detecta baseline externa e invalida.

**Testes.** `comunicadoEditorValueSync.test.ts` reescrito para o predicado novo (5 casos: invalida remoto estrangeiro, invalida restore de deck, não invalida bump sem mudança, não invalida troca de slide, não invalida sem baseline externa). Novo `comunicadoEditorContext.remoteHistory.test.tsx` no nível do provider (4 casos: undo vira no-op após remoto; ack próprio preserva pilha; redo invalidado; edição pós-remota reempilha). Suítes relacionadas: 15 + 90 + 3 tests PASS. Vitest total do MFE: 3 falhas PRÉ-EXISTENTES em arquivos não relacionados (verificado em HEAD via stash).

**Riscos residuais.** (1) Race estreita ack↔WS: reload pode resolver antes do `recordWriteRevision` publicar o head — a própria escrita seria vista como externa e a pilha zera (direção conservadora segura). (2) Desfazer mudança remota exige o painel de histórico do deck (restore governado), não mais Ctrl+Z — trade-off do contrato. (3) E2E visual em dois browsers reais continua `TEST_NOT_RUN` — a prova foi API + provider tests; validação visual multiusuário fica para a fase de smoke E2E.

### Execução — VISTA-TV-EDITOR-SELF-WS-RELOAD-OPTIMIZATION-024 (P1, desempenho)

**Comportamento anterior (reproduzido).** Todo `presentation_updated` — incluindo o eco do próprio commit — disparava `reloadPlaylistFromServer` incondicional (`getPlaylist` + `refreshPreviewThumbnails` + `deckHistory.handleRemoteUpdate`/`loadHistory` ≈ 3 GETs + rebuild de estado por escrita própria). O evento WS não carregava revisão da playlist nem identidade do autor — sem correlação possível entre ACK e evento. Prova no ambiente local: commit próprio `ack_rev=N` era seguido do evento que iniciava novo fetch do estado que o próprio ACK acabara de confirmar.

**Causa raiz / owner.** Ausência de correlação de revisão no contrato do evento: `notify_presentation_changed` não publicava `playlistRevision`, então o consumidor não podia distinguir "rev já incorporada" de "rev desconhecida". Owner do contrato: backend `presentation_change_notifier` (ponto único de notify, cobre editor REST, MCP, GPT e copiloto). Owner do consumo: `PlaylistEditorPage.onSync`.

**Correção mínima.** (1) O notifier resolve `playlistRevision` pós-commit quando não informado (`PlaylistRepository().get_revision`), falha → omite o campo (consumidor recarrega — safe). (2) `PresentationRealtimeEvent.playlistRevision?: number`. (3) `hasPendingPlaylistWrite` expõe a lane. (4) Predicado `resolvePresentationSyncReloadDecision` decide o skip no `onSync`; reload continua para reconexão (`onSync(undefined)`), payloads antigos sem revisão e qualquer revisão acima do rastreado.

**Contrato de supressão segura.** `tracked = max(knownPlaylistRevision, sharedWriteHead)`. Skip se `eventRev <= tracked` (já incorporado — próprio ACK, irmão, ou estrangeiro já carregado), ou `eventRev == tracked+1 && write em voo` (ambíguo WS-antes-do-ACK: se for estrangeiro de fato, o CAS do pendente vira 409 → server-wins — nada se perde). Caso contrário reload. Fecha o residual #1 da task 023: eco próprio não alcança mais o caminho de baseline externa.

**Pipeline medido (local, WS real).** `A_OWN`: `rev 11 → ack 12 (60–95ms) → ws playlistRevision=12` → suprimido. `B_FOREIGN`: `ack 13 → A recebe playlistRevision=13` → `13 > head 12` → reload. TV pública não usa o predicado — continua refetch em todo evento (`EDITOR ≡ PREVIEW ≡ TV` preservado).

**Reload count antes/depois (por commit próprio).** Antes: ~3 HTTP (playlist + preview + history) + rebuild completo. Depois: 0. Eventos externos: inalterados.

**Testes.** `presentationSyncReloadDecision.test.ts` (8: ack incorporado, atrasado/duplicado, WS-antes-ACK c/ e s/ pendente, estrangeiro adiante, sem revisão, NaN, estado inicial). `test_presentation_sync.py` +2 (revisão no payload; omissão em falha de lookup). Suítes: hooks+context+utils 142 PASS; realtime 12; backend revision/realtime/sync 27 PASS. TSC/lint: somente erros pré-existentes (verificado em HEAD via stash).

**Riscos residuais.** (1) Skip ambíguo `tracked+1` assume que lane em voo implica commit próximo — se a escrita falhar por outro motivo o estado local fica adiantado otimisticamente até a próxima sync (mesmo comportamento anterior ao otimismo, sem perda). (2) E2E visual com dois browsers segue `TEST_NOT_RUN`; prova coberta por WS real + testes. (3) `slide_draft`/`presence` inalterados (já filtram por `clientId`).

#### 024-R1 — endurecimento contratual (rework de `8b4a1527bd`)

**Risco A — supressão ambígua: CONFIRMADO e corrigido.** A versão original dispensava `tracked+1` apenas por haver escrita em voo; se o evento fosse estrangeiro e a escrita local falhasse por erro não-CAS (rede, timeout, cancelamento), a remota ficava permanentemente ignorada até outro evento/reconexão. Correção (Opção B — reconciliação diferida): evento ambíguo é registrado em `pendingAmbiguousSyncRevision` e avaliado obrigatoriamente no settle da lane (`onPlaylistWriteSettled`). Fundamento de correção: a lane serializa commits por playlist — uma escrita pendente que **fulfilla** comita exatamente `tracked+1` (ou prova via CAS que `tracked` já cobria o evento); o ACK ≥ ambíguo em `recordWriteRevision` limpa o marcador. Rejeição (409, timeout, cancelamento) sem cobertura → reload obrigatório. Sem timers: `queueMicrotask` apenas ordena a avaliação depois do processamento do ACK.

**Risco B — proveniência de `playlistRevision`: semântica corrigida e documentada, não reimplementada.** `get_revision` no notify lê pós-commit → o campo é **piso** (`>=` rev produzida pela escrita disparadora), nunca identidade do commit — um commit concorrente pode elevá-lo, mas subestimar é impossível (leitura após o commit só vê >=). Para o consumidor isso é estritamente seguro: superestimar só causa um reload a mais; suprimir por `eventRev <= incorporado` nunca esconde estado não visto. Prova interleaved em `test_presentation_sync.py` (A comitou 41, B 42 → evento carrega 42). Passar a revisão exata do commit exigiria `RETURNING revision` em ~15 métodos do repositório + todos os produtores — fora de escopo e desnecessário ao contrato; o parâmetro `playlist_revision` explícito segue tendo precedência quando o caller o conhece.

**Veredito por cenário.** A1 (WS→ACK próprio): ambíguo registrado → settle fulfilled → ACK publica rev → marcador limpo → sem reload. A2 (estrangeiro + 409): settle rejected → `amb > tracked` → reload diferido + recuperação server-wins do 409. A3/A4 (falha não-CAS/cancelamento): idem — **a remota não fica mais ignorada**. A5 (duas revs remotas): `N+2 > tracked+1` → reload imediato, nunca suprimido. A6 (duplicado/atrasado): `<= tracked` → incorporado.

**Métricas antes/depois do R1.** `OWN_ACK_RELOAD_COUNT`: 0→0 (mantido). `AMBIGUOUS_EVENT_RECOVERY_COUNT`: antes 0 (evento podia morrer ignorado) → 1 obrigatório por settle não confirmado. `HTTP_REQUESTS_PER_OWN_COMMIT`: inalterado. Custo residual admitido: settle rejeitado pode disparar um reload adicional além do server-wins do 409 (corrida estreita, direção segura).

### Execução — VISTA-TV-EDITOR-LOCAL-VISUAL-PROJECTION-025 (P1, resposta visual imediata)

**Estado anterior.** `alignSelected` (alinhar ×6, centralizar ×2, distribuir ×2, variantes `align-slide-*`) e `applyLayerOrder` (bring-to-front, send-to-back, bring-forward, send-backward) eram **ACK-first**: `applyLocal` só rodava no `.then` quando o commit retornava `null`. Clique→primeira pintura = RTT completo da mutation (~96–125ms warm, 510ms cold na playlist isolada local) + parse/aplicação.

**Causa raiz.** Os handlers não usavam o mecanismo local-first já estabelecido (`updateBlocks` + `ackBlocksMutation`, mesmo padrão de `sameSizeSelected`, `nudgeSelected`, `reorderBlockLayer`, drag). `EXISTING_EQUIVALENT = YES` — nenhum reducer novo foi criado.

**Decisão contratual importante.** Os comandos passaram a persistir via `upsert_block` do resultado projetado em vez dos ops `align_blocks`/`reorder_block_z`, porque:
- `align_blocks` no backend **não reconcilia conectores** — o ack canônico carregaria geometria de conector divergente do palco já reconciliado (`reconcileConnectorsAfterDrag`);
- `reorder_block_z` no backend atribui `max_z+1..` só aos selecionados, enquanto a projeção local reindexa 1..N — mesma ordem relativa, valores divergentes → toda mutação de camada produziria ack ≠ projeção.
Com `upsert_block`, **persistido ≡ projetado por construção** → ack de mesma autoridade, sem salto visual sistemático. Os ops `align_blocks`/`reorder_block_z` permanecem intactos e funcionais para callers não-editor (MCP/GPT/VISTA) — verificado ao vivo (`align-left`/`align-right` RTT ~112ms, rev 16→22).

**Mecanismo reutilizado.** `updateBlocks` (histórico + `syncAllConnectors`/`pruneOrphanConnectors` + autosave full-config) → `ackBlocksMutation(changed)` → `ackUpsertBlocksWithGeneration` (gate de geração contra ack stale) → `commitUpsertBlocks` → fila FIFO por playlist + `expected_revision`/CAS + `If-Match`. O conjunto `changed` é diff por identidade contra o estado anterior — captura membros alinhados/reindexados **e conectores reconciliados**. No-op real (`changed` vazio: seleção já alinhada, `<3` unidades para distribuir) não projeta nem commita.

**Contratos preservados.** CAS/`expected_revision` intactos (ops passam pela mesma `applyPresentationMutations`/`withWriteEpoch`); geração descarta ack stale entre comandos consecutivos (teste A→B fora de ordem); 409 segue server-wins da infraestrutura de escrita existente; falha não-CAS mantém a projeção no palco sem fingir confirmação (mesma semântica de sameSize/drag — a recuperação é do autosave full-config e da reconciliação WS/024-R1); histórico segue um passo lógico por comando (ver quirk abaixo); WS/reconciliação não tocadas — o suppression do 024/024-R1 não usa projeção otimista como prova de incorporação.

**Quirk preexistente documentado.** `parseComunicadoConfig` → `normalizeBlock` materializa defaults de estilo no ack; o fingerprint do canônico difere da projeção esparsa e `commitWithHistory` pode empilhar uma segunda entrada de histórico visualmente idêntica. É o comportamento vigente de **todos** os caminhos local-first (sameSize/drag/insert) — não introduzido aqui; correção global seria normalizar a projeção antes do upsert, fora de escopo.

**Métricas.** `CLICK_TO_FIRST_VISUAL_MS`: antes = RTT mutation (~112ms warm local, >500ms cold) → depois = commit síncrono `commitWithHistory` (um React commit, <16ms alvo). `CLICK_TO_CONFIRMED_VISUAL_MS`: inalterado (~RTT). `HTTP_REQUESTS_PER_COMMAND`: 1 mutation → 1 mutation (mesma contagem; o autosave full-config existia nos dois mundos). `VISUAL_CORRECTION_COUNT`: 0 sistemático — persistido ≡ projetado.

**Testes.** `useComunicadoEditorBlocks.alignProjection.test.ts` (8): pinta antes do ACK + upsert projetado (sem op align), ack idêntico sem undo extra induzido, distribute-h imediato, no-op <3 sem commit, A→B com ack stale dropado pela geração, falha não-CAS sem falso sucesso/reversão cega, z-order bringToFront imediato via upsert (sem reorder_block_z), undo pós-ack. Regressão: 103 testes dos hooks/utils/align/layer/mutation PASS; suíte completa `src/` sem novos failures (5 arquivos já falhavam no baseline; `PlaylistPreviewPage.loading` flaky sob carga, PASS isolado).

**Limitações.** E2E visual dois-browsers `TEST_NOT_RUN`. Cenários multiusuário A–F regidos pelo mesmo contrato de escrita do sameSize (upsert + autosave + CAS + WS) — sem nova superfície de conflito, mas sem sessão dupla executada nesta task. Undo de projeção pode precisar de 2 passos quando o canônico normaliza estilos (quirk acima).

### Cache

`notify_presentation_changed` limpa `reset_comunicado_data_block_cache` também em mutação visual. O clear em si não foi cronometrado. A consulta seguinte da TV/prévia deixa de usar o cache. Não alterar esta política sem teste de dado obsoleto.

### Reuso

| Capacidade | Existente | Decisão |
|---|---|---|
| Projeção local de move/estilo/grupo | YES | REUSE |
| Projeção de alinhar/z-order com rollback | YES (025) | REUSED — `updateBlocks` + `ackBlocksMutation` |
| Fila FIFO + Web Lock | YES | REUSE |
| Revisão / 409 / server-wins | YES | REUSE |
| Read-back `nativeConfig` | YES | REUSE |
| Presença e `slide_draft` | YES | REUSE |
| Reconciliação de dois editores no mesmo bloco | NO | Fase 3, sem auto-merge |
| Telemetria clique→frame | NO | EXTEND quando for medir de verdade |
| Render seletivo | TO_INVENTORY | não propor ainda |

### Próximo diff recomendado

Não é projeção otimista nem sala nova.

1. **Fase 1 residual:** medir, no editor autenticado, fila, rede, persistência, read-back e o reload do próprio `presentation_updated`. Só então decidir se o eco sem `clientId` ou o clear de cache entram num patch. Owner: `PlaylistEditorPage` + `notify_presentation_changed`. Teste: uma sessão, comandos de alinhar e prefixo, sem gravar cenário irreversível.
2. **Fase 2 (feita — 025):** alinhar/distribuir/z-order projetam via `updateBlocks` + `ackBlocksMutation` (sem reducer novo; ack continua autoridade). Residual: E2E visual dois-browsers e o quirk de histórico por normalização de estilo no ack.
3. **Fase 3:** duas sessões reais nos cenários A–F. Conflito continua 409 + aviso. Undo não pode persistir por cima da revisão do outro usuário. Sem CRDT, OT ou merge por campo até existir ADR.

### Testes nesta reancoragem

| Suíte | Resultado |
|---|---|
| `test_presentation_realtime.py`, `test_playlist_revision_http.py`, `test_editor_mutation_fingerprint_scope.py` | PASS — 36. Prova hub, revisão HTTP e gate de fingerprint. Não prova dois browsers. |
| Vitest da fila, sync e undo | TEST_NOT_RUN — o worktree não tem `node_modules` do MFE. |
| Sessões A–F e clique no palco | TEST_NOT_RUN |
