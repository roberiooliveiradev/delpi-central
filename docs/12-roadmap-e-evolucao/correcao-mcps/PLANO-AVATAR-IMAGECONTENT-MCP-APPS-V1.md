# PLANO DE IMPLEMENTAÇÃO — Avatares inline nos MCPs DELPI V1

**Data:** 2026-11-06  
**Estado:** PLANNED / TARGET; implementação e aceite visual ainda não executados.  
**Owners:** TÉO (transformometro-api), VISTA (tv-dashboard-api), CLARA (controllership-finance-api), CAIO (commercial-api), SURI (supplies-api), EVA (engineering-api), DAVI (api-delpi; **bloqueado para mudanças durante refatoração**).  
**Problema:** as fichas já guardam avatar oficial, mas o ChatGPT não apresenta necessariamente a imagem dentro da conversa; retornar `avatar_distribution.url` não é renderização inline.

## 1. Objetivo e limites da experiência

Ao perguntar *"Mostre seu avatar"*, *"Como é sua aparência?"*, *"Como você é visualmente?"*, *"Mostre sua foto"* ou perguntas equivalentes sobre características do personagem, o especialista deve exibir **o arquivo de avatar original, aprovado**, diretamente dentro da conversa, com texto descritivo quando cabível. O usuário não deve depender de clicar no link. Resposta não visual (ex.: ferramentas) não deve inserir foto automaticamente. Apresentação de identidade sem intenção visual pode ser somente textual. Não gerar ou editar nova imagem.

**Não confundir:** imagem inline na mensagem, bloco `ImageContent` enviado pela tool MCP, recurso visual MCP Apps e **ícone permanente do GPT/plugin**. São capacidades distintas; nenhuma é garantida pela simples presença de URL na ficha. Clientes sem suporte de imagem devem continuar recebendo informação textual e eventualmente link como fallback honesto.

## 2. Contratos já existentes — PROVEN no GitHub e no MCP

`shared/delpi_character_profiles` define modelos, validações, projeções e versões; cada owner mantém sua ficha `CharacterProfile` e asset. **Shared owns the structure. MCP owns the character.** Não duplicar fichas no `shared` nem criar registro central, SQL, URL proxy genérico ou outra autoridade.

| MCP | Fonte/arquivo local | Avatar publicado na projeção MCP consultada |
|---|---|---|
| TÉO | `transformometro-api/tm_app/assets/characters/teo/avatar-v2.png` | `avatar_distribution.url` HTTPS; status APPROVED |
| VISTA | `tv-dashboard-api/tv_app/content/characters/vista/avatar-v2.jpg` | `avatar_distribution.url` HTTPS; status APPROVED |
| CLARA | `controllership-finance-api/controllership_finance_app/assets/characters/clara/avatar-v1.jpg` | `avatar_distribution.url` HTTPS; status APPROVED |
| CAIO | `commercial-api/commercial_app/assets/characters/caio/avatar-v1.jpg` | `avatar_distribution.url` HTTPS; envelope alternativo `distribution`/`media_type` |
| SURI | `supplies-api/app/assets/characters/suri/avatar-preview-v1.png` | **Não exposto** em `get_context(action=catalog)`, apesar de `OFFICIAL_AVATAR_APPROVED` na ficha |
| EVA | `engineering-api/engineering_app/assets/characters/eva/avatar-v1.jpg` | `avatar_distribution.url` HTTPS; status APPROVED |
| DAVI | `api-delpi/app/assets/characters/davi/avatar-v1.png` | Existia metadata em projeção anterior; **não retestado na refatoração** |

TÉO, VISTA, CLARA, CAIO, EVA e DAVI têm código de rota HTTP `/public/characters/{character_id}/avatar/{filename}` nas APIs proprietárias; SURI não apareceu no inventário desse padrão (verificar outras rotas antes de declarar ausência). A prova HTTP externa 200, MIME, hash e renderização real ainda é **TEST_NOT_RUN/INCONCLUSIVE**, não PASS.

Fontes: `shared/delpi_character_profiles/README.md`, `ACEITE-AVATARES-MCP-2026-11-06.md`, `INVENTARIO-FONTES-EXISTENTES.md`, perfis `*/persona/*_profile.py`, catálogos e `*_agent_intelligence.json`.

## 3. Architecture Decision Gate — escolher a menor via comprovada

**POC primeiro no TÉO**. Inventariar as versões reais dos SDKs, transportes MCP, resources, retorno `CallToolResult`, metadados da tool e consumidores ChatGPT. Testar duas vias antes de decidir:

**A. MCP ImageContent:** uma ferramenta/resource de leitura com resultado `content` de imagem `type=image`, MIME e base64 do asset **exato** aprovado; conteúdo textual estruturado mínimo; sem URL arbitrária nem binário na ficha/catalog. Suportar limites de dimensão/bytes/memória. **ImageContent disponibiliza bytes ao cliente/modelo, mas não prova apresentação inline.**

**B. MCP Apps / interface visual inline:** disponibilizar recurso `ui://` com componente visual vinculado à ferramenta de consulta do avatar por metadata da UI (ex.: `_meta.ui.resourceUri`, conforme SDK e especificação efetivamente instalados). Mostrar foto oficial em HTML responsivo com alt, contexto visual seguro e CSP que permita somente domínio da imagem aprovado. Sem tokens no HTML, sem interceptar dados privados e sem usar iframe de site não confiável. Validar compatibilidade com o cliente ChatGPT real, não só testes de servidor.

Escolher a opção **somente após teste visual real**: se A exibir imagem inline, não introduzir B; se A apenas devolver bytes ou links, aplicar B quando suportado. Se ambas não funcionarem no cliente, reportar limitação e alternativa realmente suportada, sem afirmar sucesso. Não criar ferramenta nova caso resource ou capability existente satisfaça a necessidade. Se for necessária ferramenta, usar nome e contrato de leitura específico do owner, sem modificar ferramentas existentes de escrita.

Manter regras de apresentação: consultas sobre aparência disparam foto; consulta de especialidade puramente funcional não dispara automaticamente; `Who am I` pode permanecer texto a menos que usuário indique intenção visual. Ícone do plugin/GPT é fora do escopo backend; levantar requisito manual separadamente.

## 4. SURI — correção obrigatória, não duplicar o asset

1. Confirmar `supplies-api/app/content/suri_agent_intelligence.json`, `app/persona/suri_profile.py`, `OFFICIAL_AVATAR_APPROVED`, `avatar_reference`, asset real, SHA-256 e MIME.
2. Descobrir rotas reais do owner, ingress e serviços distintos `delpi-supplies-api` e `delpi-supplies-mcp`. Se não houver rota equivalente, implementar endpoint público **estritamente allowlisted** para o avatar aprovado, sem path de usuário, sem autenticação porque asset é público aprovado, mas com verificação de basename, status e presença; resposta 404 para outros ids/files, `Content-Type: image/png`, `X-Content-Type-Options: nosniff` e `Cache-Control` apropriado.
3. Projetar metadata mínima de `avatar_distribution` na descoberta SURI a partir da ficha do owner, URL HTTPS configurada e SHA do **asset servido**, seguindo o padrão existente dos demais MCPs sem impor transformação incompatível a consumers.
4. Testar URL externa e a mesma instância conectada ao ChatGPT. O fato do filename conter `preview` **não** invalida a aprovação de `OFFICIAL_AVATAR_APPROVED`; renomear somente se necessário e com migração compatível.
5. Rebuild/deploy dos **serviços afetados**, não apenas da API: a SURI já teve `EXECUTION_DRIFT` porque `supplies-mcp` não acompanhou `supplies-api`.

## 5. Rollout dos demais

- **TÉO:** POC A/B, aceitação visual, fixar contrato mínimo em testes.
- **VISTA:** manter avatar v2 e services atuais; aplicar somente adaptação de apresentação.
- **CLARA:** preservar URL/asset aprovado e projeção existente.
- **CAIO:** respeitar envelope `avatar_distribution` existente (`distribution`, `media_type`), sem breaking change. Se adaptação necessária, fazê-la aditiva.
- **SURI:** corrigir rota/projeção e adicionar capacidade visual com prova no ChatGPT.
- **EVA:** preservar `act_tiers`, `import=false` e outras políticas; recurso de avatar é read-only.
- **DAVI:** somente inventário/brief de mudança futura enquanto refactor estiver ativo, sem editar, commitar ou deployar.

Antes de extrair código compartilhado, aplicar **Abstraction Gate**: necessidade real, owner/boundary, equivalente existente, solução simples, coupling e segurança. Um eventual helper compartilhado deve ser visual/transport-neutral, sem importar módulos internos dos MCPs e sem possuir avatares.

## 6. Matriz obrigatória de testes

Para cada MCP alterado:
- Perfil: status `OFFICIAL_AVATAR_APPROVED`, referência, hash, formato, arquivo e versão.
- Rota pública: GET anônimo 200, MIME correto, bytes e dimensões, SHA alinhado, sem redirecionamento indevido, HTTPS, cache; 404 para filename, character_id e traversal inválidos; nenhum vazamento de caminho ou token.
- Projeção: URL idêntica ao asset exposto, versão/MIME/status, compatibilidade dos consumers e retrocompatibilidade.
- Tool ImageContent: bytes originais exatos, `mimeType`, esquema `content`, limitação de payload e fallback de host sem imagem.
- UI MCP Apps (se usada): metadata/resource `ui://`, CSP, rede, layout acessível e responsivo, alt e fallback. Usar SDK oficial e contrato real.
- ChatGPT: **abrir conexão do especialista**, pedir `Mostre seu avatar` e `Como é sua aparência?`; imagem deve aparecer **no próprio chat sem clicar** e texto refletir a ficha; pergunta de ferramenta não deve inserir avatar desnecessariamente.
- Negative/security: status não aprovado, arquivo ausente, erro de rede, MIME inválido, host sem suporte, autenticação/404, tamanho excessivo; sem escrita/consentimento.
- DAVI não é submetido a testes/alterações enquanto bloqueado pela refatoração.

Marcar `PROVEN`, `TO_INVENTORY`, `PLANNED`, `TARGET` e `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE` apropriadamente. Teste unitário verde, 2xx do MCP ou asset HTTP 200 **não provam** imagem visível no ChatGPT. Se não puder acessar a UI do ChatGPT, registrar `TEST_NOT_RUN` e ações manuais exatas; não inventar screenshot/aceite.

## 7. Fluxo de implementação e deploy

1. `git status`, `git rev-parse HEAD`, `git fetch` seguro, ler `AGENTS.md`, instruções `.cursor/.devin`, fontes canônicas, consumers, OpenAPI/Actions, infra e docs.
2. POC TÉO read-only; provar o melhor modo na UI antes de multiplicar diffs.
3. Corrigir SURI e, após contract gate, distribuir a solução nos quatro outros MCPs previstos. Um owner de cada vez, menor diff e preservar trabalho paralelo.
4. Testes focalizados + regressão, `git diff --check`, residual search e segurança; corrigir só o que for atribuível à task.
5. Commit/push seguro por owner; deploy canônico dos componentes MCP/API realmente alterados. Confirmar SHA/runtime e versões de artefatos (não basta health 200).
6. Authoritative read-back: catálogo, recurso, GET externo, respostas das ferramentas e visual no ChatGPT. Nunca chamar sucesso antes de observar a foto realmente renderizada.
7. Atualizar `docs/12-roadmap-e-evolucao/correcao-mcps/` com execução, decisões, evidências, commits, gaps e etapas manuais.

## 8. Critérios de parada e aceite

- **PASS técnico por owner:** arquivo aprovado, URL pública verificada, transporte seguro, tool/resource correto, metadados coerentes, tests pass e SHA em runtime.
- **PASS experiência ChatGPT:** imagem original e correta renderizada inline no chat quando solicitada, sem clique, com texto aderente à aparência declarada.
- **PENDING/TEST_NOT_RUN:** interface ChatGPT ou configuração MCP do cliente não acessível; registrar owner da ação manual e roteiro.
- **OUTCOME_VERIFICATION_FAILED:** resposta ou imagem diferente do esperado após deploy; não declarar sucesso nem compensar com imagens geradas.
- **Semântica de DONE:** seis MCPs com aceites visuais aprovados, SURI corrigida; DAVI só entra quando o gate de refatoração for liberado. Se cliente não suporta renderização solicitada, registrar limitação comprovada em vez de mascará-la.

## 9. Relatório obrigatório

`TRANSFORMÔMETRO EXECUTION REPORT` por owner: TASK, BASE HEAD, FINAL HEAD, STATUS, OWNER/SOURCE/CONTRACT, files, tests, OpenAPI/Actions, AuthZ, postcondition, read-back, residual search, gaps/risks, commit/push, deploy, manual GPT Builder/ChatGPT actions. Incluir matriz consolidada e status de **visual acceptance** separado de backend acceptance.

**Regra final:** manter identidade e assets owner-local, não inventar fatos nem habilidades de UI, **provar antes de generalizar**.
