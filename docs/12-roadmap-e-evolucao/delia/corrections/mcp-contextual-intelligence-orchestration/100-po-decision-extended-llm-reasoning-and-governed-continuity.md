# 100 — PO DECISION: janela ampliada de inteligência LLM e continuidade governada

**Data:** 2026-10-22
**Origem:** decisão explícita do Product Owner após revisão da Etapa 6 e do doc 99.
**Status:** `PRODUCT_DIRECTION=APPROVED`; `IMPLEMENTATION=NOT_STARTED`; `CONTRACT_REDESIGN=ARCHITECTURE_DECISION_REQUIRED`; `PRODUCTION_ACTIVATION=BLOCKED` até gates. Este documento **não altera** os limites ativos e **não aprova deploy**.

## 1. Decisão aprovada pelo PO

1. **Ampliar o tempo disponível para o trabalho semântico do LLM para até 60 segundos por tentativa de raciocínio/decisão.** O teto anterior de 30 segundos por tentativa é insuficiente em casos operacionais complexos; a DÉLIA não deve confundir lentidão de seleção semântica com lentidão ou falha da API.
2. **Permitir continuidade governada em múltiplas tentativas dentro da mesma interação original, considerando até três tentativas**, em vez de exigir que o usuário repita a pergunta. O PO propõe três janelas de até 60 segundos para o raciocínio LLM; a forma exata de delimitar tentativa, estágio e interação precisa ser contratada. A soma **não é autorização automática** para deadline produtivo de 180s ou execução ilimitada.
3. **Comunicar a espera de maneira útil e transparente ao usuário.** Quando for necessário mais tempo ou uma segunda/terceira tentativa, emitir evento real e status user-facing do tipo `Ainda estou analisando sua solicitação e preciso de mais tempo para decidir como prosseguir`. A UI deve refletir estado real, sem gerar afirmação falsa de avanço ou recomeço. Nunca revelar chain-of-thought. Disponibilizar cancelamento já existente, com propagação real.
4. **Aprovar como direção B+D:** (B) preservar tempo para a execução operacional e a verificação autoritativa, separadamente do tempo de decisão do LLM; (D) encerrar honestamente quando não houver condição de continuar em segurança. A execução de MCP/Domain API, AuthZ, CRI e entrega exige orçamento próprio e métricas próprias; não deve ser sacrificada pelo consumo da janela de inferência.
5. **Modelo agnóstico:** o orçamento deve comportar modelos com diferentes tempos de inferência e manter interpretação/seleção semântica pelo LLM. Proibidos atalhos por regex, keywords, aliases de especialista, branches por provider, chamadas duplicadas ou aumento de autoridade.

## 2. Limites anteriores e novo direcionamento — nunca reconciliar silenciosamente

**Estado anterior documentado / atualmente implementado em dev:** `MAX_ATTEMPTS=2`, `TOTAL_BUDGET=60s`, `PER_ATTEMPT_BUDGET=30s`; produção retry OFF por gate de revogação de credencial delegada. A decisão PO **substitui a preferência de produto** quanto a número de tentativas e janela semântica, **mas não substitui automaticamente contratos técnicos ou segurança**. Portanto, abrir revisão formal das regras e interfaces de `TurnDeadline`, `ModelInvocation`, `OperationalCapabilityOrchestrator`, continuidade efêmera e NDJSON.

**Intent de produto para elaboração do novo contrato:** até **3 tentativas governadas** e até **60s de trabalho LLM por tentativa** com comunicação de continuidade. Definir explicitamente: se a quota LLM é acumulada por tentativa ou por chamada; como debitar estágio interrompido, cache/replay e custo; quanto reservar para discovery/AuthZ/invoke/postcondition/composição; qual deadline end-to-end de proteção; fronteiras entre 1ª/2ª/3ª tentativa; se uma tentativa de 60s LLM necessita tempo adicional operacional; duração de proxy/gateway/client e heartbeat; cancel/disconnect; latência e limites de cada provider; como se encerra ao atingir quota. **Valores globais definitivos e budgets operacionais = TO_DECIDE, não inferir 3×60 como runtime total.**

## 3. Comportamento esperado user-facing

- Ao iniciar: sinalizar processamento com etapas reais (`OBSERVE/CONTEXTUALIZE` conforme eventos).
- Enquanto o modelo permanece num estágio longo: progresso honesto, sem fake progress ou stream infinito; informar demora com mensagem/ActivityEvent tipado quando houver motivo real e suporte contratual.
- Ao esgotar a janela semântica de uma tentativa e iniciar tentativa autorizada seguinte: emitir `CONTINUING`/estado tipado real e mensagem amigável como `Preciso de mais tempo para analisar sua solicitação; vou continuar`. Não anunciar nova tentativa se retry bloqueado, budget global encerrado, usuário cancelou ou fronteira material iniciada.
- Se o usuário cancelar: sinal imediatamente impede novos trabalhos, respeitando limitações de chamadas em curso; terminal honesto, sem nova tentativa.
- Se não for possível prosseguir após orçamento/attempts: estado final claro sem mascarar timeout como `SOURCE_UNAVAILABLE`; não pedir repetição da pergunta quando a continuidade segura era possível.
- Painel Contexto: refletir tempos separados `model`, `operational`, `composition`, remanescente/grants, índice da tentativa e `timeout_source`, preservando privacidade, seleção por turno e contrato `observability` já implementado.

## 4. Gates de autoridade, segurança e reuso

- `EXISTING_EQUIVALENT=YES` para `TurnDeadline`, fluxo `attempt()`, `_RESUME_STATE` ContextVar, `ActivityPhase.CONTINUING`, ActivityEvent/NDJSON, cancelamento e `turn_observability`. `REUSE_DECISION=EXTEND` *condicional* após inventário completo; não criar segundo timeout engine, scheduler, fila, banco ou estado persistente.
- A continuidade permanece efêmera, no request/worker existente; perda após refresh/restart mantém o limite anterior até decisão específica.
- Revalidar autorização ao retomar. **Gate R4 ainda aberto:** `InMemoryDelegatedTokenCache` pode reutilizar token emitido antes de usuário ser desabilitado; contrato de revogação por tentativa exige decisão e testes negativos. `MAX_GOVERNED_ATTEMPTS` em produção permanece OFF até resolver.
- Proteção contra repetição de operações materiais: DISCOVERY/READ concluído pode usar replay dentro de invariantes de mesma interação/sujeito/args/autorização; PREPARE/ACT/unknown nunca reexecutar. Respeitar Core/Domain authority, confirmation, idempotency, audit e postcondition.
- Nenhum segredo, chain-of-thought ou conteúdo MCP não confiável entra em prompt/log/projeção.
- Ollama GPU para todas as avaliações locais de LLM real, sem chamadas externas pagas. Modelo produtivo externo somente tráfego de usuário real em produção.

## 5. Próximo fluxo de implementação — contrato antes de código

1. Reancorar HEAD, Project Instructions/.cursor e hierarquia 16→50→17→49→51→52→21→20→25, arquitetura, product spec, docs 88–100, ledger; confirmar owners, fases e CP/RQ.
2. Inventariar tempos reais e contratos existentes, incluindo prova de segregação LLM vs API (doc 99); caracterizar cenários 17,8s `select_capability`, estágios GPU, API lenta, modelo lento, streaming longo e cancelamento.
3. Produzir proposta de contrato com **janela semântica até 60s/tentativa**, até **3 tentativas**, reserva operacional adaptada a capability/timeout autoritativo, deadline global protetor fundamentado, resposta de progresso e regras de cancelamento/revogação. Incluir observabilidade/grants, errors, compatibilidade, testes e deploy; escalonar `ARCHITECTURE_DECISION_REQUIRED` para parâmetros ainda não aprovados. Não implementar valores não decididos.
4. Uma vez aprovado o contrato, implementar *menor diff nos owners canônicos*; RED/GREEN determinístico de budgets, interações reais locais Ollama GPU, multi-turn e MCP autenticado, sem duplicar PREPARE/ACT, testes de disconnect/heartbeat/proxy e wire sanitizado.
5. Validar UX de estados de análise/continuidade no plugin-ui, sem barra ornamental ou mensagens repetitivas; eventos reais por turno.
6. Publicar documentação e ledger de acordo com evidência, fazer review independente e somente então propor release/rollout produtivo autorizado; manter retry OFF enquanto gate de revogação estiver aberto.

## 6. Critérios de aceite futuros

- Decisões semânticas do LLM têm quota independente e documentada, executada por `TurnDeadline`/adapters existentes; tempo da API separado e protegido, sob envelope global seguro.
- Até três tentativas **somente quando autorizadas e tecnicamente elegíveis**, sem reinício indiscriminado, custos ocultos ou duplicação de side effects.
- Informação real de processamento/continuidade user-facing, cancelamento funciona e não expõe chain-of-thought.
- Evidência de limites por estágio/attempt, classificações de timeout e outcome correto; mesmo caso passa com modelos lentos sem alterar decisão semântica por regex.
- Gate de revogação, segurança, rede/proxy e release efetivamente satisfeitos antes de habilitar produção.

**DECISION_LOG:** `PO_APPROVED=60s_semantic_per_attempt+up_to_3_attempts+B+D+user_visible_continuity`; `END_TO_END_DEADLINE=TO_DECIDE`; `OPERATIONAL_RESERVE=TO_DECIDE`; `REVOCATION_POLICY=OPEN`; `CODE_CHANGE=NONE`; `RELEASE=NONE`.


## Adendo PO — priorização do residual de revogação (2026-10-22)

**PO_PRIORITY_DECISION:** não dedicar o próximo ciclo à remediação integral da revogação intra-turno do cache de credencial delegada; priorizar a funcionalidade de orçamentos semânticos, continuidade e experiência do usuário. O PO aceita manter o finding documentado para tratamento posterior. **Esta decisão não transforma o finding em PASS nem revoga os controles de segurança congelados.**

**RISK_ACCEPTANCE_SCOPE:** postergação de engenharia e priorização de roadmap; NÃO é autorização para ignorar autorização vigente, desabilitar Core/Domain AuthZ, aceitar token revogado, ou habilitar produção de múltiplas tentativas contra gate canônico ainda aberto. A hipótese de ocorrência rara não foi empiricamente quantificada; a janela de risco existe independentemente de sua frequência.

**RECOMMENDED_EXECUTION:** desenvolver e homologar a política de até 60s de decisão semântica por tentativa, até 3 tentativas governadas, progressos e cancelamento no ambiente dev/flag OFF em produção, reutilizando owners existentes; entregar avaliação de prontidão e isolar activation gate. Se o novo fluxo exigir ativação produtiva e o gate R4 continuar obrigatório, sinalizar ARCHITECTURE_DECISION_REQUIRED para uma decisão de risco/controle pelo owner competente, sem reconciliação silenciosa. A autenticação e a autorização final continuam backend-first/fail-closed e operações materiais não podem ser repetidas.

**STATUS:** `REVOCATION_REMEDIATION=DEFERRED_BY_PO`; `REVOCATION_RISK=OPEN`; `DEV_FUNCTIONAL_WORK=AUTHORIZED_WITH_EXISTING_GATES`; `PRODUCTION_RETRY_ACTIVATION=NOT_AUTHORIZED_BY_THIS_DECISION`.


> **SUPERSESSION / decisão PO de 2026-10-23:** [doc 103](./103-po-approved-llm-call-timeout-retry-and-global-five-minute-cap.md) prevalece sobre propostas anteriores conflitantes: **60s por chamada LLM real, até 3 tentativas por chamada lógica e teto global absoluto de 300s por solicitação**. Corte local genérico de 10s deve ser substituído na implementação; valores 60s de quota cumulativa por attempt, 90s attempt wall, 25s reserve e 150s streamed / 60s buffered do ADR 102 **não estão aprovados para implementação**. Reuso de owners existentes e B+D permanecem. Código ainda inalterado; next Task 2 implementação dev com testes e gates. R4 remediação postergada, risco aberto; nenhuma liberação de retry produtivo decorre deste adendo.
