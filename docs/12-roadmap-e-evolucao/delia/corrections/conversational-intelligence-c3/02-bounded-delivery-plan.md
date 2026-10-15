# 02 — Plano das seis entregas bounded

**Status:** PLANNED (sequência candidata aceita como direção de trabalho, NÃO autoriza execução).  
**Umbrella:** DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01.  
**Regra:** uma etapa por entrega e review, sem “um prompt corrige tudo”; implementação só após reanchor e autorização; nenhum novo planner/agent/engine por conveniência.

## Resultado esperado

Uma única DÉLIA que entende o pedido, descobre capacidades autorizadas, verifica conhecimento e dados do owner, resolve o que é resolúvel, pergunta só o essencial, comunica inferências como inferências e entrega respostas úteis, naturais, fundamentadas e governadas. Não é objetivo tornar o LLM fonte de dados empresariais ou autoridade de execução.

## Etapa 01 — Baseline factual e harness de eval

**Problema:** não há baseline único reproduzível dos defeitos de intenção, orientação, argumentos e síntese no mesmo SHA/config.  
**Ação candidata:** inventariar instruções realmente enviadas ao modelo e caminhos de fallback; reproduzir casos de TÉO sem mutação e owners fake, com logs redigidos, traces e expected outcomes; mapear CP/RQ/AC reais à matriz 25/20; reutilizar harness existente.  
**Entrega:** relatório por falha com stage/call contract/expected/actual/root cause PROVEN ou TO_INVENTORY; conjunto de testes baseline; thresholds só depois da medição.  
**Gate:** não iniciar refactor sem distinguir falha de intent, selection, discovery, schema, evidence, response e apresentação. **Sem ACT real.**

## Etapa 02 — Intenção, finalidade e instruções bounded

**Problema:** goal e prompts por etapa podem estar tecnicamente válidos sem reconhecer instruir vs consultar vs analisar vs preparar.  
**Ação candidata:** melhorar _understand_goal e instruções ativas existentes, não criar prompt por MCP, sem quebrar structured output, lineage ou security rules; conferir contratos/fallback e uso do mesmo objetivo entre estágios.  
**Entrega:** instrução e contrato versionados com testes para orientar, investigar, comparar, resumir, criar/modificar, ambiguidade, multi-turn.  
**Gate:** nenhuma regressão de seleção/autorização; custo/latência/tokens e generalização mensurados; nenhum novo intent vira autorização.

## Etapa 03 — Discovery e guidance provider-neutral

**Problema:** capabilities que explicam “como fazer” podem não ser escolhidas ou contextualizadas quando o usuário deseja orientação.  
**Ação candidata:** reutilizar selection/discovery/projection e knowledge owner já disponíveis; verificar contratos de guidance no live surface, recuperar somente contexto suficiente, preservar diferenças de capacidades entre providers; tratar guidance como informação não autoritativa.  
**Entrega:** fluxos de orientação com guidance disponível/ausente e tool rename invariance; sem catálogo local, sem lógica if provider.  
**Gate:** sucesso em TÉO/VISTA e fake owner não equivalente; nenhum incremento de AuthZ ou confiança no tool metadata.

## Etapa 04 — Completude, resolução e diálogo mínimo

**Problema:** schema externo válido não garante mudanças internas completas; esclarecimentos genéricos e resolver parcial causam interação pobre ou erro tardio.  
**Ação candidata:** revisar _build_arguments, _resolve_missing_inputs, _clarification_question e PREPARE gating; consumir contratos owner legítimos sem copiar validação/regra de domínio; classificar valor expresso, evidência recuperada, default declarado, proposta inferida e decisão humana requerida.  
**Entrega:** cenários com mudanças aninhadas, enums, defaults existentes/ausentes, ambiguidade, replanejamento e perguntas em linguagem de negócio.  
**Gate:** nunca autoaplicar inferência como dado/default, nem ACT com pré-condição desconhecida; política de confirmação owner + DÉLIA preservada; nenhuma correção TÉO-only.

## Etapa 05 — Resposta fundamentada, conversa e personalidade

**Problema:** selecionar campos/formatar frases não garante que a resposta satisfaça a pergunta; personalidade documentada não foi provada no runtime.  
**Ação candidata:** evoluir _synthesize_content / render/presentation nos contratos já existentes, verificando suficiência, ordenação, comparabilidade e limites; conectar baseline personality/02 com instruções/composição legítimas e preferência temporária, sem criar memory/prompt engine.  
**Entrega:** respostas naturais e específicas, com fonte/limites; multi-turn, estilo e correção sem prosa livre inventada.  
**Gate:** manter MODEL_AUTHORED_FACTUAL_PROSE=NONE até uma decisão arquitetural explícita; UNKNOWN continua UNKNOWN; nenhum claim de fato/outcome não verificado.

## Etapa 06 — Generalização, segurança e aceite independente

**Problema:** sucesso em uma tool ou exemplos de treino não comprova comportamento genérico.  
**Ação candidata:** executar matrizes L1–L9 conforme risco (20) e PERS-AC-01..31 aplicáveis, com holdout, falsos owners, mudanças de nomes/schemas, negativos de injection/AuthZ/PREPARE/ACT e validação de resultado no source.  
**Entrega:** execution report por SHA/config/modelo/policy/dataset e verdict independente ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE.  
**Gate:** sem declaração de PASS ou fim de C3 sem evidence e review; produção exige autorização/deploy/validação separados.

## Política de orçamento e número de instruções (não criar prompts infinitos)

- Reutilizar os instruction IDs/ports/stages já existentes. Regra padrão: **zero novos prompts para cada provider ou entidade**; qualquer novo instruction ID depende de equivalente inventariado NO e Abstraction Gate.
- Não criar um “superprompt” que replique todos os owners e esquemas; carregamento de contexto relevante por discovery/owner no momento necessário. Não assumir tool descriptions como instructions system.
- Preservar inicialmente bounds existentes: MAX_OPERATIONAL_PLAN_STEPS=3, MAX_REPLAN_ROUNDS=1, MAX_SURFACE_CHARS=6000, MAX_ARGUMENTS_BLOCK_CHARS=14000. Alterações desses números exigem evidência de qualidade/custo/latência e review — estes limites não foram congelados como política nova.
- Medir por stage chamadas de modelo, custo, latência, truncation, taxa de esclarecimento desnecessário e task outcome. Definir limite superior mensurável do prompt/contexto total **na Etapa 01**, após inventário; não inventar um número agora.
- Critério de otimização: menor path suficiente (FAST determinístico; OPERATIONAL regras + contexto; REASONING somente investigação complexa), sem CoT exposta/persistida.

## Protocolo de cada entrega para Devin

1. Coordenação reancora HEAD/git status/authorities/ledger e identifica a etapa NEXT vigente; confirma objetivo bounded e owner.
2. Especialistas de AI e Backend mapeiam CP/RQ, consumers, instruction contracts, expected fields, Core/Domain gates e fixtures relevantes.
3. Provar EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY e REUSE_DECISION=REUSE|EXTEND|NEW; reusar por boundary. Qualquer ADR ou drift retorna à coordenação.
4. Aprovar prompt de implementação **somente para aquela etapa**; aplicar o menor diff; executar testes/evals com baseline e holdout.
5. Entregar report com base/final SHA, diffs, contract compatibility, reprodutores e regressões, resultados de segurança, limites e evidência de outcome; review independente.
6. Atualizar ledger canônico factual **após** testes/review. Só então refletir status nesta pasta e planejar o próximo prompt bounded.

Códigos de etapa aqui são rótulos documentais (01–06), não tarefas implementadas nem novas autoridades sobre 16/ledger.
