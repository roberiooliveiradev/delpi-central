# DÉLIA — VD-F06 | Plano completo de implementação end-to-end — Devin

**Data:** 2026-10-23. **Estado:** IMPLEMENTATION_EXECUTION_PLAN / PLANNED, condicionado às authorities e aos gates abaixo. **Escopo:** backend STT incremental + frontend editor/UX + integração + testes/reworks + deploy e verificação. **Não equivale a código implementado nem a autorização de mudança de fase.**

**TASK_ID principal:** `DELIA-VD-F06-PROGRESSIVE-DICTATION-END-TO-END-IMPLEMENT-TEST-REWORK-DEPLOY-01`  
**Executor:** Devin. **Repo:** `roberiooliveiradev/delpi-central`; branch final `main`.  
**Fonte de produto:** [123 — especificação VD-F06](./123-voice-dictation-progressive-live-editing-ux-specification.md). **Base funcional:** [119](./119-conversation-audio-recorder-composer-product-ux-specification.md), [120](./120-voice-dictation-composer-visual-refinement-ux-specification.md), [dictation.transcription.v1](./contracts/dictation-transcription-contract-v1.md). **Referência na elaboração:** HEAD `5e35e14dae54ea8620631d105a9285526b1b862b`; revalidar antes da execução.

## 0. Resultado entregue e princípio de verdade

O usuário fala e **vê texto parcial real enquanto fala**; simultaneamente pode clicar, mover o caret, selecionar, substituir, digitar, apagar, colar, desfazer/refazer e continuar ditando em qualquer ponto. Transcrição final corrige apenas o segmento ainda pertencente ao STT; **nunca apaga a edição humana**. Foco permanece no editor. O envio é exclusivamente manual. A experiência funciona em full-page, **Dock real do Portal** e mobile. Se a capacidade incremental real não estiver disponível, usar o fluxo honesto de gravação seguida de transcrição do VD-F03 — jamais animar texto final como se fosse streaming.

**Aceite final exige:** contrato e provider/adapter válidos, fluxo de fala real pt-BR, merge e conflitos reproduzidos, latência medida, privacidade, testes e2e, regressões, deploy validado e evidência SHA/config. `HTTP 200 != OUTCOME PASS`.

## 1. Reancoragem e controle de autoridade (antes de qualquer diff)

1. `git fetch origin`, `git status --short`, `git rev-parse HEAD`, `git rev-parse origin/main`; isolar e preservar alterações concorrentes, não usar force push.
2. Ler Project Instructions/`.cursor` e authorities **16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25**, arquitetura técnica, product spec, docs temáticas 119/120/123, contrato v1 e ledger no HEAD.
3. Identificar owner, fase, CP/RQ, decisões congeladas, consumers, contracts, atual runtime, SHA implantado e dependências operacionais; não inventar CP nem promover fase.
4. Fazer inventário real por responsabilidade → owner → fonte canônica → consumers → contrato → implementação → testes → outcome. Zero search results não prova inexistência.
5. Provar formalmente por área: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`; `REUSE_DECISION=REUSE|EXTEND|NEW`, especialmente STT provider/adapter, admission/status, áudio, transportes streaming, auth, MessageComposer, AudioRecorderControl/useLocalAudioRecorder, DeliaComposer, API client, draft merge, focus/selection, deploy.
6. Em evidência que contrarie decisões superiores: **STOP → EXECUTION_DRIFT/ARCHITECTURE_DECISION_REQUIRED**; não criar novo provider/engine/editor ou protocolo unilateralmente.

## 2. Baseline comprovado nesta elaboração (não extrapolar)

- Contrato `dictation.transcription.v1`: `POST /dictation/transcriptions` recebe captura completa e devolve transcript final; `GET /dictation/status` é capability admission. A especificação do provider o descreve como família `openai_compatible` com `input_audio`; **isso não prova reconhecimento streaming em tempo real**.
- `plugins/delia/src/api/dictationClient.ts` transcreve blob após gravação; `DeliaComposer.tsx` tem merge determinístico em seleção/caret VD-F05 e descarte de resposta tardia.
- `plugins/plugin-ui` oferece `MessageComposer`, `AudioRecorderControl` e `useLocalAudioRecorder`. Revisar contratos reais/versões atuais antes de mexer.
- Status de streaming real, suporte nativo provider, WebSocket/WebRTC/SSE de áudio, compatibilidade de browser e custos: **TO_INVENTORY**. Não anunciar implementado por constar neste plano.

## 3. Gate crítico de viabilidade técnica STT (Stage 0, bounded)

**Objetivo:** demonstrar por experimento e contrato que existe caminho legítimo de resultados **parciais e finais antes do encerramento da captura**.

Investigar nesta ordem:
1. Reutilização da capability/provedor STT configurado, endpoints oficiais, SDK, streaming incremental (áudio upstream + eventos parciais), limitações de modelos `input_audio`, status atual de credenciais sem expô-las.
2. Adapters e interfaces STT existentes em `delia-api`, event/stream transport já usado, proxy/gateway (Upgrade/SSE/WebSocket), limites timeout/body/ingress, segurança de conexão e cancellation. Não acoplar a UI a mechanics do provider.
3. Browser: captura chunked/streaming via `MediaRecorder`/WebAudio ou estratégia suportada pelo provider; MIME, duração, chunk boundaries, microfone, permissão, compatibilidade. A escolha não deve criar buffering ilimitado.
4. Executar prova de conceito isolada **com áudio real pt-BR, amostras autorizadas**, verificando evento parcial antes do final, texto final, latência fim-a-fim, erros, reconexão e custo. Não gravar conteúdo sensível em logs.
5. Matriz objetiva: `STT_INCREMENTAL_SUPPORTED=YES|NO|INCONCLUSIVE`, `EXISTING_EQUIVALENT`, `REUSE_DECISION`, `TRANSPORT_SUPPORTED`, `SECURITY_GATE`, `EXPECTED_LIMITATIONS`.

**Go:** reusar/estender provider/adapter existente e transporte legítimo. **No-go:** se o provider atual não suporta resultados parciais, **não mentir com pseudo-streaming** nem trocar provider unilateralmente. Documentar alternativa aprovada (provider neutral adapter) e abrir `ARCHITECTURE_DECISION_REQUIRED`; executar só fatias independentes de UI/testes/fallback. Inventário não deve se tornar loop infinito: uma rodada de inspeção + uma PoC reproduzível + decisão.

## 4. Stage 1 — Contrato incremental antes do código de produção

Criar **especificação de contrato versionado**, preservando integralmente v1, com:
- Owner backend, consumer `plugins/delia`, AuthN bearer/context, Core/AuthZ admission quando aplicável, capability status, permissões de mic e política de envio de áudio, guardrails fail-closed.
- OperationIds estáveis e HTTP/OpenAPI quando aplicável; escolher SSE/WS/HTTP-chunks conforme evidência real. Não inventar endpoint antes de confirmar infraestrutura.
- Sessão e correlação: `session_id`, `segment_id`, `sequence`, `revision`, `is_final`, `text`, timestamps opcionais; tipos `started/partial/final/error/cancelled/completed` ou equivalentes reais.
- Semântica de `partial` substitutivo vs delta anexável **explicitamente declarada**, dedupe/out-of-order, final exatamente uma vez, deadline, cancel, limite de áudio/sessão, tamanho do texto e comportamento em perda de rede.
- Erros tipados: unavailable, admission denied, unsupported MIME, provider timeout, rate limit, quota/oversize, invalid sequence, remote dropped; status e fallback definidos.
- Privacidade/observabilidade: IDs, duração, métricas de latência e bytes; **jamais** áudio/transcript/secrets em logs padrão, traces de payload, memory ou embeddings.
- Estados `PREPARE/ACT` não envolvidos: transcript é input editável e não autoriza envio/execution.
- Versionamento e backward compatibility de `dictation.transcription.v1`; teste contract consumer-driven antes de integração.

**Decision gate:** não implementar streaming sem contrato revisado à luz das authorities; novos endpoints, autenticação, provider ou infraestrutura exigem aprovação do owner legítimo, não aceitação tácita deste plano.

## 5. Stage 2 — Backend real / provider-neutral

Reutilizar serviços, ports e adapters legítimos; menor diff:
1. Adicionar **capability/admission** explicitamente distinguindo `batch` e `incremental`, sem anunciar live quando indisponível. Preservar status e contract v1.
2. Implementar interface/adapter de sessão incremental no boundary autorizado, se comprovado; mecânica de provider fica no adapter, não em planner, Domain ou UI.
3. Implementar ciclo session lifecycle: start, audio ingress ordenado/bounded, partial/final dispatch, completion, cancel/timeout, cleanup, concurrent sessions/capacity, abort on disconnect. Evitar engine paralelo quando o existente dá conta.
4. Garantir envio áudio apenas à capability admitida, sem usar chat model/RAG/agents, e controlar custo, bytes/duração, backpressure, limites de requisições, microfone e tempo.
5. Não expor credenciais no frontend; autenticar backend; Core/domain authorization respeitados conforme boundary real.
6. Observabilidade determinística de latency-to-first-partial, final latency, errors, drop/retry, session cleanup, sem persistência de conteúdo.
7. Testes RED → GREEN para adapter com provider fake determinístico, contract tests, erros, rate limit, security negative, cancel, disconnect, duplicate/out-of-order. **Prova real** com provider compatível, modelo/config/SHA identificados.
8. Nunca mudar o resultado de transcrição em fato governado ou comando; backend devolve somente texto reconhecido.

## 6. Stage 3 — Núcleo determinístico de edição/âncoras e conflitos

**Executar antes de integrar áudio.** Implementar na camada apropriada, reutilizando `MessageComposer` e seleção/caret da DÉLIA, algoritmo testável sem DOM/provider.
- Modelo mínimo de segmento: session/segment/revision, status partial/final, âncora de inserção, seleção-alvo e faixa ainda possuída por STT. Document revisions/edit operations para transformar âncoras após digitação, deleção, paste, undo/redo e entrada touch.
- Cada segmento ancora no caret/seleção no **início daquele segmento**; movimento durante a fala só vale para o próximo. A finalização só substitui texto provisional intacto daquele segmento.
- Edição humana **dentro** de provisional invalida substituição automática daquele trecho; oferecer sugestão pendente ou preservação determinística sem overwrites. Usuário decide conflitos. Não salvar offsets obsoletos e não deslocar caret por eventos STT.
- Duplicatas, revisions antigas, sessão cancelada e resultados após unmount são descartados; segmento final não pode retroceder a partial.
- Trabalhar com Unicode/UTF-16, grapheme boundaries, IME composition, emoji e colagens, sem quebrar seleção do navegador.
- Não instalar ProseMirror/Slate/Lexical ou outro editor sem demonstração concreta de inviabilidade do textarea+composição mínima e gate arquitetural.
- **Testes adversariais baseados em operações** e property tests para invariantes de preservação humana, idempotência e texto vizinho intacto.

**Critérios negativos obrigatórios:** falha nunca apaga draft, cancelar não limpa transcrição editada, nenhuma substituição silenciosa de seleção alterada, sem auto-submit.

## 7. Stage 4 — Frontend UI/UX no plugin-ui e integração DÉLIA

- **plugin-ui owner:** extensão de `MessageComposer`, `AudioRecorderControl`, `useLocalAudioRecorder` e surfaces já existentes; uma só moldura. Reutilizar `IconButton`, `HelpTooltip`, tokens, waveform baseada em amplitude real. Não criar segundo composer nem visualização de áudio falsa.
- **plugins/delia consumer:** client incremental tipado, feature admission, session correlation e wired lifecycle; fallback v1. Não colocar detalhes provider no component. Componibilizar com ConversationQueue, composer Stop, DraftRecovery e recursos de voz existentes.
- Estados: writing/requesting_permission/listening/partial/reconciling/paused/finalizing/review/recoverable_error/unavailable, com controles iniciar, pausar, retomar, finalizar, descartar e retry contextual. Registrar quando pausa do stream é real vs somente local; nunca mostrar pausa falsa.
- Editor não pode desaparecer ou bloquear digitação ao iniciar/continuar fala; caret, seleção e foco livres; provisional distinguível com semântica acessível e sem impedir edição. Se textarea não permitir marcação inline, escolher menor representação acessível que não interfira na edição.
- Review manual antes de enviar; sem auto-submit. Transparência contextual de áudio remoto, não reintroduzir banner amarelo global (doc 120).
- Full-page, Dock real (não somente viewport estreita), mobile 320/360/375/420, teclado virtual, zoom 200%, dark/light/reduced motion, A11Y; opção de fallback honesta.
- Desativar funcionalidade incremental por capability flag/admission quando não suportada e preservar gravação+transcrição v1 sem regressão.

## 8. Stage 5 — Matriz de testes e generalização obrigatórias

**Cobertura VD-L01–VD-L16 da spec 123**, com scripts, vídeos/screenshots e relatórios por SHA/config. Adicionar:
- Backend: contract v1 e incremental, auth/limit/errors/transport/reconnect, doubles, late partial, abort, chunk drops, pause/resume, cleanup e privacidade.
- Unit determinístico de reconciliação: inserir no início/meio/fim, substituir seleção, dois segmentos simultâneos, alterações na faixa do STT, edição antes/depois da faixa, colagem, undo/redo, IME, touch, Unicode, resposta final atrasada, reorder, duplicate.
- Frontend: bodyOverride, foco e caret preservados, todas as transições, controle de microfone, desmonte/switch full-page/Dock, funções v1, no auto-submit, UI acessível, sem conteúdo/logs pessoais.
- Real E2E pt-BR com mic e provider legítimo, **transcrição parcial observada antes do stop** com timestamp medido, final concordante, inserção no meio durante fala, seleção/substituição, edição manual enquanto partial chega, stop/resume, queda de rede, duração máxima e feedback de falha.
- Full-page e **Dock real autenticado do Portal**; mobile, reduced motion, screen reader real quando ambiente suportar (`TEST_NOT_RUN` honesto caso contrário).
- Regression: vitest full plugin-ui/delia, backend suites, typecheck, lint quando adotado, build, Module Federation, Playwright, STT v1, ConversationQueue, DraftRecovery, confirmation, Markdown B2, Activity/Evidence; nenhum teste histórico de SHA distinto vale como PASS automático.

**Resultados:** `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`. Falhas disparam rework bounded e nova regressão. Performance: registrar P50/P95 first partial, finalization e UI responsiveness sob amostras reais; **não inventar SLA sem decisão de produto**.

## 9. Stage 6 — Rework de QA, segurança e resultado

Loop finito de execução: detectar → reproduzir em teste RED → root cause/owner → minimal fix → GREEN → suites → live QA → documentar. Agrupar defeitos do mesmo root cause; evitar corrigir sintoma de backend no frontend. Gate de saída:
- nenhum bug crítico de perda de draft/caret, sobrescrita humana, áudio sem consentimento, vazamento ou auto-submit;
- partial real antes da conclusão comprovado no runtime, ou **FEATURE_BLOCKED** com fallback v1 preservado;
- regressões relevantes verdes no evaluated SHA;
- painéis de observabilidade sem áudio/transcripts sensíveis;
- zero blockers críticos de segurança, a11y e uso básico.

Após 2 reworks sem causa identificada, parar mudanças especulativas e emitir `INCONCLUSIVE/ARCHITECTURE_DECISION_REQUIRED`, com testes e observações; não fabricar aceite nem deploy.

## 10. Stage 7 — GitHub e deploy governado

1. Commits por fatia coerente após resultados factuais; atualizar doc 123, contrato incremental aprovado, evidências e ledger. Evitar múltiplas entradas § concorrentes; fazer fetch antes de editar ledger e preservar upstream. Commit/push fast-forward main (ou workflow canônico, nunca force).
2. Pre-deploy: verificar `origin/main`, SHA e diff, approvals/gates, rollback, flags **default OFF** para live, fallback v1 ON; segredos/provider configurados apenas via mecanismos aprovados e sem revelar valores.
3. Confirmar ambiente real SSH operador e caminho script; referência histórica `ssh operador@192.168.1.237` / `./infra/scripts/up-prod-sequential.sh --cpu --build ...`. Não presumir flags nem nomes dos serviços; inspecionar script e owner operacional.
4. Fazer deploy sequencial necessário (backend `delia-api`, depois `plugin-ui` e `delia`, gateway apenas se mudança aprovada/necessária), **sem rebuild Core/Keycloak por conveniência**. Deploy inicialmente com incremental desativado, smoke v1; ativar somente capability permitida e smoke incremental real autenticado.
5. Verificar SHA implantado, health, contracts, remoteEntry/federation, v1, sessão parcial real, edição concorrente, cancel, erros, security negatives, logs não sensíveis, full-page/Dock e mobile.
6. Se falha de segurança, perda de texto ou quebra de v1: desligar incremental pela flag/admission; se insuficiente, rollback pelo procedimento canônico, verificar restauração e documentar outcome. Não marcar deploy `PASS` sem smoke de comportamento real.
7. Evidência final: `DEPLOYED_SHA`, `PROVIDER_CONFIG_FINGERPRINT` não secreto, resultados tests/eval, screenshots/videos autorizados, P50/P95 observado, residuals, rollback status, ledger.

## 11. Definition of Done e critérios de aceite

| ID | Critério decisivo | Gate |
|---|---|---|
| DO-01 | Provider/adapter/contrato incremental legítimos demonstrados | MUST PASS antes do backend live |
| DO-02 | Parcial real observado durante fala e antes de finalizar | MUST PASS para chamar VD-F06 live |
| DO-03 | Digitar, cursor livre, seleção e inserção durante gravação | MUST PASS |
| DO-04 | STT não sobrescreve correções humanas, inclusive eventos tardios | MUST PASS |
| DO-05 | Stop/cancel/falha nunca causam perda de draft | MUST PASS |
| DO-06 | Manual submit, privacidade e AuthZ/admission | MUST PASS |
| DO-07 | Fallback v1 permanece funcional | MUST PASS |
| DO-08 | Full-page + Dock real + mobile | MUST PASS |
| DO-09 | Tests/eval/regressions em SHA e configuração reais | MUST PASS |
| DO-10 | Deploy, feature flags, smoke live, rollback readiness | MUST PASS |

Se STT incremental não for demonstrado, resultado honesto = `PARTIAL_COMPLETION_FEATURE_BLOCKED` (pode entregar contrato/UX preparada sob flag OFF e v1 funcionando), nunca `COMPLETE_LIVE`.

**Aprovação:** Product Owner aceita UX; owners de backend/security aprovam mudanças de contrato; coordenação decide CP/RQ e fase. A execução do Devin não se autoaceita.

## 12. Execução por Devin: ordem e checkpoints

**Checkpoint C0** — Reanchor + proof reuse + decisão streaming (ou bloqueio explícito).  
**C1** — Contrato incremental versionado + testes RED.  
**C2** — Backend adapter/transport + segurança + provider real, testes GREEN.  
**C3** — Núcleo de reconciliação com property/adversarial tests.  
**C4** — UI plugin-ui + DÉLIA wired + fallback v1.  
**C5** — E2E áudio real + full-page/Dock + a11y + safety + regressions.  
**C6** — Reworks bounded comprovados, reteste completo.  
**C7** — Docs, ledger, commit/push main, deploy flags OFF→admission ON, smoke, rollback readiness, final report.

Não passar checkpoint crítico com `PENDING`. Executar fatias independentes enquanto bloqueio de provider estiver sob investigação; **não** implementar streaming falso.

## 13. Relatório final obrigatório

```text
DÉLIA END-TO-END EXECUTION REPORT
TASK_ID=DELIA-VD-F06-PROGRESSIVE-DICTATION-END-TO-END-IMPLEMENT-TEST-REWORK-DEPLOY-01
BASE_HEAD=
FINAL_HEAD=
ORIGIN_MAIN=
PUSH_VERIFIED=
DEPLOYED_SHA=
CURRENT_PHASE=
CP_RQ=
CANONICAL_REANCHOR=
EXISTING_EQUIVALENT=
REUSE_DECISION=
STT_INCREMENTAL_SUPPORTED=
PROVIDER_ADAPTER_OWNER=
TRANSPORT_AND_SECURITY_CONTRACT=
CONTRACT_VERSION=
AUTHZ_ADMISSION=
FALLBACK_V1=
PARTIAL_BEFORE_STOP_LIVE_EVIDENCE=
SEGMENT_ID_SEQUENCE_REVISION=
EDIT_ANCHOR_RECONCILIATION=
HUMAN_EDITS_PRESERVED=
CARET_SELECTION_IME_UNDO=
NO_AUTO_SUBMIT=
PRIVACY_LOG_REVIEW=
PLUGIN_UI_COMPONENTS=
DELIA_INTEGRATION=
FULLPAGE_QA=
REAL_DOCK_QA=
MOBILE_QA=
SCREEN_READER_QA=
VD_L01_L16=
DO_01_DO_10=
BACKEND_TESTS=
PLUGIN_UI_VITEST=
DELIA_VITEST=
TYPECHECK_BUILD_FEDERATION=
PLAYWRIGHT=
REAL_STT_EVAL=
LATENCY_P50_P95=
SECURITY_NEGATIVES=
REWORKS_PERFORMED=
FILES_CHANGED=
COMMITS=
EVIDENCE_PATH=
LEDGER_UPDATED=
PRODUCTION_DEPLOYMENT=
HEALTH_AND_SMOKE=
ROLLBACK_TEST_OR_READINESS=
EXECUTION_DRIFT=
ARCHITECTURE_DECISION_REQUIRED=
RESIDUALS=
EXECUTION_STATUS=COMPLETE_LIVE|PARTIAL_COMPLETION_FEATURE_BLOCKED|INCONCLUSIVE|FAIL
REVIEW_RECOMMENDATION=ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE
```

**Regra de encerramento:** Devin deve implementar o máximo legitimamente possível, testar, corrigir e implantar quando gates passarem; reportar qualquer bloqueio normativo real. O plano não concede permissão para mudar provider/contrato/autoridade unilateralmente e não converte resultado parcial em sucesso.
