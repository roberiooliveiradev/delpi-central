# 170 — DÉLIA · Decisão explícita de direção de produto e plano fechado de implementação

**Data:** 2026-10-27. **Status:** PRODUCT_DIRECTION_APPROVED / IMPLEMENTATION_NOT_AUTHORIZED. **Origem:** aprovação explícita do usuário após avaliação docs 163–169. **HEAD de consulta inicial:** `31dabcf5f0cbeee054fda1602f12ca1b6527a528`. **Fase/CP/RQ:** não alterados. **Documento subordinado:** autoridades 16→50→17→49→51→52→21→20→25, arquitetura técnica, Product Spec e ledger em HEAD. Em conflito, STOP / ARCHITECTURE_DECISION_REQUIRED; não reconciliar silenciosamente.

## 1. Três decisões aprovadas (direção, não implementação)

**PD-1 — Independência de modelo:** arquitetura e contratos da DÉLIA não podem depender do `qwen2.5:3b` nem de um provider específico. O `delia-json`/3B continua baseline local de desenvolvimento e comparação, não requisito permanente de capacidade do produto. Troca de modelo, serviço externo, preço, hosting ou deploy exige gate e autorização próprios.

**PD-2 — Qualidade grounded com investigação e parciais explícitas:** a DÉLIA deve procurar evidência legítima, poder refinar consultas READ governadas quando houver progresso e comunicar incerteza, ausência de cobertura e resultados parciais sem converter modelo/tool output em FACT. Nunca fabricar registros, citar quantidade sem comprovação ou substituir Core/Domain authority. Recomendação != autorização; READ != WRITE; PREPARE != ACT.

**PD-3 — Simplificação de estágios semânticos redundantes:** reduzir encadeamentos LLM e duplicações somente após inventário, prova de equivalência e avaliação comparativa; reutilizar capacidades, portas, adapters, CRI, Evidence, Policy, Decision, Outcome e contratos existentes. Nenhum engine/planner paralelo, regex de negócio, branches de provider no planner ou mudança silenciosa de ownership. Preserve governança, budgets, auditabilidade, segurança e rollback.

## 2. Evidência que limita a decisão

- Doc 165 R1: iteração local engajou, sem melhora de Business Outcome.
- Doc 166 R1.5: erros de admission e baixa sensibilidade de julgamento com payload preservado; amostras localizadas.
- Doc 167 R1.6-A: B2 por registro elevou recall, mas apresentou FPR 0.214 e custo ~5,5x; não foi aprovado produtivamente.
- Doc 168 integrada: E0 9/32, E1 8/32, sem conversão; judgment/continuity gates falharam.
- Doc 169 CH-1/CH-2: ambos REWORK / NO_PROMOTION; catálogo e injeção falharam em CH-1; G1 não extraiu quantidades em CH-2; C0 9/32 vs C1 10/32 exploratório, sem evidência de ganho.
- Owner Domain API de busca: limitações de vocabulário são `NEEDS_OWNER_DECISION`, não autorização de busca paralela na DÉLIA.

**Não declarar a arquitetura-alvo PROVEN ou implementação pronta.**

## 3. Plano fechado — execução por gates, não novas explorações abertas

**P0 — Reancoragem e contrato de mudança (documental, bounded).** No SHA atual: HEAD/status; Project Instructions/.cursor; 16→50→17→49→51→52→21→20→25; arquitetura, Product Spec, temática, ledger; inventariar caminhos admission→goal→discovery/selection→invoke→evidence→relevance→continuation→Outcome e consumidores/contratos. Identificar CP/RQ, autoridade e fase. Para cada proposta `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`. Congelar baseline e corpus, incluindo negativos/catálogo/WRITE/identidade, e um orçamento experimental finito. **Gate P0:** matriz de responsibilities, mudanças candidatas, compatibilidade, testes e rollback. Sem produção.

**P1 — Simplificação candidata isolada (harness / branch experimental, sem produção).** Comparar ao CURRENT uma composição mínima que preserve catálogo, negativas, READ/WRITE e Core/Domain AuthZ, sem adotar automaticamente CH-1 ou CH-2 reprovadas. Reusar contratos e stages; eliminar/combinar somente duplicações demonstradas. Não propor stage novo de LLM para quantidade por default. Verificar schemas e model-facing payload. **Gate P1:** passes negativos e segurança, ausência de falsos positivos materiais, preservação catalog/write, custos controlados e melhoria mensurável nas tarefas relevantes; caso contrário REWORK/INCONCLUSIVE sem promoção.

**P2 — Evidência/continuidade com avaliação end-to-end.** Reusar recuperação governada, paginação real, identificadores e provenance; LLM escolhe semântica, determinístico valida contratos, AuthZ, budgets, cobertura e stop por limites. Confirmar pertinência vs suficiência, parciais declaradas, falsos positivos e output real. Avaliar mesmo corpus, mesmo modelo/config, holdout, negativos, tokens, latência e Outcome. Não assumir N chamadas por N registros. **Gate P2:** ganho real de Business Outcome sem regressões materiais e segurança exercitada; se não alcançar, classificar FAIL e explicar primeiro ponto divergente, sem implementação.

**P3 — Decisão única de implementação mínima.** Coordenador revisa resultados P0–P2 e aprova explicitamente um diff bounded com owners/contratos e CP/RQ identificados. Se falhar, conservar baseline e documentar decisão; não abrir sequência automática de prompts. Owner Domain API recebe questão de busca e contrato separadamente; não fazer mudança cruzada.

**P4 — Implementação somente após P3 explícito.** RED→menor diff→GREEN→regressões→avaliação local com modelo congelado→independent review→document/ledger→commit/push. Separar deploy/produção em autorização própria. Testes verdes não bastam: comprovar generalização, safety e task outcome no SHA/config. Feature flag/rollback quando cabível; respeitar PREPARE/ACT e autonomia C3/C6.

**P5 — Aceite de produção somente com aprovação independente:** AuthZ e Domain owner verdadeiros, auditoria, tracing, custo, segurança e Business Outcome observado; testes produtivos pagos/deploy apenas se autorizados. Resultado `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

## 4. Critérios de encerramento do plano

- Uma matriz única KEEP/SIMPLIFY/EXTEND/REMOVE_CANDIDATE, com owner/consumer/contrato e evidências.
- Baseline vs candidato congelados e métricas de Outcome, negativos, catálogo, identidade, coverage, custos, latência, segurança e holdout.
- Zero requisitos de modelo/vendor hardcoded; nenhuma nova autoridade ou engine duplicada.
- Cada gate possui decisão binária/qualificada e condição de parada; **não permitir otimização indefinida de prompts**.
- Entrega após P2: `IMPLEMENTATION_READY` somente com gates satisfatórios, ou `NO_PROMOTION` com causas comprovadas. Nenhuma implementação automática.

## 5. Limitações da reancoragem deste registro

Consulta feita à `main` e lidos diretamente o doc 163, o doc 169 e o ledger via GitHub; os resultados dos documentos 164–168 são conhecidos pelos relatórios/revisões anteriores. **Não se atesta aqui inspeção completa, no HEAD atual, de todas as autoridades, .cursor, arquitetura técnica e Product Spec, nem git status local.** P0 exige essa reancoragem antes de gerar prompt executivo ou modificar arquitetura/código. Este registro não altera documentos canônicos superiores, fase, contrato, runtime nem aprovação de implementação.
