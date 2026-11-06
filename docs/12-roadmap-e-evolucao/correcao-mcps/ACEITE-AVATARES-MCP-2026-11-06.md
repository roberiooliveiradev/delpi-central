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

## Reteste após implementação AVATAR-INLINE-MCP-V1 (2026-11-06)

**Backend PROVEN em runtime nos 6 MCPs (DAVI fora de escopo — refatoração).**
Mecânica canônica `shared/delpi_mcp/avatar_image.py`; cada owner expõe
`read(entity=avatar, action=get)` retornando bloco `ImageContent` real
(bytes do asset aprovado + MIME + sha256, cap 8MB, fallback metadata).

| MCP | Tool ImageContent (container) | Rota pública HTTPS | avatar_distribution |
|---|---|---|---|
| TÉO | PASS `[Text,Image]` | 200 image/png ~1.0MB | existente |
| VISTA | PASS `[Text,Image]` | 200 image/jpeg ~341KB | existente |
| CLARA | PASS `[Text,Image]` | 200 image/jpeg ~288KB | existente |
| CAIO | PASS `[Text,Image]` | 200 image/jpeg ~379KB | existente |
| SURI | PASS `[Text,Image]` (supplies-mcp) | **200 image/png ~2.0MB — rota nova** | **implementado** |
| EVA | PASS `[Text,Image]` | 200 image/jpeg ~433KB | existente |

Negativos: `character_id`/filename inválidos → 404 (allowlist no
basename do `avatar_reference` aprovado). SURI: middleware de auth
isenta apenas `/public/characters/` (rota allowlisted ao asset aprovado).

**Renderização visual no ChatGPT: `TEST_NOT_RUN`** — o cliente deve
exibir o bloco `image` inline; comprovação visual depende da UI real.
Procedimento manual por especialista: perguntar *"Mostre seu avatar"*
(esperado: imagem oficial inline sem clique); *"Quais suas ferramentas?"*
(não deve inserir imagem). Se o bloco não renderizar, MCP Apps `ui://`
é o plano B documentado no plano §3.B.


## Reteste das conexões ChatGPT — após rollout (2026-11-06)

**Escopo:** chamadas reais das ferramentas MCP conectadas neste chat, sem DAVI e sem writes. Comparar com PASS container acima; estado do cliente pode diferir de estado do servidor.

| MCP | Chamado `read(entity=avatar,action=get)` | Observação | Aceite do transporte nesta conexão |
|---|---|---|---|
| TÉO | Retornou `content_items` com 2 blocos: `text` e `image` (`image/png`, 1.041.179 bytes conforme metadata) | A imagem oficial foi efetivamente encaminhada e exibida **nesta conversa** por operação explícita de visualização do bloco | **PASS** transporte; **PASS demonstração inline nesta conversa**, não comprova roteamento automático no GPT individual |
| VISTA | 2 blocos (`text`, `image/jpeg`) | `content_delivery=image_block`; bytes retornados | **PASS** transporte, visual ChatGPT individual `TEST_NOT_RUN` |
| CAIO | 2 blocos (`text`, `image/jpeg`) | `content_delivery=image_block` | **PASS** transporte, visual ChatGPT individual `TEST_NOT_RUN` |
| EVA | 2 blocos (`text`, `image/jpeg`) | `content_delivery=image_block` | **PASS** transporte, visual ChatGPT individual `TEST_NOT_RUN` |
| CLARA | `structuredContent` retornou metadata de avatar aprovado, `content_delivery=image_block`, porém a resposta da ferramenta **não continha `content_items` de imagem** na integração observada | Divergência entre container `[Text,Image]` reportado e wrapper/transport acessado nesta sessão | **INCONCLUSIVE/FAIL de paridade de entrega**: rastrear serialização e metadata do adapter; não assumir defeito no arquivo |
| SURI | **Rejeitado antes do serviço**: enum do schema da tool `read` conectado não inclui `entity=avatar` | O servidor pode estar atualizado, mas o schema anunciado/armazenado no cliente não permite chamar o novo contrato | **FAIL do schema de integração cliente/MCP**: descobrir owner do schema e atualização/reconexão/reinstalação conforme política, sem modificar domínio por palpite |

**Achados e ação recomendada:**
1. SURI — inspecionar geração/publicação do JSON Schema da ferramenta `read` e atualização da conexão no ChatGPT; comparar registro real do servidor e schema do cliente. Não tratar o erro de validação como ausência de arquivo/rota.
2. CLARA — investigar preservação dos `ImageContent` na serialização entre `read`, wrapper MCP, conector e host; confrontar wire response e projeção recebida no ChatGPT. Não alterar o arquivo da foto até comprovar causa.
3. TÉO/VISTA/CAIO/EVA — transportar bytes foi comprovado; roteamento de intenção (`avatar`, `aparência`) e renderização automática nas sessões individuais ainda exigem aceite humano. Prova do TÉO nesta conversa veio do **encaminhamento explícito do bloco de imagem**, não de autopresentação automática do plugin.
4. DAVI — não acionado nem alterado.

**Evidência epistemológica:** relatório do Devin = PASS backend, confirmação local parcial; a experiência end-to-end de seis especialistas no ChatGPT permanece **PENDING**. Sem evidência de alteração no runtime ou de erro HTTP da imagem neste reteste.
