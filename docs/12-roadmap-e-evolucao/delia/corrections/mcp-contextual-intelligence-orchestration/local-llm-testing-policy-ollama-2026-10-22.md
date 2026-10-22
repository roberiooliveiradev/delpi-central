# DÉLIA — Política de testes locais com Ollama (decisão de produto, 2026-10-22)

**Decision:** LOCAL_LLM_TEST_PROVIDER=OLLAMA; EXTERNAL_PAID_LLM_IN_LOCAL_TESTS=PROHIBITED; EXTERNAL_LLM_USAGE=PRODUCTION_END_USER_ONLY.
**Status:** PRODUCT_DECISION_APPROVED; LOCAL_RUNTIME=TO_VERIFY; CONFIG_IMPLEMENTATION=NOT_STARTED. Esta decisão não constitui alteração de código, infraestrutura ou produção.

## Regra aprovada

Todos os testes locais da DÉLIA que requerem um modelo de linguagem verdadeiro usam **Ollama local**. Testes unitários e de contrato continuam preferencialmente determinísticos (fixtures/fakes) quando isso melhora reprodutibilidade. Nenhum teste local — unitário, integração, orquestração, MCP, recuperação de timeout, generalização, avaliação manual ou smoke — deve invocar LLM externo pago, mesmo como fallback. O LLM externo fica reservado para **utilização real por usuários na produção**, sob os contratos de governança e segurança já vigentes. Não assumir automaticamente equivalência de inteligência/qualidade entre modelos.

## Inventário inicial confirmado somente no código do GitHub

- `infra/docker-compose.dev.yml` possui serviço `ollama`, imagem `ollama/ollama:latest`, profile `optional-heavy`, container `delpi-ollama`, porta `11434`, volume `ollama_data`, limite de memória configurável (default `4500M`). Existência de serviço no YAML **não comprova que o container esteja iniciado** nem que haja modelo instalado.
- O ecossistema legada do Chat refere `OLLAMA_MODEL` default `qwen2.5:1.5b`, mas isso **não autoriza reutilizar seus serviços/runtime** na DÉLIA e não torna esse modelo automaticamente apto aos contratos tipados da DÉLIA.
- `delia-api` já possui `OpenAICompatibleModelInvocationAdapter` e `DELIA_LLM_PROVIDER`, `DELIA_LLM_BASE_URL`, `DELIA_LLM_MODEL`, `DELIA_LLM_API_KEY` como configuração provider-neutral. Testar o protocolo OpenAI-compatible do Ollama nesse adapter existente, sem duplicar provider ou importar nada do Chat.
- Hardware, GPU, RAM livre, endpoint acessível do container DÉLIA, modelos realmente baixados, outputs estruturados, latência e compliance com budgets 30s/60s: `TO_INVENTORY`.

## Guardrails para implementação posterior

1. Aplicar esta política no ambiente e pipeline de teste **sem alterar a configuração do LLM em produção**. Não copiar ou consultar chaves pagas nos testes. Sanear logs de configuração.
2. Bloquear explicitamente ou comprovar ausência de egress aos LLMs externos durante testes locais; qualquer endpoint/base_url externa no perfil local resulta em erro claro, sem fallback externo. Testar também configuração ausente, modelo Ollama offline e falha de schema estruturado.
3. Reusar a infraestrutura Ollama existente e o adapter DÉLIA; `EXISTING_EQUIVALENT=YES` para serviço compose e OpenAI-compatible adapter; `REUSE_DECISION=REUSE/EXTEND` somente onde houver gap contratual demonstrado.
4. Selecionar o menor modelo local que satisfaça os contratos de JSON/propostas tipadas, contexto e as avaliações necessárias **medindo no hardware real**. Modelos muito pequenos podem gerar falsos negativos semânticos; documentar model ID, quantização, resources, hardware, configuração, SHA, custo/latência e métricas. Não prometer que produção necessariamente passa porque Ollama passou.
5. Testes de segurança, idempotência, AuthZ, timeout, replay e recuperação precisam ser determinísticos sempre que possível; Ollama agrega integração real de protocolo e comportamento semântico. Falha ou ausência de Ollama = FAIL/TEST_NOT_RUN, jamais migração paga.
6. Testar MCP com autorização real de **desenvolvimento** quando disponível; Ollama só substitui o LLM, não a fonte factual, nem o Core/Domain gate.
7. Alterar instruções/CI/scripts de eval para assegurar a política, respeitando ownership e canonical reanchor; nunca alterar de forma oportunista jobs de produção. Se alguma autoridade canônica exigir LLM externo em homologação local, registrar conflito/EXECUTION_DRIFT e levar à coordenação; não reconciliar silenciosamente.

## Próximo passo bounded (não executado nesta decisão)

Inventariar `docker compose ps`, `ollama list`, rede, recursos, compatibilidade `/v1` no ambiente autorizado, e scripts de avaliação que hoje cobram tokens externos. Produzir decisão de modelo + configuração dev isolada + testes fail-closed + relatório com `EXISTING_EQUIVALENT` e `REUSE_DECISION`. Coordenar com CP5 em execução; não alterar seu ambiente simultaneamente sem evitar conflito de worktree/config.

**Evidence:** PRODUCT_DECISION=APPROVED; OLLAMA_COMPOSE_DECLARED=PROVEN_STATIC; OLLAMA_CONTAINER_RUNNING=TO_INVENTORY; LOCAL_MODEL_INSTALLED=TO_INVENTORY; DELIA_LOCAL_OLLAMA_VALIDATED=TEST_NOT_RUN; PRODUCTION_LLM_CONFIGURATION=UNCHANGED.
