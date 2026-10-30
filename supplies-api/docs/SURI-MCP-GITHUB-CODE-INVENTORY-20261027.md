# SURI — Levantamento do código MCP no GitHub

**Data:** 2026-10-27  
**Status:** CODE_INVENTORY_PARTIAL / READ-ONLY — fontes diretas encontradas e lidas; ausência de execução de testes e acesso a produção.  
**Repositório:** `roberiooliveiradev/delpi-central`; baseline `main` observado na inspeção anterior: `486831a025bfad52694a5aa0a0711dffc2340f95`. Revalidar HEAD antes de execução.  
**Objetivo:** fundamentar SURI por evidência de código, não somente descrições de ferramentas.

## 1. Código encontrado

| Produto | Arquivos-base verificados diretamente | Evidência |
|---|---|---|
| TÉO | `transformometro-api/tm_app/interface/mcp/server.py` | `MCPServer`, tools tipadas, bridge, OAuth metadata, classes de operação |
| VISTA | `tv-dashboard-api/tv_app/interface/mcp/server.py` | `MCPServer`, Streamable HTTP, ferramentas e tratamento de erro |
| CLARA | `controllership-finance-api/controllership_finance_app/interface/mcp/server.py` | `MCPServer`, tool metadata, AuthZ no bridge |
| CLARA | `controllership-finance-api/controllership_finance_app/interface/mcp/asgi.py` | `streamable_http_app(..., stateless_http=True, json_response=True)`, mount |
| CLARA | `controllership-finance-api/controllership_finance_app/interface/mcp/tool_bridge.py` | `require_mcp_context`, `authorized_user`, `has_permission` e domínio próprio |
| DAVI | `api-delpi/app/interface/mcp/server.py` | ferramentas READ dinâmicas `discover`/`execute`, Pydantic |
| Shared | `shared/delpi_mcp/transport.py` | ASGI path normalization, lifespan, DNS-rebinding protection |
| Shared | `shared/delpi_mcp/identity.py` | snapshot de contexto autenticado e construção de request; sem validar JWT nem decidir RBAC |
| Shared | `shared/delpi_mcp/resource_contract.py` | OAuth / RFC 9728, `aud` exato, scopes, protected resource metadata |
| CLARA knowledge | `controllership-finance-api/controllership_finance_app/application/clara/corpus_ingestion.py` | inventário explícito de fontes, proveniência, hash, `citation_locator`, supersede |
| Supplies | `supplies-api/app/create_app.py` e `supplies-api/app/composition/root_composer.py` | Flask app factory, blueprints atuais e middleware auth |

### Evidência de histórico

Commits rastreados para localizar os paths:
- `4a084e527f7c1eb58aea62ee0f4cfcf08400d507`: centralização do ASGI transport `delpi_mcp`.
- `41fdcf65e1954fb3090d508d5f94c50f779524f3`: implementação CLARA MCP e corpus governado.
- `fc980bc9afae201e78af5b39453cd8dd1969b3c2`: boundary de inteligência VISTA.
- `d256e5cc6287fbae85c4261c25c2b806c0199fc4`: boundary de inteligência TÉO.
- `7c6164b38076436f5176bcf51160d12483c5111a`: orquestração de conhecimento DAVI.

**Importante:** histórico é ferramenta de discovery; a leitura de arquivos default branch fornece evidência de código atual consultado. A completude e os testes dependem do inventário integral.

## 2. Arquitetura real dos especialistas

TÉO, VISTA, CLARA e DAVI implementam MCP como interface do owner, em Python, sobre seus services/use cases. O `MCPServer` é construído no próprio serviço, com tool registration, branding e bridges locais. O pacote `shared/delpi_mcp` é deliberadamente infraestrutura: não cria serviço MCP genérico, não reinterpreta negócio, não integra diretamente bancos nem resolve autorização.

`shared/delpi_mcp/identity.py` usa contexto já estabelecido em `delpi_auth`, falha fechado sem usuário e não valida JWT nem interpreta permissions. `resource_contract.py` implementa metadata RFC 9728 e binding OAuth de audience e scope; `mcp:tools` é scope de transporte e **não é permissão de negócio**.

CLARA reutiliza `authorized_user`/`has_permission` e repositórios/use cases canônicos; o bridge não duplica regra. Sua camada de conhecimento mantém `source_id`, hash de conteúdo, origem/authority e locator por seção; documentos permitidos vêm de manifest explícito, e conteúdo alterado supersede a versão publicada anterior.

VISTA possui transporte Streamable HTTP e documentação de ferramentas que delegam ao dispatch canônico no mesmo processo, sem loop HTTP. **Adaptação importante para SURI:** como `supplies-api` é Flask, o padrão ASGI de CLARA/VISTA não pode ser copiado como se a BFF já fosse ASGI. É preciso decidir a composição Flask↔ASGI no gate de arquitetura sem migrar o framework da BFF.

## 3. Supplies-api atual: superfície de composição provada

`app/composition/root_composer.py` registra Flask blueprints:
- `health`, `me`, `analytics`;
- `purchase_requests`, `purchase_orders`, `deliveries`;
- `inventory`, `safety_stock`, `market_intelligence`;
- `suppliers`, `supplier_creation`, `supplier_enrichment`;
- `users`.

**PROVEN:** pontos de montagem dos blueprints no código. **NÃO PROVEN:** que todas as rotas estejam habilitadas/saudáveis em produção ou que cada uma seja apropriada ao MCP. Em especial, escrita no ERP depende dos gates atuais. O fato de `supplies-api` existir em Flask impede afirmar que um servidor MCP já está implementado nela; nenhum arquivo de interface MCP de Suprimentos foi inspecionado como existente.

## 4. Runbook canônico de onboarding

Arquivo lido: `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`.

Registra como padrão: Keycloak client dedicado `mcp-<domain>`, Authorization Code + PKCE S256, audience específica por recurso MCP, `mcp:tools` compartilhado sem mapper de audience de outro MCP, prova de token sanitizado, metadata protected resource e isolamento de audiences; não publicar secrets. Host/compose/gateway/Keycloak/deploy de **produção** devem ser verificados no ambiente de produção, e documento ou setup local não os substituem.

Essa referência deve ser revalidada contra a versão do código, esquema Keycloak e regra `.cursor/rules/openai-plugin-mcp-integration.mdc` antes da implementação.

## 5. Proposta de arquitetura SURI — não implementada

```text
ChatGPT / SURI
  → OAuth end-user Keycloak (cliente dedicado + audience específica)
  → MCP Streamable HTTP /apps/supplies-api/mcp [TARGET, não rota provada]
  → adapter MCP de Suprimentos (tool_bridge, branding, server, auth gate)
  → use cases / composição canônica supplies-api (Flask preservado)
  → Core effective permissions, unit/resource/ownership e owners externos via BFF
```

A decisão Flask↔ASGI permanece **TO_INVENTORY**: avaliar compatibilidade/isolamento do adapter e contratos HTTP ou invocação segura de application service, sem migrar `supplies-api` para FastAPI/Starlette e sem duplicar AuthZ. Não usar padrões internos da CLARA por import cross-context de domain/application.

Para a camada de conhecimento, **reutilizar o método** de corpus explícito, provenance, versão, citation, publish/supersede e access scope da CLARA; não compartilhar indiscriminadamente seu conteúdo ou banco, nem criar indexação sem owner/escopo. Para inteligência, começar com análises determinísticas de dados homologados que a BFF já fornece.

## 6. Decisões e evidências em aberto

| Item | Classificação |
|---|---|
| Quatro `server.py` encontrados e lidos | PROVEN — código |
| `delpi_mcp` shared transport/identity/resource contract | PROVEN — código |
| CLARA tool bridge e corpus ingestion | PROVEN — código |
| `supplies-api` Flask blueprint registration | PROVEN — código |
| Read-only live tools TÉO/VISTA/CLARA | PASS — catálogo na sessão anterior |
| Git local status / current HEAD runtime | TO_INVENTORY |
| Flask-ASGI composition segura | TO_INVENTORY |
| HTTP auth gate e suporte OpenAI Plugin para supplies | TO_INVENTORY |
| Rotas/endpoints, service/authz e cobertura dos testes por capacidade | TO_INVENTORY |
| Client Keycloak, audience, infraestrutura e deploy da SURI | PLANNED |
| Testes automatizados executados nesta rodada | TEST_NOT_RUN |
| Smoke MCP autenticado SURI em produção | TEST_NOT_RUN |

## 7. Execução seguinte mínima (SURI.S0 — INVENTORY/ARCHITECTURE GATE)

1. Validar HEAD + git status; regras .cursor globais, `openai-plugin-mcp-integration.mdc`, security/API/boundaries/plan-construction.
2. Ler integralmente `shared/delpi_mcp`, `shared/delpi_auth`, auth middleware + oauth contracts dos especialistas; conferir runtime/CI/deployment.
3. Mapear os blueprints `supplies-api` com rotas, use cases, AuthZ, unidades/ownership, contrato HTTP e testes.
4. Comparar duas opções concretas, sem declarar qual implementaremos antes da prova: adapter MCP co-local com Flask + ASGI boundary versus adapter separado com consumo exclusivamente de `supplies-api` por HTTP autenticado. Documentar trade-offs para autoridade/isolamento e política do repositório.
5. Definir RQ/AC e primeira fatia READ de risco baixo; provar autenticação e casos positivo/sibling/negativo; nenhuma escrita antes de gate.
6. Somente após decisão explícita, preparar implementation brief mínimo e testes.

**STOP CONDITION:** AuthZ final não comprovado, reuso que migre a BFF de Flask, MCP com acesso direto a `api-delpi`/Postgres de domínio irmão, permissão por tool, tokens compartilhados ou writes ERP bloqueados ⇒ EXECUTION_DRIFT.

**Veredito:** inventário de padrões em código **PARTIAL / ACCEPT_WITH_RESIDUAL** para desenhar SURI.S0. Implementação/go-live **INCONCLUSIVE** até fechar integração Flask, autenticação e paridade de capacidades com evidência.
