# DÉLIA — Estado atual: flexibilidade semântica e eficiência de investigação

Data: 2026-11-06. Registro de coordenação; **não** é aceite de fase, autorização de deploy ou decisão de criar nova arquitetura. HEAD remoto observado na preparação: `21dedc76a61bb186dcf68be5545af1e8ef33240d` (pode avançar). Autoridades canônicas e ledger prevalecem em caso de divergência; reancorar antes da execução.

## Objetivo de produto

A DÉLIA deve resolver situações imprevistas com flexibilidade e eficiência: interpretar erros contratuais, reconsiderar argumentos/capabilities, reutilizar contexto e evidências, evitar trabalho sem progresso e encerrar com resultado empresarial fundamentado ou limitação honesta. Eficiência **não** equivale a limitar artificialmente o número de chamadas. Não criar planner, retry engine, registry, regras por owner ou memória paralelos. Priorizar recursos nativos Pydantic AI e capacidades existentes.

## Evidência existente e limites

- `DELIA-C3-PYDANTIC-AI-MCP-TYPED-TRANSPORT-TRACE-01`: B2 observou `params` como objeto/dict real; o registro anterior em string era artefato do harness. EVALUATED_SHA `e905fbd4aa`.
- `DELIA-C3-PYDANTIC-AI-B2-INVESTIGATION-PROGRESS-ROOT-CAUSE-01`: B2 registrou 8 tool calls, 3 classificadas úteis, 3 discovers DAVI de baixo rendimento, 1 HTTP 400, 2 chamadas analyze; recuperação posterior e resposta GROUNDED. Essa classificação vale **somente** para o B2 observado.
- `DELIA-C3-TEO-MCP-DISCOVERY-ANALYZE-CONTRACT-ROOT-CAUSE-01` e `DELIA-C3-TEO-ANALYZE-CONTRACT-CLARIFICATION-AND-B2-VALIDATION-01`: requisitos de escopo do TÉO comprovados; descrição de `analyze` omite exigência de `filial_id` + `setor_id` para `department`; proposta textual mínima documentada, `OWNER_APPROVAL=PENDING`; sem mudança contratual autorizada. Alegação de schema condicional 'unsupported' deve ser lida como não comprovado/suportado na cadeia atual, não impossibilidade do JSON Schema.
- `DELIA-C3-PYDANTIC-AI-NATIVE-MCP-ERROR-RECOVERY-REMEDIATION-01`: código revisado com Pydantic AI 2.50.0; ModelRetry para certas rejeições técnicas de argumentos, erro do owner projetado como tool result estruturado, recuperação 400 → sucesso no B2, dedup de chamadas exatamente equivalentes, AuthZ/Policy fail-closed. `NO_DEFECT_PROVEN`, `NO_FUNCTIONAL_CHANGE_REQUIRED`; commit `26509367864c64bb976329fabb9aac186d6e6bdb` alterou apenas ledger. Não confundir recuperação por tool result com ModelRetry.

## Estado de avaliação

- Recuperação no B2: **PASS** no caso observado; resposta classificada GROUNDED no relatório.
- Generalização comportamental multi-owner e casos inéditos: **INCONCLUSIVE**; nenhuma nova chamada real no último diagnóstico.
- Eficiência semântica, escolha inicial e encerramento oportuno: **TO_INVENTORY / PENDING EVAL**; B2 evidencia churn, não prova causa local nem melhoria.
- Alteração funcional na DÉLIA: **não autorizada sem defeito reproduzido**.
- Melhoria do contrato TÉO: **PENDING OWNER APPROVAL**, manter separada.
- Deploy produção: **NOT_AUTHORIZED**.

## Próximo passo bounded proposto (ainda não executado)

Realizar avaliação de generalização semântica e eficiência de investigação **sem alterar código inicialmente**, com perguntas inéditas, diferentes owners MCP existentes/autorizados e configurações/modelos fixados. Medir seleção da capability, validade dos argumentos, correção/replanejamento após erros, reuso de evidência, chamadas redundantes, latência/custo e Outcome empresarial com fontes. Classificar cada falha por boundary: modelo/descrição de capability/contexto/Pydantic AI/owner/governança. Não tratar HTTP 200 ou output do modelo como Outcome comprovado. Comparar ao B2 sem extrapolar seu denominador. Caso apareça deficiência reproduzível na DÉLIA, retornar à coordenação para decidir menor correção provider-neutral após EXISTING_EQUIVALENT e REUSE_DECISION.

## Reancoragem obrigatória para execução futura

HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática → ledger. Fase/NEXT são derivados do 16 + ledger no HEAD, não deste registro de coordenação.
