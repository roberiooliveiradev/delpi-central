# Aceite dos avatares MCP — diagnóstico e execução orientada a evidências

**Data:** 2026-11-06  
**Objetivo:** separar identidade narrativa, distribuição pública da foto, renderização da foto em resposta do ChatGPT e ícone do plugin/GPT.  
**Escopo:** TÉO, VISTA, CLARA, CAIO, SURI, EVA; DAVI apenas inventário, **sem alterar** durante refatoração.  
**Execução nesta auditoria:** leitura de fonte GitHub e consultas MCP de catálogo; **nenhum deploy nem mutação de código do domínio**.

## Evidência PROVEN no MCP conectado

| MCP | Ficha informa aprovação | Avatar HTTPS na resposta de catálogo | Fonte |
|---|---|---|---|
| TÉO | Sim | `https://minhadelpi.com.br/apps/transformometro-api/public/characters/teo/avatar/avatar-v2.png` | `tm_app/application/gpt_actions/teo_agent_intelligence_service.py` |
| VISTA | Sim | `https://minhadelpi.com.br/apps/tv-dashboard-api/public/characters/vista/avatar/avatar-v2.jpg` | `tv_app/application/gpt_actions/vista_agent_intelligence_service.py` |
| CLARA | Sim | `https://minhadelpi.com.br/apps/controllership-finance-api/public/characters/clara/avatar/avatar-v1.jpg` | `controllership_finance_app/application/clara/agent_intelligence_service.py` |
| CAIO | Sim | `https://minhadelpi.com.br/apps/commercial-api/public/characters/caio/avatar/avatar-v1.jpg` | `commercial_app/persona/caio_profile.py` e projection do MCP |
| EVA | Sim | `https://minhadelpi.com.br/apps/engineering-api/public/characters/eva/avatar/avatar-v1.jpg` | `engineering_app/application/eva/agent_intelligence_service.py` |
| SURI | Sim no JSON e no teste da ficha | **Não publicado em `get_context(action=catalog)`** | `supplies-api/app/content/suri_agent_intelligence.json`; `app/persona/suri_profile.py`; `app/interfaces/mcp/tool_bridge.py` |
| DAVI | Sim na projeção anterior; não retestado nesta rodada | URL constava em `agent_directives.character.avatar_distribution` antes da refatoração | `api-delpi/app/persona/davi_profile.py` + serviço de inteligência |

**SURI:** o avatar `app/assets/characters/suri/avatar-preview-v1.png` já existe na árvore GitHub, tem `sha256` estático e `avatar_status=OFFICIAL_AVATAR_APPROVED`; o teste `tests/persona/test_suri_profile.py` valida integridade do arquivo. Porém, não foi encontrada rota `/public/characters/.../avatar/...` no inventário da árvore de `supplies-api` e a resposta de catálogo não expõe `avatar_distribution`. A indisponibilidade HTTP real ainda precisa de teste pelo ambiente com rede de produção. O sufixo `preview` no filename não invalida a aprovação do campo, mas pode confundir consumers.

**Outros seis:** TÉO, VISTA, CLARA, CAIO, EVA e DAVI possuem código de rota HTTP de avatar público owner-local em suas APIs. Para CAIO, o envelope `avatar_distribution` difere: `distribution=public` e `media_type`, em vez de `kind=public_https`/`mime_type`. Antes de padronizar, verificar consumidores reais; não quebrar contratos existentes.

## Teste de URL externa — INCONCLUSIVE
- A tentativa HTTP GET de cinco URLs via executor desta sessão falhou na resolução DNS de `minhadelpi.com.br` (**limitação de rede deste executor**).
- A tentativa de abrir binário pela ferramenta de navegação não concluiu; **não representa prova de 404, 401 ou falta de acesso público**.
- Ainda faltam respostas GET reais da internet com `HTTP 200`, `Content-Type: image/*`, comprimento, redirecionamentos e SHA-256 coerente.

## Causa raiz dividida por objetivo

**A. Avatar presente na ficha mas sem metadata SURI:** PROVEN lacuna no catálogo SURI; provável necessidade de rota owner-local e projeção de metadados, condicionada a inventário de contrato HTTP existente.

**B. Foto aparecer automaticamente em mensagens do ChatGPT:** a resposta MCP em JSON com `avatar_distribution.url` **não exige** renderização como imagem pelo cliente. A apresentação visual deve usar capacidade da plataforma (por exemplo, componente opcional MCP Apps com recurso UI para pedidos explícitos de avatar), em vez de esperar renderização automática de um campo JSON. O modelo pode, no mínimo, apresentar um link verificável. Não inserir base64 gigante no `agent_directives` nem tentar forçar UI por texto.

**C. Ícone permanente do plugin ou GPT:** é configuração de apresentação da entidade na plataforma, distinta de `CharacterProfile` e de `avatar_distribution`. Não afirmar que pode ser alterada pelo MCP sem provar a API/manifest de publicação apropriada.

## Execução solicitada ao Cursor — roteiro

1. **HEAD safety**: `git status`, `git rev-parse HEAD`, `origin/main`; preservar trabalho paralelo, inclusive DAVI.
2. **Inventariar owners e consumers**: perfil, JSON declarativo, serviço de projection, rota pública e cliente ChatGPT; escolher o menor método suficiente. Distinguir **imagem em resposta** de **ícone da interface**.
3. **Confirmar HTTP real para os 5 URLs publicados**, em uma rede que alcance `minhadelpi.com.br`: GET anônimo, 200, conteúdo de imagem, cache, SSL, `nosniff`, integridade SHA, payload/dimensões, caminhos do proxy. Observar `PUBLIC_BASE_URL`, container e ingress; jamais expor tokens.
4. **SURI**: verificar se já existe rota equivalente por outro nome; se não houver, implementar rota pública allowlisted exclusivamente para o arquivo aprovado no owner `supplies-api`; publicar somente metadados sanitizados do avatar na superfície semântica de descoberta, sem conceder AuthZ e sem expor path arbitrário. Reusar padrão provado das APIs, sem criar registry ou tool genérica.
5. **CAIO**: não mudar formato de `avatar_distribution` se consumidores existentes dependerem dele; adicionar compatibilidade apenas se houver contrato explícito e testes.
6. **Teste de exibição na conversa**: avaliar se o host ChatGPT renderiza imagem vinculada na resposta textual; se não, implementar componente MCP Apps **somente quando a necessidade for renderizar a foto na conversa e houver suporte da conexão**. Testar com solicitação explícita "Mostre o avatar da SURI". Não prometer foto automática após toda chamada.
7. **Ícone do plugin/GPT**: inventariar configuração do plugin/Agent Studio/Builder separadamente. Se a plataforma exigir upload/edição manual, fornecer ações exatas; não simular atualização via `agent_directives`.
8. **Testes**: perfil, hash SHA, basename/allowlist, 404 para identidade ou filename incorretos, imagem pública sem token, cache, no path traversal, headers `Content-Type`, projeção MCP, endereço externo, teste real no ChatGPT; teste do GPT/plugin visual `TEST_NOT_RUN` se inacessível.
9. **Deploy**: confirmar serviços MCP distintos de APIs, como foi comprovado no incidente `delpi-supplies-mcp`; build, push, deploy canônico, SHA/runtime, GET externo e reconsulta do catálogo após rollout; não declarar sucesso por health 200.
10. **Entrega**: `TRANSFORMÔMETRO EXECUTION REPORT` por owner, contendo BASE/FINAL HEAD, fonte e contrato, alterações, testes, AuthZ, impacto OpenAPI/Actions, read-back, status, gaps, commit/push/deploy e ações manuais do ChatGPT. **Nunca afirmar que a UI mostra a foto sem um teste real visível do ChatGPT**.

## Matriz de aceite
| Requisito | Estado atual |
|---|---|
| Avatar aprovado/ficha em 7 owners | PROVEN no código e projeções disponíveis, com DAVI sujeito a refactor |
| Metadados HTTPS de TÉO/VISTA/CLARA/CAIO/EVA no MCP | PASS |
| Metadados HTTPS de SURI no MCP | FAIL |
| Arquivo SURI e teste de SHA em GitHub | PROVEN |
| HTTP 200 externo de cada imagem | INCONCLUSIVE |
| Renderização da foto no corpo da conversa ChatGPT | TEST_NOT_RUN |
| Uso automático da foto como ícone de plugin/GPT | TO_INVENTORY; não decorre da ficha |
| Código corrigido/deploy de avatar | NOT_IMPLEMENTED nesta auditoria |
