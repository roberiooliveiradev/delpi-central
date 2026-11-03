# DÉLIA — Plano coordenado de consolidação semântica de respostas (Pydantic AI)

**Estado:** PLANNED — documentação de implementação, NÃO aceite de arquitetura executada.  
**Trilha:** C3 / apresentação de evidências e resposta contextual / sucessora de `DELIA-C3-PRESENTATION-BOUNDARY-UNIFIED-REMARK-REHYPE-01`.  
**TASK planejada:** `DELIA-C3-CRI-SEMANTIC-RESPONSE-CONTRACT-CONSOLIDATION-01`.  
**Owner de coordenação:** arquitetura/produto DÉLIA; **executor:** Devin (somente após reancoragem e gates).  
**Referência de investigação:** HEAD `d268cd05b06deb3584d3e84e436664a3f2c98a48` (revalidar obrigatoriamente ao executar); arquivos de aplicação e ledger consultados em main.  
**Objetivo:** simplificar a composição CRI para que a inteligência existente comunique o significado da resposta sem confundir cardinalidade de registros, dados de negócio e metadados técnicos; preservar segurança, evidência, performance, generalização e owners.

> **Hierarquia de autoridade.** Este plano NÃO suplanta Project Instructions/.cursor, documentos 16→50→17→49→51→52→21→20→25, arquitetura técnica, product spec, decisão congelada nem ledger. Fase/NEXT/CP-RQ DEVEM ser apurados no HEAD pelo executor. Em conflito, STOP → `ARCHITECTURE_DECISION_REQUIRED` ou `EXECUTION_DRIFT`, com evidência. Um plano persistido não adianta fase nem concede autorização para ACT.

## 1. Contexto e evidências

### 1.1 Reprodução empresarial (OBSERVED, fornecida pelo usuário)
- Consulta: `Qual a estrutura do 90260148?`. Evidence empresarial renderizada: raiz PA `90260148`, dois intermediários PI `50220013` e `50220015`, quatro ocorrências de MP (incluindo `10080031` duas vezes). A resposta anunciou `Encontrei 2 registros`. Esse número corresponde aos dois registros principais, NÃO ao tamanho completo da hierarquia e NÃO à quantidade de tools DAVI.
- Consulta `90260921`: raiz PA `90260921`, uma ocorrência MP `10020003`; texto `Encontrei este registro`. Ambos os casos provam que `single_found/records_found` não são comunicativamente universais.
- Exposição anterior de `Entity: product_structure`, `Shape: hierarchy`, `Root:`: mistura de metadados do envelope com conteúdo empresarial.
- A evidência dos exemplos vem de duas sessões reais reportadas no Portal; não equivale a uma avaliação generalizada no SHA futuro.

### 1.2 Inventário parcial confirmado no GitHub (PROVEN no momento da consulta)
- `delia-api/app/application/capability_provision/conversational_response.py`: `compose_cri_response()`, vocabulário `leads`, `field_labels`, `result_context`, contagens e render de evidências. Na revisão consultada, shapes de estrutura já usam `structure_found` quando disponível; NÃO reimplementar esse fix.
- `delia-api/app/application/capability_provision/orchestration.py`: coleta `EvidenceFacts`, `OutcomeVerdict`, `_compose_cri_response`, `_synthesize_content`, `_apply_outcome_assessment`; `_arggen_engine == "pydantic_ai"` invoca `propose_arguments` de infraestrutura para argumentos de capabilities.
- `delia-api/app/infrastructure/arggen/pydantic_arggen.py`: Pydantic AI `Agent` com output tipado derivado do JSON Schema, via provider/adapter; escopo EXCLUSIVO da geração de argumentos. `_validate_instance` continua a validação definitiva antes de uma capability. **Não tratar adapter de argumentos como adapter de respostas existente nem misturar prompts/credenciais.**
- Ledger da trilha T20: `DELIA-C3-PRESENTATION-BOUNDARY-UNIFIED-REMARK-REHYPE-01` reportada em `f899f24ebf`: `ConversationMarkdown` no plugin-ui passou de marked.lexer para unified + remark-parse + remark-gfm; `structure_found` e filtragem de chaves técnicas foram implementados; testes reportados GREEN; E2E empresarial da mudança PENDING; produção NÃO autorizada nessa task.
- Ledger também registra deploy produtivo anterior via VM `srv-api`; presença do procedimento NÃO implica permissão para a task futura.
- `remark/rehype` = sintaxe Markdown/renderização, NÃO decisão sobre significado/verdade; refatoração semântica pertence à aplicação DÉLIA, não ao frontend.
- `LangGraph` e a invocação de modelo estruturado existentes devem ser inventariados antes de qualquer nova stage.

### 1.3 Estado do inventário
`EXISTING_EQUIVALENT=TO_INVENTORY` **para o contrato tipado de intenção comunicativa**; existe infraestrutura parcial de saída estruturada com Pydantic AI em geração de argumentos, mas equivalência NÃO comprovada.  
`REUSE_DECISION=TO_INVENTORY` até leitura das fontes canônicas + contratos + consumers. Preferência condicional: `EXTEND` uma projeção/contrato ou stage existente; `NEW` só por necessidade comprovada de boundary/owner/consumer e com decisão aprovada.  
Estas declarações são portas de decisão, não exceções para criar engine antecipadamente.

## 2. Resultado-alvo e não objetivos

**TARGET:** a DÉLIA responde ao objetivo do usuário com referência semântica correta ao assunto e à evidência, sem usar `len(records)` como apresentação universal; preserva integralmente a representação determinística de dados autorizados, limitações, cobertura e provenance. O modelo pode sugerir *intenção comunicativa*; jamais reescrever fatos como autoridade, definir contagens ou autorização.

**NÃO implementar:** novo planner/segundo grafo, novo agente livre com acesso ao MCP, outro CRI paralelo, serviço/registry/engine/provider novo por conveniência, templates por DAVI/BOM/produto/endpoint, prompts com credenciais, inferência de permissões, migrations de Minha DELPI Chat, renderização HTML no backend, chamada extra ao LLM por default, reclassificação autônoma do Outcome, outputs do LLM como FACT.

**Boundary owners:**
- Keycloak: identidade; Core: AuthZ live; Domain API: regra/dado empresarial final; DAVI/MCP: interop não autoritativa; DÉLIA Evidence: dados/proveniência; DÉLIA Outcome: suficiência/cobertura; DÉLIA Application: semântica de comunicação + composição com evidência; DÉLIA Infrastructure: adapter de Pydantic AI se necessidade comprovada; plugin-ui: Markdown/visualização.
- Domain/Application não importam `pydantic_ai` nem SDK, HTTP, ORM, DB; tipagem portável em Pydantic puro somente se já autorizado pelos padrões existentes (ou tipos de domínio neutros). Framework restrito a Infrastructure.
- O conteúdo do modelo/tool/provider é UNTRUSTED DATA; somente evidence autorizada pode alimentar a resposta factual.

## 3. Arquitetura lógica e fluxo

```text
TURN / USER GOAL
   ↓
orquestração LLM + capabilities existentes (sem nova seleção duplicada)
   ↓
EvidenceFacts + OutcomeVerdict + limites/coverage/provenance
   ↓
REUSE de interpretação semântica existente, quando presente e válida
   ↓
contrato tipado mínimo de intenção comunicativa (PROPOSAL; não FACT)
   ↓
composição determinística: intro validada/fallback neutro + dados renderizados
   ↓
Markdown seguro existente → plugin-ui unified/remark
```

**FAST path:** evidência suficiente e semântica já conhecida → zero nova chamada de LLM.  
**OPERATIONAL path:** contexto, regras e formatação determinística → zero chamada dedicada se possível.  
**REASONING path:** se um modelo adicional for comprovadamente necessário, gate explícito de utilidade, orçamento, deadline, telemetria e fallback; não aprovar neste documento uma stage nova automaticamente.

### 3.1 Contrato conceitual (NÃO código aprovado)
Preferir reutilização dos tipos e projections existentes; se gap real, a proposta mínima deverá suportar:
- `communication_purpose` ou equivalente: orientação comunicativa abstrata (sem taxonomia infinita específica de domínio);
- `subject_ref`: referência resolvida por evidence/context autorizado, nunca código inventado;
- `evidence_refs`: referências de evidências efetivamente existentes;
- `introduction_proposal`: texto opcional, que não acrescente fatos não ancorados;
- `confidence/uncertainty` somente se contrato proprietário e avaliação justificarem uso; sem verdade inferida;
- `presentation_hint` abstrato, se já existir e for necessário, sem mecânicas de renderer;
- `limitations` e `coverage` provenientes de Evidence/Outcome, não do output do LLM.

**Separação invariável:** `interpretation != fact`; `count != meaning`; `owner pagination != presentation omission`; `read != write`; `semantic hint != permission`.

### 3.2 Regras determinísticas da composição
1. Se houver Evidence/Outcome válidos, transmitir fatos aprovados e não reinventar raízes/quantidades/unidades.
2. Título/introduction: usar interpretação ancorada no objetivo ou forma neutra `Resultado da consulta:` se semântica não comprovada; jamais usar `single_found/records_found` como fallback universal.
3. Contagens tipadas: distinguir `top_level_records`, `nested_occurrences`, `distinct_business_entities`, `owner_total`, `returned_count`, `presented_count`. Não introduzir todas como campos novos se já houver contrato; qualquer número exibido deve apontar para sua fonte e unidade de contagem. Não deduplicar ocorrências repetidas para apresentação.
4. Envelope técnico `entity/shape/pagination` é contexto do contrato: não apresentá-lo como fato empresarial; preservar `root` e demais valores de negócio autorizados.
5. Parcialidade: preservar `limitations` originais, `MAX_RENDER_LIST_ITEMS` e limites de segurança, paginação do owner e omissões técnicas separadas. Nunca silenciosamente truncar.
6. Falha de saída estruturada/timeout/provider → fallback determinístico seguro, sem perder evidência.
7. Não inserir selectores de produto, owner, MCP action, tipo de SKU, texto exato da pergunta ou código `90260148` como heurística.

## 4. Coordenação de implementação por gates

### G0 — Reancoragem e delimitação (PENDING)
No worktree isolado e com `git status` limpo: HEAD/origin/main; Project Instructions/.cursor; documentos 16→50→17→49→51→52→21→20→25; arquitetura técnica; product spec; specs CRI/Pydantic/Presentation; ledger e último SHA aprovado. Comparar commits da task unified/remark, evolução do CRI e mudanças concorrentes. Inventariar CP/RQ exatos e fase sem inventar IDs; registrar dependências e decisões congeladas. STOP em conflito.

**Saída:** matriz owner → fonte → consumidor → contrato → implementação → teste → outcome; arquivos/consumers; HEAD e limites.

### G1 — Inventário profundo + reuse gate (PENDING)
Mapear sem suposições: goal interpretation, semantic proposal/stage, Pydantic AI adapter (argumentos), model invocation, structured-output schema, CRI leads/vocabulary, evidence projection, coverage/counting, formatter, synthesis path, renderer, front consumers, testes/evals; localizar todo fallback e caminhos de apresentação concorrentes. Verificar `0 results != ausência` com inspeção residual de imports/calls. Classificar por função `KEEP | EXTEND | MOVE | REMOVE` (sem remoção antecipada).

**Saída:** `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`; `REUSE_DECISION=REUSE|EXTEND|NEW`; prova das fontes e das diferenças; matriz de diffs mínima. Se NEW, requer decisão arquitetural explícita antes da implementação.

### G2 — Contrato e tests RED (PENDING)
Definir contrato de comunicação **antes** do código: owner/consumers, proposta vs fato, input/output, errors/timeout, reference resolution, validação, compatibilidade de CRI e frontend, telemetria, indicadores de cobertura/contagem, fallback e boundary de segurança. Evitar schemas excessivamente enumerados que amarrem a inteligência a tipos de negócio. Adotar Pydantic AI somente no adapter de infraestrutura se houver chamada tipada inevitável; não assumir agent novo. Criar RED testes que exponham os defeitos e controlem regressão, sem hardcode por códigos.

**Saída:** contrato documentado, RED reproduzível, testes de invariantes e contrato de fallback.

### G3 — Implementação limitada (PENDING)
- Reutilizar/estender interpretação existente no mesmo fluxo da DÉLIA; preferir carregar a intenção comunicativa da primeira inferência de goal, não uma nona/décima chamada.
- Se Pydantic AI necessário, manter runtime no adapter infrastructural existente/adequado com dependência bounded, provider-neutral pelo boundary, sem reaproveitar prompt de geração de argumentos para resposta.
- Compositor CRI lê interpretação tipada e Evidence/Outcome; elimina `single_found/records_found` como regra universal, mantém vocabulário para avisos e fallback legítimos. Excluir redundâncias comprovadas sem modificar renderer fora do contrato.
- Preservar `structure_found` e sanitização técnica já entregues por unified/remark; só estender onde houver defeito comprovado.
- Nenhum novo MCP, provider, planner, engine, workflow, registry, serviço, DB, API ou JS SDK no backend Domain/Application.

**Saída:** menor diff correto, sem branches de domínio, sem APIs paralelas.

### G4 — GREEN, regressão e generalização (PENDING)
**Casos fixos de caracterização:** `90260148` (1 raiz, 2 PI, 4 ocorrências MP, incluindo MP repetida) e `90260921` (1 raiz, 1 MP); ambos sem frase universal de cardinalidade. Buscar convenções de resultado `plain collection`, objeto, hierarquia, listagem paginada, zero lines, leitura parcial, insuficiente, falha, dados contraditórios, bytes/campos longos, unknown/new owner.
**Generalization holdout:** pelo menos três casos empresariais com shapes/owners distintos NÃO usados para ajustar seletor ou prompt e com outcomes avaliados; registrar owner autorizado, SHA/config/model/seed quando aplicável; se não houver acesso, `TEST_NOT_RUN`/residual.
**Security:** malicious prompts em `description`, metadata de MCP, `semantic_hints`, JSON de owner, links/Markdown hostis; testes negativos de AuthZ e ausência de vazamento; nenhum campo técnico governante vira instruction.
**Performance:** baseline contra SHA pré-mudança em mesmo workload/model/provider: número de chamadas LLM por turno, input/output tokens (quando medíveis), latência end-to-end e por stage, timeout/fallback, custo se disponível. Gate: sem nova chamada por default; se custo adicional, demonstrar ganho de task outcome e decisão superior.
**Regressão:** tests CRI, outcome, evidence, orchestration, pydantic arggen, plugin-ui, tsc/build/federation conforme diff; código verde não comprova business outcome.
**Saída:** GREEN e matriz PASS/FAIL/PENDING/INCONCLUSIVE, logs/correlation IDs sem secrets.

### G5 — Local oficial + E2E empresarial (PENDING)
Atualizar deploy-wt versionado e serviços oficiais locais sem alterar trabalho concorrente; verificar Gateway alias `delia-api`, Keycloak/Core AuthZ, Portal, runtime SHA, model/provider e renderer ativo. E2E real para os dois produtos e pelo menos um outro owner aprovado. Usar sessão humana de forma legítima ou conta técnica com roles governadas; não pedir senha pessoal no chat, não reprovisionar conta humana. Comparar retorno owner vs texto final, completude/semântica/contagens/limitações. Capturar evidência visual quando aplicável. Sem credencial legítima, marcar `TEST_NOT_RUN` e não afirmar PASS.

### G6 — Review, documentação e promoção (PENDING)
Review independente: `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`; preservar resultados do G0–G5 em docs/ledger; atualizar matriz de ownership, decisão e handoff; commit e push main com controle de concorrência. **Produção não está autorizada por este plano**. Apenas task separada com gate local/segurança/outcome, procedimento canônico de srv-api, rollback e autorização de promoção.

## 5. Matriz de rastreabilidade e provas

| Requirement | Owner | Evidência mínima | Gate |
|---|---|---|---|
| Intenção comunicativa contextual | Orquestração DÉLIA | Consome goal já existente, nenhuma nova decisão concorrente | G1–G4 |
| Fatos/valores inalterados | Evidence / Domain authority | Diff do payload owner vs render | G2–G5 |
| Contagens tipadas | Evidence / compositor | sem `records_found` para hierarquia e sem perda de repetição | G2–G5 |
| Pydantic AI bounded | Infrastructure | imports/adapter e testes de falha/timeout/provider | G1–G4 |
| Presentation contract | DÉLIA Application | typed output + ref validation + backward compatibility | G2–G5 |
| Metadata isolada | Presentation boundary | `entity/shape` não expostos; `root` mantido | G2–G5 |
| Markdown seguro | plugin-ui | teste mdast/render, XSS/links, MFE build | G4–G5 |
| Fallback honesto | Compositor | output inválido, sem evidence, zero/partial | G2–G5 |
| Latência/tokens | Model invocation/telemetry | comparação baseline e SHA avaliados | G4–G5 |
| Autorização | Core/Domain | AuthZ live + ausência de bypass | G4–G5 |
| Outcome real | DÉLIA Outcome | E2E Portal e dados autoritativos | G5 |
| Ledger/release | Coordenação | SHA, resultado, decisão, residual, próximo bounded step | G6 |

## 6. Contratos de falha e blockers

- `MODEL_OUTPUT_INVALID` → sem interpretação utilizável; fallback factual e neutro; observabilidade.
- `MODEL_TIMEOUT` / provider 5xx/402 → respeitar deadline global; não repetir chamada sem governança; fallback.
- `MCP_DISCOVERY_EMPTY` ≠ dado inexistente. `MCP_RESULT` ≠ FACT automaticamente.
- `AUTHZ_DENIED` → não exibir dado empresarial; não contornar ou usar conta humana sem autorização.
- `EVIDENCE_INSUFFICIENT` → resposta explicita insuficiência; não preencher lacunas por LLM.
- `PRESENTATION_PARTIAL` vs `OWNER_PAGINATED` → causas e avisos distintos.
- `FRAMEWORK_MISMATCH` → manter contrato e escolher adapter conforme runtime real; sem import SDK em Domain/Application.
- `ARCHITECTURE_DECISION_REQUIRED` / `EXECUTION_DRIFT` → STOP, reportar conflito, não redesenhar silenciosamente.

## 7. Handoff obrigatório ao executor

**Escopo fixo:** simplificação da semântica CRI pela interpretação estruturada existente, usando Pydantic AI apenas quando houver capacidade/adapter/necessidade demonstrados, sem novo planner.  
**SHA de leitura:** `d268cd05b06deb3584d3e84e436664a3f2c98a48`; obter HEAD atual e ledger atualizado.  
**Dependência:** task unified/remark `f899f24ebf` já reportada no ledger; reavaliar aceite/revisão independente antes de mexer nas superfícies.  
**Arquivos iniciais:** `delia-api/app/application/capability_provision/{conversational_response,orchestration,outcome_assessment,generic_evidence_renderer}.py`; `delia-api/app/infrastructure/arggen/pydantic_arggen.py`; testes associados, vocabulary governado, contracts e plugin-ui Markdown. Não presumir localização de novos arquivos.  
**Evidências prioritárias:** estrutura `90260148`, `90260921`, ledger T20, baseline LLM/tokens e resposta real no Portal.  
**Execução:** um gate por vez, commits pequenos, menor diff, green+generalization+safety+business outcome, residual search, ledger atualizado **após** evidência, push main; sem touch em worktrees de terceiros, sem force-push.  
**Report final:**
```text
TASK_ID=
BASE_HEAD=
FINAL_SHA=
ORIGIN_MAIN=
PUSH_VERIFIED=
AUTHORITIES_REVALIDATED=
PHASE_CP_RQ=
EXISTING_EQUIVALENT=
REUSE_DECISION=
CONTRACT_OWNER_CONSUMERS=
MODEL_STAGE_REUSED=
PYDANTIC_AI_ADAPTER_DECISION=
EXTRA_LLM_CALLS=
CRI_RULES_REMOVED_OR_RETAINED=
EVIDENCE_OUTCOME_INVARIANTS=
TESTS_RED_GREEN=
GENERALIZATION_HOLDOUT=
SECURITY_NEGATIVE_TESTS=
BASELINE_VS_ACTUAL_LATENCY_TOKENS=
LOCAL_OFFICIAL_RUNTIME_SHA=
REAL_E2E_90260148=
REAL_E2E_90260921=
REAL_E2E_OTHER_OWNER=
BUSINESS_OUTCOME=
DOCS_UPDATED=
LEDGER_UPDATED=
FILES_CHANGED=
WORKSPACE_STATE=
DRIFT_RESIDUALS=
PRODUCTION_DEPLOY=NOT_AUTHORIZED
REVIEW_VERDICT=PENDING_INDEPENDENT_REVIEW
```

## 8. Coordenação: sequência autorizável

1. **Agora:** registrar este plano como `PLANNED`, sem avançar fase.
2. **Antes da implementação:** revisão independente da entrega unified/remark `f899f24ebf` e confirmação da fase/NEXT no 16+ledger atual.
3. **Task única bounded:** G0→G6 com verificação explícita de reuse e contrato; o executor não inventa novos owners.
4. **Após execução:** review de generalization/security/business outcome e decisão de aceite.
5. **Só depois:** eventual promoção em task separada e gates produtivos.

**Critério de conclusão:** clareza comunicativa contextual em dados novos, evidência fiel, nenhuma autoridade duplicada, sem regressão de segurança e sem custo de LLM adicional injustificado. **Documentação ≠ implementação; unit tests ≠ E2E; HTTP 200 ≠ Outcome.**
