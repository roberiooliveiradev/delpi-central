# 210 — Plano vivo de correção: inteligência, interação e resposta da DÉLIA

- **Status:** PLANNED — plano de coordenação, não aceite de implementação.
- **Atualizado em:** 2026-10-29.
- **Escopo:** confiabilidade local da cadeia objetivo → contexto → admissão → discovery → seleção → argumentos → gates → execução owner → evidência → relevância → CRI → resposta → outcome.
- **Referências:** docs 187–209; docs 203–209 para incidentes causais; Execution Ledger; recursos de instrução v28; Task 16/17; último teste manual do usuário em produção.
- **Autoridade:** este documento é **plano temático vivo** e não substitui Document 16, autoridades 50/17/49/51/52/21/20/25, arquitetura técnica, especificação do produto ou o Execution Ledger. Fase/NEXT válidos exigem reancoragem no HEAD.
- **Local-first:** nenhuma mudança produtiva ou teste produtivo automatizado está autorizado por este plano. Deploy exige task e autorização separados.

## 1. Estado factual e riscos abertos

| Tema | Evidência | Classificação | Próxima prova |
|---|---|---|---|
| Product search owner | API-DELPI corrigida; DAVI consultado diretamente nesta revisão: códigos **10080683** = "TERMINAL PINO FEMEA 1,83MM 24-18AWG BRONZE DE FÓSFORO ESTANHADO - ROHS" e **10081935** = "TERMINAL PINO MACHO USINADO 16AWG COMP. 21,4MM S/ ISOLACAO GRANEL - WEIPU" | PROVEN para dados atuais consultados; não equivale a validação do turn produtivo | Replay com payload/contrato autorizado |
| Task 16 local E2E | 22 cenários reportados: 13 PASS / 1 PARTIAL / 8 FAIL; Qwen3 4B, LangGraph B1; 112 chamadas, 194.971 tokens; nenhuma fabricação observada | Evidência reportada, não generalização comprovada | Repetições e held-out |
| Task 17 v28 comparativo same-session | v27: 8/22 PASS, 7/12 foreign; v28: 10/22 PASS, 4/14 foreign; chamadas 120→144, tokens 193.029→236.231 | PROVEN contratual local; benefício geral e eficiência INCONCLUSIVE | Comparação multi-run e custos por stage |
| Task 18 release | v28 ativa em delia-api, LangGraph B1 / Kimi K3 / CRI preservados; doc 209 | DEPLOY_REPORTED_VERIFIED; smoke autenticado da task TEST_NOT_RUN | Avaliação funcional separada |
| Teste manual produtivo 2026-10-29 ~16:47–16:48 | "oi, délia liste 2 exemplos de terminal pino cadastrados"; DAVI execute_delpi_information; 4 consultas de fonte, 15 chamadas LLM, 32.042 tokens, ~86s; resposta "registros reais ... não correspondem ao que foi pedido" | **FAIL Business Outcome**; raiz TO_INVENTORY | Trace de candidatos, argumentos, records, relevância e recovery, sem novos calls produtivos |
| Playlist em Painéis TV | Resposta de incapacidade apesar de contexto visual; capacidade real de PREPARE/ACT não provada nessa sessão | TO_INVENTORY; nenhum write autorizado | Inventário do owner/capability e contrato PREPARE |
| Continuidade referencial, latest process, discovery-as-answer | Falhas estocásticas e divergências nos testes locais | OPEN / modelo vs contrato TO_INVENTORY por caso | Replays de multi-turn e estados |
| Operação local | Instabilidades WSL/RAM; falhas env-bound; migration V014 já aplicada deve ser imutável | Risco ambiental; owner específico para migração | Snapshot config/recursos e testes saneados |

Não confundir **fonte não pertinente**, **owner vazio**, **projeção vazia** ou **seleção errada**. Modelo/metadata não são FACT nem AuthZ. Resultados de negócio só podem ser aceitos com dados autoritativos e postcondition adequada.

## 2. Objetivo e decisão de arquitetura

A DÉLIA deve concluir objetivos autorizados com resposta relevante, grounded, contextual e rastreável, ou apresentar limitação exata. Preservar **LangGraph B1**, Engine A como fallback configurado, CRI, EvidenceFacts, ModelCallLedger, gates, políticas, Core AuthZ, Domain authority e owners MCP/A2A. Chat é somente inventário; nenhuma reutilização de runtime.

Antes de criar capability/port/adapter/engine/serviço: **EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY; REUSE_DECISION=REUSE|EXTEND|NEW**. Identificar responsabilidade, owner, fonte, consumers, contrato, implementação, teste e outcome. Fronteira existente `record_resolver` deve ser reutilizada quando pertinente. Não duplicar planner/evidence engine, nem aceitar heurísticas por palavras, nome de provider ou prompt específico.

## 3. Sequência bounded de correção (não são fases canônicas)

### A — Diagnóstico local e comparação causal (NEXT PROPOSTO)

1. Reancorar HEAD/git status/worktrees, project instructions/.cursor e autoridades na ordem canônica, doc 16 + ledger; inventariar runtime local exato (Qwen3 4B, LangGraph B1, instructions v28, todos os owners necessários). Não alterar ambiente produtivo.
2. Usar corpus existente de 22 cenários e acrescentar **held-out** para produto real, pedido implícito/explicito de MCP, context de Portal/Painéis TV, tarefas gerais sem owner, latest process, multi-turn, discovery/execute, PREPARE sem ACT, rejeição de irrelevância, ausência legítima.
3. Reconstruir falha "terminal pino" pelos logs sanitizados existentes e por **replay local**: identificar primeira divergência em discovery, candidato, argumento, execução, owner-result, relevância, recuperação e CRI. A consulta direta DAVI já confirmou dois códigos pertinentes; não assumir que esses foram os records do turn produtivo.
4. Medir baseline local por estágio: admissões, candidate selection, native_assessment, relevance, continuity, model calls e tokens. Controlar amostragem e separar infraestrutura de falha semântica.
5. Entregar mapa causal + `PROVEN|TO_INVENTORY`, testes RED para defeitos comprovados e decisão de reuse. Se evidência ausente, registrar `INCONCLUSIVE` em vez de redesenhar.

### B — Menor correção e testes de conformidade

- Corrigir apenas divergências `PROVEN` no owner/contrato legítimo; preservar authority, proveniência, classificação de vazios, limites e PREPARE/ACT.
- Avaliar primeiro mecanismos existentes de seleção, argumento, recuperação controlada, relevância, record_resolver, CRI e continuidade; extrações só quando boundary e consumers justificarem.
- Testar com replay determinístico RED/GREEN **e** modelo local real. Não introduzir novas bibliotecas por preferência.
- Playlist: descobrir legitimamente API/capability de programação TV e o contexto de rota; apenas simular/PREPARE, nunca criar playlist real em testes sem gates e autorização.
- Não alterar código por falsos positivos decorrentes de instabilidade WSL, tokens expirados ou ambientes incompletos.

### C — Avaliação comparativa de tecnologias e modelos, condicionada à causa

- Baseline LangGraph B1 + validação Pydantic/CRI/ModelCallLedger e contratos presentes.
- Se necessidade real e boundary permitirem, comparar em harness **eval-only** uma alternativa delimitada: LlamaIndex (síntese/evidência), Haystack (ranking/agregação), ou modelo local mais capaz; DSPy/PydanticAI só com hipótese nova, dado o resultado anterior.
- Mesmos cenários, contratos, dados, parâmetros e métricas. Medir contribuição causal, segurança, calls, tokens, latência, estabilidade e generalização com >=3 repetições quando recursos permitirem. Não concluir que modelo maior necessariamente funciona melhor.
- Não modificar arquitetura produtiva nem instalar ferramenta em runtime sem decisão documental explícita.

### D — Aceite local e gate de release separado

- Matriz por cenário: objetivo, capability autorizada, owner, args, evidência, relevance, resposta, outcome, custo e trace. Testes E2E locais autenticados contra owners disponíveis e fixtures para falhas.
- Critérios **propostos** (não autoridade de fase): >=90% de sucesso nos cenários elegíveis e corpus representativo, zero fabricações/violação de AuthZ/ACT indevido, continuidade correta, latência/tokens sem crescimento injustificado. Reportar confiança por repetições, regressões por classe e limitações legítimas.
- Se falhar gate: `REWORK|INCONCLUSIVE`; continuar local. Publicação em main somente de diffs testados, com ledger e docs; nenhum deploy implícito.
- Deploy produtivo futuro requer autorização separada, diff de release, rollback, smoke autenticado e business outcome demonstrado.

## 4. Regra permanente de manutenção

Ao concluir **cada task/review** desta trilha, reancorar e atualizar **este plano vivo** e o **Execution Ledger** na mesma entrega documental: data, HEAD base/final, task, hipótese/prova, ACCEPT/REWORK, cenários baseline/final, alterações, métricas, residual, próximo bounded step, owner e evidências. Proibido marcar `PASS` para trabalho não executado, avançar fase por documentação ou alterar decisões congeladas silenciosamente. Se nova evidência contrariar autoridade/decisão: `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`.

Registrar `LAST_VERIFIED_HEAD` em cada revisão (não confundir com runtime SHA); chat/handoff não substituem GitHub. Este plano é atualizado sob solicitação e durante tasks efetivamente executadas; **não implica monitoramento automático ou trabalho em background**.
