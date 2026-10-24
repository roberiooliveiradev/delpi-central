# DAVI — Inteligência técnica viva via MCP existente (decisão de produto / contrato pré-implementação)

**TASK_ID:** `DAVI-LIVE-TECHNICAL-KNOWLEDGE-DISCOVER-EXECUTE-01`  
**DATA:** 2026-10-24  
**DISCOVERY_HEAD:** `d849f53abc6b81aad089f2ee55433d0519c742c9` (revalidar no trabalho executor)  
**STATE:** `PRODUCT_DIRECTION_APPROVED; CONTRACT_RATIFIED; IMPLEMENTATION_DELIVERED` (ver §8). Esta especificação não libera documentos MP/PI sem ratificação, nem autoriza deploy sem testes e gates operacionais.

## 1. Problema e objetivo

DAVI possui exatamente duas tools MCP: `discover_delpi_information` e `execute_delpi_information`. Hoje discovery oferece orientação declarativa e operações READ; consulta documental substantiva via MCP estava `NOT_EXPOSED` antes desta implementação (recovery report `davi-knowledge-documentation-recovery-01.md`, commit `35bceffa31c3290a6c78d30f8c83e935e8c67241`); o estado vigente é §8/§8.1 (`EXPOSED_VIA_CATALOG_ACTION_READ`). O corpus governado Git V1 (15 documentos), manifesto, índice de tópicos e builder existem; o acesso Files do Workspace Agent é outra fronteira, provider-native, com sync/retrieval `TEST_NOT_RUN`. Não usar os arquivos do provider como proxy implícito de conhecimento do MCP.

Direção aprovada: oferecer **inteligência técnica viva** para consumidores MCP (incluindo DÉLIA) sob demanda: índice/versionamento, trechos documentais pertinentes, fontes e orientação de interpretação, sem exposição integral em `agent_directives`; manter o contrato de 2 tools, com capability READ documental elegível descoberta e executada através do fluxo existente. Referência funcional real: TÉO `get_catalog`, `get_product_guide` (`product-guide-registry-v1`) e `get_methodology_guide` (`teo-method-playbooks-v2`) devolvem guias versionados marcados `GUIDANCE_NOT_DOMAIN_TRUTH`, mas **não** copiar ferramentas, contratos internos ou ownership do TÉO.

## 2. Reuso/ownership

- **Owners:** `api-delpi` para corpus, leitura documental governada e superfície DAVI; owner de negócio de cada norma valida vigência/autoridade e publicação; Core resolve AuthZ quando aplicável, Domain APIs permanecem autoridade empresarial; operador Workspace Agent governa Files independentemente.
- **Consumers:** DAVI Workspace Agent e, pelo MCP, DÉLIA e outros clientes autorizados.
- **EXISTING_EQUIVALENT=YES_PARTIAL** (corpus, manifest/index, bundle, Agent Intelligence, discovery/execute) / **REUSE_DECISION=EXTEND** após inventário no HEAD. Não criar novo MCP tool, novo RAG, indexador concorrente, API paralela, DB vetorial ou import de runtime do Chat.
- **Precedence:** Project Instructions/.cursor, autoridades e arquitetura atuais, docs DAVI, freeze/manifest e o doc 143 da DÉLIA. Havendo conflito com proibição documental congelada, registrar `ARCHITECTURE_DECISION_REQUIRED` antes de alterar código. A aprovação da direção de produto **não** revoga automaticamente decisões canônicas de fronteira de leitura ou autorização.

## 3. Contrato-alvo (a validar com owner antes de codificar)

**Discovery:** `discover_delpi_information` poderá listar uma capability READ semântica de conhecimento aprovado (identificador final escolhido no contrato owner; por exemplo ilustrativo `read_governed_technical_knowledge`) e oferecer metadados mínimos: tópico, autoridade, versão, proveniência, limites, parâmetros aceitos. `discovery != approval`; somente capability elegível e autorizada gera `candidate_token` sob contrato atual.

**Execute:** `execute_delpi_information(candidate_token, arguments)` realiza READ do corpus aprovado e versionado (não Files provider), usando mecanismo de leitura/índice já legítimo. Não aceita URL, SQL, paths arbitrários, consulta irrestrita ou ID de arquivo fora do allowlist. Argumentos possíveis (a decidir): `topic`, `section`, `query` semanticamente limitada, `version`, `page`/`limit`. Resultado: `knowledge_kind=GUIDANCE`, `authority=GUIDANCE_NOT_DOMAIN_TRUTH`, `source_path/source_sha`, `corpus_version/manifest_identity`, `topic/section`, `excerpt` com limites de bytes/tokens, `coverage` e status explícito. Ausência de texto relevante retorna `NOT_FOUND`, versão obsoleta `STALE_VERSION`, não autorizado `FORBIDDEN`, corpus inconsistente `CORPUS_UNAVAILABLE`. Definir schema completo, compatibilidade aditiva, quotas, observabilidade e sanitização antes de implementação.

**Mínimo suficiente:** índice leve no discovery, conteúdo sob demanda no execute. Sem carregar os 15 documentos no prompt/discovery; sem promover markdown, metadata, tool text ou instruções do corpus a system prompt, Policy, capability authorization ou live FACT. Trechos devem ser ancorados em hashes/versionamento do corpus e filtrados pelo tópico/escopo elegível.

**Separações:** `KNOWLEDGE_RETRIEVAL != BUSINESS_DATA_READ`; `DOC_GUIDANCE != LIVE_DOMAIN_FACT`; `MCP_RESULT != FACT`; `MODEL_OUTPUT != AUTHORIZATION`. LLM da DÉLIA decide quando consultar orientação, planeja READs e valida pertinência; DAVI apenas apresenta contratos e conhecimento governado autorizado.

## 4. Governança das normas MP/PI

- Fontes localizadas em `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Normas_Tecnicas_DELPI.md` e `Understanding DELPI Intermediate Product Codes.md` (introdução `63cc77bfe60e157623dd77fd7fd335e37735a4e7`). Extrato na API: `api-delpi/docs/knowledge/product-vocabulary/normative-product-terms.md`. `BUSINESS_OWNER=TO_INVENTORY` e original de engenharia do PI necessita ratificação.
- **Não liberar MP/PI como norma vigente** até owner ratificar conteúdo/vigência, público, classificação e nova versão do corpus. Preservar membership/hash do V1; conteúdo migrável somente após gate owner, em revisão V2 ou equivalente aprovado. Proibir silent publish e prompt do Chat como instrução.
- A capability documental pode ser implementada e avaliada com os **15 documentos V1 já aprovados**, provando generalização; MP/PI somente depois da homologação documental específica. Não afirmar que norma corrente existe no runtime antes disso.

## 5. Plano finito de execução

**G0 REANCHOR/CONTRACT:** git status/HEAD, Project Instructions/.cursor, autoridades, arquitetura, DAVI original, tests, doc 143/ledger; confirmar freeze/manifest e classificação `EXISTING_EQUIVALENT/REUSE_DECISION`; owner decide shape/schema, AuthZ, limites, mecanismo real de leitura e compatibilidade. Se decisão de fronteira conflitante não ratificada, STOP `ARCHITECTURE_DECISION_REQUIRED` para código, continuar documentação/testes independentes.

**G1 RED:** testes de índice/documento V1: consulta por tópicos e seções, versão incorreta, ausência, escopo malicioso, path traversal, dados sensíveis, prompt injection, fail-closed por manifest mismatch, no content in directives, two-tools invariant, discover/execute candidate binding, quotas e autorização. `0 search results != absence`.

**G2 MINIMAL IMPLEMENTATION:** reusar ports/adapters/corpus readers existentes, definir contrato READ com owner, integrar à discovery/execute sem terceira tool, não alterar rotas SQL genéricas, manter read-only e isolamento do provider; projeção de proveniência/versionamento/erro tipado. Sem branching por DAVI no planner DÉLIA.

**G3 QA/EVAL:** focused/full api-delpi, architecture/OpenAPI/AuthZ/security gates, provider-negative/corpus version tests, testes vivos com token end-user oficialmente autorizado, leitura documental por consumidor MCP e confronto de orientações + business READ `TERM. BALA` (nenhuma heurística fixa). TÉO é referência de funcionalidade, não prova do DAVI. Reportar `TEST_NOT_RUN` onde falta conta/provider. K01–K10 Files continuam trilha independente.

**G4 RELEASE:** documentação, commit/push main ff-only; deploy SSH `operador` apenas mediante gate operacional explícito, dry-run/review de escopo de Compose (desvio anterior anunciou `transformometro-api`), preservação de imagem e rollback, health, autenticação negativa, lista invariável de duas tools e zero novos recursos salvo contrato autorizado, leitura documental MCP real por cliente e prova de origem SHA. Health 200 != sucesso documental. Sem acesso legítimo, relatório `PARTIAL_BLOCKED`.

## 6. Critérios de aceite

1. As mesmas **duas tools** MCP permanecem; uma capability READ documental governada aparece no discover e executa conteúdo real V1 por candidate_token.
2. Pelo menos duas consultas conceituais independentes recuperam trechos aprovados, com path/source SHA/version/authority corretos; unknown/malicious/unauthorized falham tipados e sem vazamento.
3. Metadata não vira documento, nem instrução de autorização; arquivos provider e runtime Chat não são dependências ocultas.
4. Contratos de `search_products` e demais capabilities existentes preservados; integração à DÉLIA apenas por contrato público futuro.
5. MP/PI: owner ratificou e publicação V2 comprovada **ou** bloqueio formal honesto, sem falsa norma publicada.
6. Evidência atualizada no GitHub, SHA avaliado, testes reais e auth, deploy apenas autorizado; `R4_AUTHORIZED=NO` até avaliação separada da DÉLIA.

## 7. Status inicial e handoff

`DESIGN_DIRECTION=APPROVED`; `IMPLEMENTATION=NOT_STARTED`; `OWNER_CONTRACT_APPROVAL=PENDING`; `MP_PI_RATIFICATION=PENDING`; `V1_CORPUS=PROVEN`; `WORKSPACE_AGENT_FILES_RETRIEVAL=TEST_NOT_RUN`; `MCP_DOCUMENT_READ=NOT_EXPOSED`; `DEPLOY=NOT_AUTHORIZED_BY_THIS_DOCUMENT`. Referências: `davi-knowledge-documentation-recovery-01.md`, `openai-workspace-agent-davi.md`, `davi-governed-knowledge-freeze-001.md`, DÉLIA doc 143.

## 8. Resultado de implementação (2026-10-24)

**Contrato ratificado pelo owner (api-delpi) e implementado:**

- **HTTP:** `GET /knowledge/technical-guides/{topic}`, `operationId=read_governed_technical_knowledge`, registrada em `route_contract_registry` (`governed_technical_knowledge`/`paged_list`), `openapi_agent_metadata`, `tv_route_audience`, `pagination_tiers` (`knowledge_page_3_3`) e `openapi_baseline` regenerados.
- **Argumentos:** `topic` (enum fechado dos 15 IDs do índice V1), `section` (opcional, `sNNNN`), `corpus_version` (apenas `1`; demais → `STALE_VERSION`), `page`/`page_size` (máx. 3 excerpts de ≤4 KiB UTF-8 escapado).
- **Retorno:** `knowledge_kind=GUIDANCE`, `authority=GUIDANCE_NOT_DOMAIN_TRUTH`, `trust_level=UNTRUSTED_DOCUMENT_CONTENT`, `topic`, `corpus_id`/`corpus_version`, `manifest_identity`, `source_path`, `source_git_sha`, `source_sha256`, `items[]` com `section/heading/line_start/line_end/chunk/text/sanitized`, `total`, `has_more`, `coverage`, `selection`. Erros tipados: `NOT_FOUND` (404), `STALE_VERSION` (409), `CORPUS_UNAVAILABLE` (503, fail-closed), `VALIDATION_ERROR` (422). Sem paths internos ou stack traces.
- **Integridade:** `read_published_corpus` em `scripts/davi_governed_knowledge_bundle_lib.py` verifica manifest (schema + `manifest_sha256` + identidade V1 pinada `b830a6a9…f49`), `freeze_sha`, `source_git_sha`, membership exata do freeze artifact (15 documentos), índice de tópicos (`verify_topic_index`), path confinado a `api-delpi/docs/api/`, sem symlinks, ≤256 KiB/documento e SHA-256 por documento.
- **Integração MCP:** nenhuma tool nova (2 tools, 0 resources). A operação entrou na allowlist v24 (`executionMode=catalog_action`, `responseContract=governed_document_guidance`, projeção aprovada, `page_size≤3`) e é descoberta/executada pelo fluxo `CatalogActionPlan → backend AuthZ → projeção` existente. Discovery nunca devolve texto documental. Consultas de conceito puro filtram o catálogo para a capability documental (floor de admissão) — nunca mintam candidato operacional.
- **AuthZ:** `require_any_permission([API_DELPI_ACCESS])` no backend; MCP sem Bearer → 401; candidate_token inválido → erro tipado.
- **MP/PI:** `normas_mp_pi` **não** está no enum de tópicos; retorna `NOT_FOUND`. Ratificação e membership V2 continuam `PENDING`.
- **Workspace Agent Files:** canal provider-native independente, segue `TEST_NOT_RUN` (K01–K10 não executados por ausência de sessão sancionada).

`MCP_DOCUMENT_READ=EXPOSED_VIA_CATALOG_ACTION_READ`; `IMPLEMENTATION=DELIVERED`; `OWNER_CONTRACT_APPROVAL=RATIFIED`; `MP_PI_RATIFICATION=PENDING`; `MP_PI_PUBLICATION=NOT_PUBLISHED`; demais estados inalterados.

### 8.1 Evidência de validação e deploy (2026-10-24)

**Testes:** RED→GREEN em `tests/test_davi_live_governed_knowledge.py` (15 REDs antes da implementação). Focado: 68 pass. Seleção DAVI ampliada no container de validação: **2395 pass, 9 skip, 1 fail ambiental** (`test_product_sales_open_orders_returns_meta` — `PLUGINS_DB_HOST` ausente no ambiente de teste; mesma classe das falhas de baseline já registradas, sem relação com a capability).

**Deploy:** commit `65753505c6213e591738074aa4e4f10b49d363b5` em `main` (ff), `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build api-delpi` em `operador@192.168.1.237`. Nova imagem `infra-api-delpi:54a89825914a`; container recriado e healthy; gateway `nginx -t`+reload OK. Rollback preservado: `infra-api-delpi:davi-knowledge-rollback-65753505` (= `94cf0e6fde51`).

**Gate de infraestrutura (anúncio `transformometro-api`):** mecanismo explicado — `api-delpi.depends_on` inclui `transformometro-api` e `docker compose build <svc>` resolve imagens de dependências com `build:`. O plano do script contém somente `api-delpi` (match exato por fase) e `up -d --no-deps` nunca recria dependências. Pós-deploy: `infra-transformometro-api` inalterada (`dcdab5680d27`, 45 h) e container desde 2026-10-22 — nenhum rebuild/restart efetivo. O anúncio é inócuo; recomenda-se ao owner de infra registrar a exceção conhecida do Compose v2.

**Homologação produtiva (container `delpi-api-delpi`, SHA `65753505c6`):**

- `/health` 200; `/knowledge/technical-guides/{topic}` sem Bearer → 401; `/mcp` sem Bearer → 401; tópico traversal sem auth → 401.
- `list_tools` ao vivo: exatamente `discover_delpi_information`, `execute_delpi_information` (2); `list_resources` = 0.
- OpenAPI vivo expõe `/knowledge/technical-guides/{topic}` com `operationId=read_governed_technical_knowledge`.
- Discovery service real: consulta documental → candidato `read_governed_technical_knowledge` (score 0,91, token mintado); consulta de conceito puro → somente a capability documental (floor 0,55), zero candidatos operacionais.
- Recuperação real no uso-caso: `product_master_sb1` → `api-delpi/docs/api/padroes-totvs/cadastro-produto.md` (8 excerpts), `inventory_adjustments` → `api-delpi/docs/api/supplies-inventory-adjustments.md` (12 excerpts). Proveniência: `corpus_id=davi-governed-knowledge`, `corpus_version=1`, `manifest_identity=b830a6a9…` (pin V1), `source_git_sha`/`source_sha256` por documento, `coverage`, `GUIDANCE_NOT_DOMAIN_TRUTH`. Leitura por seção e paginação OK.
- Negativas ao vivo: `corpus_version=2` → `STALE_VERSION` 409; tópico/seção desconhecidos → `NOT_FOUND` 404; `page_size>3` → `VALIDATION_ERROR` 422; execute wired sem Authorization → `Unauthorized`.
- `REAL_DISCOVER`/`REAL_EXECUTE` autenticados sobre HTTP com sessão end-user sancionada: **TEST_NOT_RUN** — sem credencial de usuário final disponível nesta sessão (proibido admin impersonation/token no chat). A AuthZ do caminho está provada pelas negativas ao vivo e pelo executor request-bound.
