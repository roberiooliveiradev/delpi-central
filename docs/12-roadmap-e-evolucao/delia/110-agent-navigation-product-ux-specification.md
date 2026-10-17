# 110 — DÉLIA | AgentNavigation — Especialistas e agentes

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`; **documentação somente**.  
**Master:** [103 — DeliaNavigationSidebar](./103-delia-navigation-sidebar-master-product-ux-specification.md).  
**Base verificada:** `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b` antes dos commits desta série. Documentação não é runtime nem autorização de execução.  
**Autoridades para reancoragem antes de código:** HEAD/git status + Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura → product spec → temática → ledger. `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED` em conflito.  
**Owner de apresentação:** `plugin-ui`; **consumer/estado:** DÉLIA; Core/Portal/Domain APIs preservam seus boundaries.  


## Intenção e autoridade

A categoria **Agentes** permite descobrir e acessar experiências assistivas legítimas, sem criar autoridade paralela nem converter qualquer resultado MCP/A2A em agente aprovado. Verificar catálogo/registro já existente, o domínio do agente, owner, surface/autorização Core, capacidade semântica, persona publicada e limites de uso. `discovery != approval`; `agent scope != Core/domain authorization`; `tool metadata != permission`.

`EXISTING_EQUIVALENT=YES` para rail/painel/cards/avatares visuais disponíveis no kit; `REUSE_DECISION=REUSE|EXTEND` visual. `EXISTING_EQUIVALENT=TO_INVENTORY` para catálogo de agents e launch boundary; `REUSE_DECISION=PENDING_GATE`.

## Aparência

```text
Agentes                               [recolher]
Especialistas disponíveis
  [avatar] Nome aprovado
           Descrição curta permitida         [>]
  [avatar] Outro especialista autorizado     [>]
Categorizações futuras * somente se owner fornecer
  Operações / Dados / Transformação etc.
```

Somente itens autorizados, com avatar institucional publicado, nome 13–14px, descrição 11–12px em até duas linhas, status disponível/indisponível apenas se fonte determinar, target 44–56px. Usar `UnifiedAvatar` ou equivalente do kit após inventário; não recriar avatar. Ícones de agentes apresentados no painel, **não** proliferados no rail geral. Lista com hover tonal, focus-visible, sem sombras/cards pesados por linha. Nunca inventar ranking, capacidade ou qualidade.

## Estados e comportamento

`catalog_unavailable`, `loading`, `authorized_list`, `empty_confirmed`, `restricted`, `launch_pending`, `launch_failed`, `stale_catalog`. Selecionar um agente não executa capability automaticamente: o consumer resolve rota/hand-off governado, escopo mínimo delegado e permissões live. O Planner continua sem endpoints/tool mechanics.

Abertura pode acontecer em contexto de conversa, em nova visão ou navegação Portal **apenas segundo contrato explícito de sessão/experiência**. Não reutilizar memória ou agentes do Minha DELPI Chat. Se não houver contrato de transição, botão não é funcional; não alterar status da conversa.

## Recursos futuros (dependentes)

- Explorar catálogo aprovado com descrição curta, tags autorizadas e classificação editorial do owner.
- Abrir ficha de especialista e origem/capabilities tipadas; metadata jamais sobrepõe Policy.
- Iniciar sessão ou handoff contextual somente quando autorizados; limites de exposição de dados e usuário confirmados.
- Favoritar/fixar agentes apenas com write autorizado, idempotência e postcondition; não transformar toque em publicação de preferência backend.
- Indicar disponibilidade real sem inferir a partir de falha de timeout ou texto do modelo.

## Contratos necessários

Owner/catalog version, IDs, display name, avatar, description, scope, availability, capability projection, consumidor, route/launch actions, erros, AuthN/AuthZ, Domain authority, delegated identity/credentials, observabilidade, registros de execução quando governados. Provider/A2A/MCP permanece integração, não autoridade.

## Segurança e QA

Itens não autorizados omitidos sem leak de nomes; resposta do catálogo tratada como dados não confiáveis; ausência do provider nunca libera fallback não aprovado. Testar click com/sem autorização, cross-tenant, revogação, Unicode/HTML nos labels, longa descrição, dark/light, dock/mobile, screen reader, mudança de categoria no meio de conversa e ausência de execução automática. Verificar que abrir item não representa sucesso de task/outcome.

## Contrato de qualidade transversal

Usar cores/tokens do kit em light/dark, sem tons cinzas permanentes em botões ghost de repouso. Ícones 16–20px, hit target 40–44px, foco 2px, labels reais, keyboard e tooltip acessível; movimento 180–240ms ou nulo em `prefers-reduced-motion`. Validar container 1440/1280/1024/768/420/375/320px, zoom 200% e Companion Dock; sem overflow horizontal, remount de conversa ou perda de draft. Snapshots ou exemplos de UI nunca substituem dados/permission reais. Testes e browser QA permanecem `TEST_NOT_RUN`; independente `PENDING`.



## Rework R1 — agentes aprovados, não descoberta como permissão

Categoria Agentes é alvo visual; listagem e launch requerem `EXISTING_EQUIVALENT=TO_INVENTORY` de catálogos oficiais, Agent/Capability projection, owner e rotas governadas. `REUSE_DECISION=PENDING_GATE` para feed/launch. Um agente encontrado via MCP/A2A não vira aprovado/visible pelo metadata. Em falta de contrato, categoria apenas `contract_unavailable` quando product preview aprovado; `forbidden` é omitido. Seleção de item não delega credentials nem inicia execução sem passagem autorizada e guardas de escopo mínimo. Não criar agents/personas paralelos aos owners existentes.

## Implementação bounded 07 — AgentNavigation (2026-10-17)

**Autorização:** Product Master confirmou “Ok, implemente” após a entrega `ProjectNavigation`. **BASE_HEAD consultado:** `94dd12cb0ee391135f5d6eceb596791b39d16112`. Esta task implementa **somente o componente frontend `AgentNavigation`** e sua integração como categoria de apresentação, não executa MCP/A2A, criação de agentes, planner, delegação ou integração de catálogo.

### Reuse e ownership

- `EXISTING_EQUIVALENT=YES` para `NavigationRail`, `NavigationCategoryPanel`, `ConversationThreeRegionLayout`, estados e estilos da navegação de projetos; `REUSE_DECISION=EXTEND` do shell existente, sem outro `nav` persistente, fonte de dados ou runtime.
- `EXISTING_EQUIVALENT=TO_INVENTORY` para catálogo oficial de especialistas e agents, capability projection, contrato de launch, provider/connector e scopes legítimos; `REUSE_DECISION=PENDING_GATE` para qualquer interação real. Catálogo não é inventado por este componente e MCP discovery não confere permissão.
- `plugin-ui` é owner de apresentação; `plugins/delia` consome com estado visual transitório. Core/Domain preservam AuthZ e autoridade final; o Planner não recebe endpoint, selector ou provider mechanics.

### Contrato e aparência entregues

`AgentNavigationProps`: `status = catalog_unavailable|ready|loading|authorized_empty|error`, `agents?: readonly {id,name,description?,selected?}[]`, `onSelectAgent?(id)`, `onRetry?`, `className?`. Sem contrato, default `catalog_unavailable` com orientação única e **nenhum agente fictício**. `ready` só renderiza itens providos pelo consumer com callback, lista semântica, heading “Especialistas disponíveis”, ícone institucional neutro `Bot` 19px (não identidade física/pessoal fabricada), descrição em até 2 linhas e título de uma linha. Não foi adicionada nova API de avatar antes do inventário de `UnifiedAvatar` e das identidades oficiais. O click sinaliza somente intenção visual; não executa/handoff/lança capability. `onRetry` aparece apenas em `error` com callback explícito. `forbidden` deve ser filtrado antes da projeção; o componente não autoriza.

Estilos isolados `AgentNavigation.css` reutilizam tokens light/dark, ghost transparente, hover tonal, selected distinto, hit target mínimo 48px, foco visível e reduced motion. Nenhum provider branding hardcoded.

### Integração e limites

`DeliaConversationPage` habilita **Agentes como prévia visual da categoria** no `NavigationRail`, além de Conversas e Projetos. Ao selecionar, expande o único shell existente e apresenta `NavigationCategoryPanel category="agents"` com `AgentNavigation status="catalog_unavailable"`. A conversa central e o ContextPopover não são remontados intencionalmente; Plugins continua indisponível. No painel expandido, a navegação entre categorias ainda depende de recolher para acessar o rail — evolução futura do shell, **não solucionada nesta task**. Não foi criado um catálogo/registro de agentes na DÉLIA.

### Arquivos e evidência

Criados `plugins/plugin-ui/src/components/conversation/AgentNavigation.tsx`, `AgentNavigation.css`, `AgentNavigation.test.tsx`. Ajustados exports `components/conversation/index.ts` e `src/index.ts`, CSS import em `src/styles.css`, gate `scripts/verify-host-exports.mjs`, `plugins/delia/src/ui/DeliaConversationPage.tsx` e seu teste.

Testes criados para ausência de dados fictícios, callback de seleção, ausência de ACT, textos inertes, states error/loading/empty e preservação do centro no consumer. **Execução não comprovada:** `VITEST=TEST_NOT_RUN`, `TSC=TEST_NOT_RUN`, `FEDERATION_BUILD=TEST_NOT_RUN`, `BROWSER_QA=TEST_NOT_RUN`, `INDEPENDENT_REVIEW=PENDING`. Reancoragem integral .cursor/16→50→17→49→51→52→21→20→25, arquitetura, ledger e workspace status não comprovados por este conector: `INCONCLUSIVE`. Não há aceite de fase ou runtime; resultado limitado a `CODE_COMMITTED_CANDIDATE` quando a publicação for verificada na main.
