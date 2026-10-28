# EVA.MCP.V1 — Marco de conexão funcional ao ChatGPT e evolução paralela

**Data da evidência:** 2026-10-28  
**Estado:** `PROVEN` para criação/conexão do Plugin EVA no ChatGPT e execução de `get_catalog` na sessão autenticada apresentada; `PENDING` para testes de negócio `get_engineering_home` e `get_engineering_overview` e negativos de permissão em ambiente real.  
**Base de implementação:** EVA.MCP.V1 (`3060ab0741`), hardening EVA.MCP.V1.R1 (`b47441108b`); documentação 26–30.  
**Fonte de evidência funcional:** capturas de tela fornecidas pela Coordenação nesta conversa, referentes à administração Keycloak e ao ChatGPT conectado. As capturas não foram anexadas ao repositório; este registro descreve exatamente o que mostram, sem afirmar log de backend ou teste automatizado independente.

## 1. Marco confirmado

- Keycloak de produção: realm `delpi`, cliente OpenID Connect `mcp-engineering` criado e habilitado, autenticação de cliente ON, Standard Flow ON, demais fluxos interativos/serviço não necessários desabilitados; PKCE S256 apresentado.
- Client scopes: `mcp:tools` e `audience-delpi` associados como Default. Mapper dedicado `audience-mcp-engineering` inclui a custom audience `https://minhadelpi.com.br/apps/engineering-api/mcp` no access token, não no ID token.
- Simulação do access token no Keycloak (“Evaluate”): `iss=https://minhadelpi.com.br/auth/realms/delpi`; `azp=mcp-engineering`; `aud` inclui o recurso MCP EVA e `delpi-central`; `scope` inclui `openid email mcp:tools profile`. Não houve verificação independente do JWT obtido em login real.
- Callback `https://chatgpt.com/connector_platform_oauth_redirect` cadastrado em `Valid redirect URIs` do cliente, conforme captura da tela Keycloak.
- No ChatGPT: Plugin “EVA — Engenharia Virtual Assistida” criado com endpoint `https://minhadelpi.com.br/apps/engineering-api/mcp`, autenticação OAuth e registro de client definido pelo usuário; interface exibiu “Aprovado pelo administrador” e tela de conexão.
- **Evidência decisiva:** em conversa com EVA selecionada no ChatGPT, foi solicitada explicitamente a execução de `get_catalog`; a resposta exibida informa “Executei get_catalog com sucesso” e apresenta exatamente as **três ferramentas implementadas** (`get_catalog`, `get_engineering_home`, `get_engineering_overview`) e **três grupos de capacidades planejadas** (produtos; BOM/roteiros; desenhos/especificações/inspeções), em conformidade com o contrato do MCP V1. Isso demonstra uma interação de ferramenta funcional observada no cliente; não substitui logs independentes do request.
- A interface também exibiu uma resposta de apresentação (“quem é você?”); essa resposta isolada não comprovaria acesso ao backend e não é usada como evidência do catálogo.

**Veredicto de ativação:** `ACCEPT_WITH_RESIDUAL` — o marco “EVA conectada e get_catalog funcional no ChatGPT” está atingido conforme evidência visual; **não** marcar `E2E_FULL_PASS` para dados de negócio nem negativas de autorização até testes explícitos.

## 2. Matriz de evidências

| Item | Estado | Evidência/limite |
|---|---|---|
| Cliente Keycloak e mapper dedicado | PROVEN visualmente | Capturas do console Keycloak |
| Claims de token (simulação Evaluate) | PROVEN para simulação | Não valida sessão OAuth real |
| Plugin criado / aprovado no ChatGPT | PROVEN visualmente | Capturas de UI |
| Execução `get_catalog` via ChatGPT | PROVEN visualmente | Resposta mostrando ferramentas reais e planned não implementadas |
| `get_engineering_home` com dados autorizados | PENDING | Não demonstrado |
| `get_engineering_overview` com indicadores reais | PENDING | Não demonstrado |
| Usuario sem `engineering.access` / falhas por recurso | PENDING | Não demonstrado no cliente real |
| Logs e correlação de execução autenticada | PENDING | Não fornecidos |
| Verificação de diferentes usuários e revogação | PENDING | Não demonstrado |

## 3. Diretriz aprovada de produto e arquitetura

**O Portal Engenharia permanece a experiência digital, e EVA permanece especialista interoperável (não uma tela/rota interna fictícia). A Engineering API e a EVA evoluirão em paralelo.**

Regra de entrega de toda nova capability:

1. Inventariar **owner → fonte oficial → contrato → autorização real**; registrar fatos `PROVEN | TO_INVENTORY | PLANNED | TARGET`.
2. Definir a operação na Engineering API (ou reutilizar contrato oficial existente) com request/response, erros, filtros, limites, observabilidade e testes. Nunca acessar bancos alheios, importar internals de outro domínio ou duplicar regra de owner.
3. Adicionar/atualizar use case e adapters conforme necessidade real; preservar Clean Architecture e AuthN Keycloak, AuthZ Core e por recurso em downstream.
4. Expor **tool MCP EVA correspondente somente quando a API já possui contrato implementado e testado**; catalogar a capacidade com schema, escopo de leitura/escrita, provenance, limites e estados de falha.
5. Testar encadeamento `ChatGPT → MCP EVA → engineering-api → owner` com identidade humana e negativas; nunca elevar com service token.
6. Publicar de forma compatível, versionada e com rollback; documentar commits/SHA, smoke e outcome. Separar `DRAFT/CANDIDATE` de revisão/aprovação/publicação para desenho/documentos futuros.

O MCP permanece **in-process em `engineering-api`**, com `shared/delpi_mcp`, sem novo serviço autônomo salvo decisão arquitetural formal. A EVA não vira source of truth.

## 4. Próxima evolução de Engenharia — inventário, não promessa

Priorizar novas capacidades pela existência de dados oficiais e autorização, não por uma lista aspiracional. Investigar inicialmente:

- Consultas específicas de LMPs/solicitações e detalhes permitidos, além dos resumos atuais.
- Produtos/descrições técnicas, estruturas/BOM, roteiros e processos, **somente após localizar contratos oficiais**.
- Desenhos/inspeções e comparações desenho × dados como fase posterior; nenhuma cota, tolerância, material ou norma deve ser inventada.
- Qualquer geração de artefato: `fonte → extração → análise → DRAFT/CANDIDATE → owner review → publicação`; sem escrita/ACT sem gates governados.

**Próximo gate recomendado:** completar testes reais de `get_engineering_home` e `get_engineering_overview` no ChatGPT (com períodos, valores e provenance), e ao menos um negativo de autorização; em paralelo inventariar a próxima leitura oficial que possa virar capacidade incremental da Engineering API + EVA.

## 5. Restrições de segurança e evidência

Sem secrets, tokens, IDs pessoais ou payloads sensíveis neste documento. O client OAuth não confere `engineering.access`: a Core continua autoridade de RBAC, e os owners downstream aplicam permissões por recurso. Capturas de UI não equivalem a smoke de produção do lado do servidor. Nenhuma evidência aqui autoriza a alegação de catálogo de produtos, BOM, roteiros, desenhos ou escrita já implementados.

**Status de coordenação:** `EVA.MCP.V1 = FUNCTIONAL_CONNECTION_PROVEN_WITH_RESIDUALS`; `ENGINEERING_API + EVA = PARALLEL_INCREMENTAL_EVOLUTION`.
