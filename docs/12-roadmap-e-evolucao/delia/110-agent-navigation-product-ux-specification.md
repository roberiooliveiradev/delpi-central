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


