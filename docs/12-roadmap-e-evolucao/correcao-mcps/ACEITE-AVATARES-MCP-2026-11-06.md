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

## HOTFIX AVATAR-INLINE-V1 (2026-11-06) — CLARA + SURI

**Teste real ChatGPT revelou duas falhas pós-rollout — corrigidas e verificadas em runtime.**

### CLARA — ImageContent descartado pelo envelope `_wrap`
- **Root cause PROVEN:** `controllership_finance_app/interface/mcp/semantic_bridge.py::_wrap` re-empacotava `mcp_tool_result(payload)` descartando blocos não-texto — o handler retornava `[Text,Image]` mas o envelope emitia só texto (metadados chegavam; imagem não). Mesmo defeito já corrigido no CAIO.
- **Fix:** `_wrap` agora carrega blocos `ImageContent` (`images=...`) — regressão `test_avatar_read_returns_image_content_block` valida o caminho completo `tool_read(avatar,get)`.
- **Read-back container:** `read(entity=avatar,action=get)` → `[TextContent, ImageContent]` mime `image/jpeg`. Commit `ac8136040f`; deploy `delpi-controllership-finance-api`.

### SURI — schema `read` sem entity `avatar` no tools/list
- **Root cause PROVEN:** `app/interfaces/mcp/server.py` declara o tool `read` com `entity: Literal[...]` fechado que não incluía `"avatar"` — o JSON Schema publicado rejeitava `'avatar' is not one of [...]` antes de chegar ao dispatcher (que já suportava a entidade).
- **Fix:** `"avatar"` adicionado ao Literal de `entity` (action `get` já existia). Regressão `tests/interface/suri_mcp/test_avatar.py`: schema anuncia `avatar` + `avatar.get` retorna `ImageContent image/png`.
- **Read-back container `delpi-supplies-mcp`:** `read(entity=avatar,action=get)` → `[TextContent, ImageContent]` mime `image/png`; rota pública e `mcp.avatar_distribution` intactos. Commit `5e5f56781c`; deploy `delpi-supplies-mcp`.

**Visual acceptance ChatGPT:** `TEST_NOT_RUN` — reteste manual: "CLARA/SURI, mostre seu avatar" deve renderizar a foto oficial inline; "Quais ferramentas você possui?" não deve inserir imagem.

## MCP-AVATAR-UI-V2 — piloto TÉO (MCP Apps) (2026-11-06)

**Backend/transporte PROVEN em runtime.** `shared/delpi_mcp/avatar_ui.py`
(cartão visual reutilizável: CSP restritiva ao origin da URL aprovada,
light/dark, alt acessível, fallback textual) + TÉO registra:

- resource `ui://delpi/teo/avatar/v1` → `read_resource` retorna HTML
  completo `text/html;profile=mcp-app` com URL oficial avatar-v2.png
  embutida e CSP `img-src` limitada ao origin aprovado;
- tool `show_avatar` (READ, mesma view-gate) com `_meta.ui.resourceUri`
  + payload `image_url`/mime/sha256 + `ImageContent` (fallback para
  hosts sem MCP Apps); `read(entity=avatar)` preservado.

Commits: `8fbacd7f17` (impl) + fix f-string py3.11 ×2; deploy
`delpi-transformometro-api` healthy no HEAD.

**Renderização visual ChatGPT: `TEST_NOT_RUN`** — a conexão precisa
reler `tools/list`+`resources/list`; reteste manual: "TÉO, mostre seu
avatar" deve renderizar o card com a foto inline; "TÉO, quais
ferramentas você possui?" não deve montar o componente. Se o host não
renderizar `ui://`, a limitação fica documentada (não é PASS visual).
Rollout VISTA/CLARA/CAIO/SURI/EVA bloqueado até essa validação.

## HOTFIX MCP-AVATAR-UI-V2.1 (2026-11-06) — timeout do componente TÉO

**Sintoma:** "Mostrar avatar oficial excedeu o tempo limite" no ChatGPT.
**Causa-raiz medida:** `show_avatar` executava em 0.01s mas transportava
o PNG inteiro (~1.39MB base64) no payload — latência/limite no caminho da
UI. **Fix:** `show_avatar` agora retorna metadados+`image_url` apenas
(129B); bytes seguem em `read(entity=avatar,action=get)` inalterado.
Adicionado `_meta["openai/outputTemplate"]=ui://delpi/teo/avatar/v1`
(chave reconhecida pelo Apps SDK, além do `ui.resourceUri` genérico).
**Read-back runtime:** exec 0.01s, payload 129B, meta OK, container
healthy. Visual ChatGPT: `TEST_NOT_RUN` (reteste manual pendente).

## HOTFIX MCP-AVATAR-UI-V2.2 (2026-11-06) — handshake MCP Apps

**Hipótese fundamentada aplicada (menor diff):** o componente era
estático — lia `window.openai` mas nunca respondia `ui/initialize` nem
emitia `ui/notifications/initialized`; hosts que dirigem o lifecycle
MCP Apps aguardam o ACK antes de entregar `tool-result` → timeout.
**Correção:** `avatar_ui.py` agora implementa o ciclo `ui/initialize`
(ACK `clientInfo`/`protocolVersion`) → `ui/notifications/initialized` →
`ui/notifications/tool-result` (structuredContent) + fallback
`window.openai`; recurso publica `_meta.ui.csp.resourceDomains`
(`https://minhadelpi.com.br`); URI bump `ui://delpi/teo/avatar/v2`
(cache do host). `show_avatar` segue metadata-only (129B);
`read(avatar,get)` com ImageContent intacto.
**Runtime:** resource v2 + csp + outputTemplate v2 verificados no
container; HTML contém handshake. ChatGPT visual: `TEST_NOT_RUN` —
reconectar a conexão MCP e retestar "TÉO, mostre seu avatar".

## HOTFIX MCP-AVATAR-UI-V2.3 (2026-11-06) — CSP do host + JS bloqueado

**Evidência do Console (PROVEN):** `inline script violates script-src` e
`img-src 'self' data:` bloqueava o PNG — a CSP **efetiva** é a do host
ChatGPT; metatag no HTML só restringe, nunca amplia. `ui.csp` no
resource meta não chegou ao host.
**Correção:** (1) `_meta["openai/widgetCSP"]` no tool `show_avatar`
(`resource_domains=[https://minhadelpi.com.br]`, `connect_domains=[]`) —
chave documentada do Apps SDK; (2) card agora **100% estático** — sem
`<script>` (img+nome+especialidade já embutidos no HTML; elimina a
violação de script-src e a dependência de handshake JS); (3) URI →
`ui://delpi/teo/avatar/v3`. `script-src 'none'` na metatag.
**Runtime:** tool meta + resource v3 + HTML sem script verificados no
container (1703B). ChatGPT visual: `TEST_NOT_RUN`.

## MCP-AVATAR-UI-V2.4 (2026-11-06) — experimento diagnóstico isolado

**Exp A publicado:** resource `ui://delpi/teo/avatar-diagnostic/text-v1`
(HTML texto mínimo — sem JS/imagem/CSS/URL) + tool
`show_avatar_diagnostic` (READ, mesmo gate). `show_avatar`/`v3` intactos.
**Runtime verificado:** tool registrada, resource listado, HTML texto
servido sem script/img.
**Reteste ChatGPT manual:** "TÉO, execute show_avatar_diagnostic e
mostre o componente 'TÉO — Teste visual'". Se o texto mínimo falhar →
o bloqueio está no host/contrato (cenário 1); se passar → avançar para
miniatura `data:` embutida (exp B). ChatGPT: `TEST_NOT_RUN`.

## MCP IMAGE DELIVERY V3 (2026-11-06) — descontinuação do MCP Apps

**Decisão:** a estratégia MCP Apps `ui://` (V2–V2.4) não renderiza no
ChatGPT — até o componente texto mínimo (`text-v1`) excedeu o tempo
limite. Backend provado; host não suporta a superfície nesta conexão.
**Removido (TÉO only):** `show_avatar`, `show_avatar_diagnostic`,
resources `ui://delpi/teo/*`, `delpi_mcp/avatar_ui.py`, handlers e
entradas de registry. **Preservado:** `read(entity=avatar,action=get)`
→ `[TextContent, ImageContent]` nos 6 MCPs + `delpi_mcp.avatar_image`
+ `avatar_distribution` + rotas públicas.
**Runtime:** tools = `[analyze,delete,execute,get_context,knowledge,
read]`; resources vazio; `read(avatar)` → ImageContent OK.
**ChatGPT visual:** `TEST_NOT_RUN` — reteste: "TÉO, mostre seu avatar"
deve acionar `read(entity=avatar)` e renderizar o PNG nativamente pelo
host (entrega de bytes governada; apresentação é do ChatGPT).

## MCP IMAGE DELIVERY V3.1 (2026-11-06) — rollout nativo verificado

**Matriz runtime (read-back container, HEAD atual):**

| MCP | read(entity=avatar,get) | ImageContent | Residual | Status |
|---|---|---|---|---|
| TÉO | ✅ [Text,Image] png | PASS | show_avatar/resources removidos | PASS |
| VISTA | ✅ [Text,Image] jpeg | PASS | — | PASS |
| CLARA | ✅ [Text,Image] jpeg | PASS | _wrap preserva blocos | PASS |
| CAIO | ✅ [Text,Image] jpeg | PASS | _wrap corrigido | PASS |
| SURI | ✅ [Text,Image] png (supplies-mcp) | PASS | schema literal inclui avatar | PASS |
| EVA | ✅ [Text,Image] jpeg | PASS | — | PASS |
| DAVI | PENDING — contrato `read(capability)` via `davi_read_wired`, área `external_capabilities` em refatoração ativa; integração de avatar exige registrar capability de leitura (não tool nova) — aguardar convergência da refatoração | — | — | PENDING |

**Residual search:** zero `show_avatar|avatar_ui|avatar-diagnostic|ui://delpi|widgetCSP` em todos os serviços.
**ChatGPT visual:** `TEST_NOT_RUN` — reteste por especialista: "mostre sua imagem oficial" → host deve renderizar `ImageContent` nativamente.

## DAVI — integração completada (2026-11-08)

`read(capability="avatar")` → `[TextContent, ImageContent]` (475KB png),
`get_context` com `identity.acronym` + `avatar_distribution` — verificado
em `delpi-api-delpi` (commit `f48feb6834`). 7/7 MCPs com entrega de imagem.
ChatGPT visual: `TEST_NOT_RUN`.

## CHARACTER PROFILE COMPLETENESS AUDIT V1 (2026-11-08) — SURI

**Lacuna comprovada:** `get_context(action="catalog")` publicava só
`mcp.persona/acronym/mission/avatar_distribution` — sem `character`
(estrutura que TÉO/VISTA/CLARA/CAIO/EVA/DAVI já projetam).
**Fix menor:** `mcp["character"] = _suri_character()` (helper
`project_persona_context(get_suri_profile())`) no catalog + `character`
em `action="context"`. Campos projetados: identity, appearance_summary,
avatar_status/reference, personality_summary, communication, expertise,
conduct, coexistence, relationships, narrative_classification,
profile_version. **Runtime `delpi-supplies-mcp`:** catalog retorna
character com os 12+ campos + acronym correto. Demais 6: já conformes
(verificado pela evidência do usuário + código). Commit impl.

## DELPI SPECIALIST VISUAL IDENTITY V1 (2026-11-08) — DAVI envelope + governança

**Sintoma reportado:** `read(capability="avatar")` do DAVI retornava
metadata `content_delivery="image_block"`, mas o consumidor da conversa
não recebeu bloco de imagem acessível.

**Investigação (cadeia MCP server → transport → envelope → adapter → host):**
- Wire JSON-RPC PROVEN in-process (`streamable_http_app`):
  `tools/call read(capability="avatar")` → `content=[text, image]`
  (PNG 633KB base64) + `structuredContent` — backend/transporte correto,
  paridade com os 6 irmãos.
- **Defeito de contrato encontrado:** `structuredContent` do avatar
  violava o `outputSchema` publicado `readOutput` (campos obrigatórios
  `capability/status/action_id/projection/truncated/is_complete`
  ausentes + `additionalProperties:false`). Os 6 irmãos anunciam
  `outputSchema` permissivo (`{"type":"object"}`) — DAVI era o único
  divergente; host que valide `structuredContent`×`outputSchema` podia
  desconfiar do resultado.
- **Fix (menor diff, owner-local):** metadata do avatar agora viaja no
  campo `data` do envelope `readOutput` canônico
  (`structuredContent.data.*`). `content=[text,image]` inalterado.
- Teste novo `tests/test_davi_avatar_read_contract.py` (6 testes):
  ImageContent real + sha256 do asset, conformidade `ReadOutput`,
  escopo do asset, negativo `avatar_x`→`CAPABILITY_NOT_ALLOWED`,
  superfície de tools inalterada (4 tools).
- Knowledge V2: seção `VISUAL IDENTITY & OFFICIAL AVATAR` + patch de
  Instructions (~2.6k chars) em DELPI-SPECIALIST-CONVERSATION-ACTIVATION-V2.

**Gap residual host-side:** se o conector DAVI em uso for do tipo
Plugin/app (fronteira "OpenAI Plugin adapter"), ele pode expor apenas
`structuredContent` ao consumidor — comportamento não comprovável pelo
repositório. `CHATGPT_VISUAL: TEST_NOT_RUN` — reteste manual V1–V12.
