# 111 — DÉLIA | PluginNavigation — Aplicações e integrações

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`; **documentação somente**.  
**Master:** [103 — DeliaNavigationSidebar](./103-delia-navigation-sidebar-master-product-ux-specification.md).  
**Base verificada:** `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b` antes dos commits desta série. Documentação não é runtime nem autorização de execução.  
**Autoridades para reancoragem antes de código:** HEAD/git status + Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura → product spec → temática → ledger. `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED` em conflito.  
**Owner de apresentação:** `plugin-ui`; **consumer/estado:** DÉLIA; Core/Portal/Domain APIs preservam seus boundaries.  


## Direção e limites de ownership

A categoria `Plugins / Aplicações` funciona como **navegação de descoberta para recursos externos autorizados**, usando catálogo/rotas/capabilities já pertencentes ao Core/Portal e eventualmente ao Plugin Management. Não criar um segundo marketplace/catálogo nem resolver permissões pelo client, plugins declarativos ou MCP discovery. Verificar se essa categoria deve permanecer em DÉLIA quando já existir navegação global Portal; em conflito, `ARCHITECTURE_DECISION_REQUIRED`.

`EXISTING_EQUIVALENT=YES` para componentes UI, Portal como owner de aplicativos/rotas; `REUSE_DECISION=REUSE` via boundary. Para feed/filtro específicos `TO_INVENTORY` antes de desenhar adapter.

## Visual alvo

```text
Aplicações e recursos                [recolher]
Disponíveis para você
  [ícone aprovado] Nome do recurso           [↗]
                    Descrição curta
Categorias de aplicação * se publicadas pelo Core
  Operação / Painéis / Integrações...
```

Itens 44–60px, ícone 18–24px segundo tokens do kit, nome 13–14px, descrição breve permitida e estado do tipo de destino (abrir no Portal / link externo aprovado). Não carregar logo arbitrário de metadata untrusted. “Plugin” e “Aplicação” só são rótulos equivalentes se o catálogo do owner assim definir; evitar sugerir que qualquer ferramenta MCP é um plugin instalável.

## Comportamento

Selecionar abre rota oficial através do Portal quando autorizada; não importar código de outro MFE para dentro da DÉLIA nem inspecionar seu banco. Para integrações que exigem conexão/permissão, respeitar consentimento do usuário e confirmação de instalação nos fluxos oficiais; a sidebar nunca instala silenciosamente nem dá fake “Conectado”.

Estados `unavailable`, `loading_real`, `authorized`, `permission_required`, `connection_required`, `forbidden`, `error`, `stale_entry`. Se a permissão foi revogada, remover item ou mostrar estado neutro conforme contrato, nunca abrir por link stale. A categoria não causa planner ACT nem automation write.

## Contratos futuros

Descoberta via catálogo Core/Portal por boundary oficial, route identity, label/icon/description autorizados, scopes, validation/expiry, erro, deep-link permitido, observabilidade e regras de exibição; integração externa/credenciais pertencem aos owners. Alguns recursos podem ser exibidos apenas como atalho; outros devem estar somente no Portal para não duplicar navegação.

## QA

Validar rota interna/autorizada, links externos seguros, provider untrusted, permissões revogadas, offline, icon fallback, labels longos, várias dezenas de aplicações, performance, screen reader, light/dark, keyboard, portal host e Dock. Verificar que categorias não tornam o Portal um subcomponente de DÉLIA.

## Contrato de qualidade transversal

Usar cores/tokens do kit em light/dark, sem tons cinzas permanentes em botões ghost de repouso. Ícones 16–20px, hit target 40–44px, foco 2px, labels reais, keyboard e tooltip acessível; movimento 180–240ms ou nulo em `prefers-reduced-motion`. Validar container 1440/1280/1024/768/420/375/320px, zoom 200% e Companion Dock; sem overflow horizontal, remount de conversa ou perda de draft. Snapshots ou exemplos de UI nunca substituem dados/permission reais. Testes e browser QA permanecem `TEST_NOT_RUN`; independente `PENDING`.



## Rework R1 — definição de boundary Portal/Core (R-05)

**Decisão aplicável para o desenho da UX:** Plugins/Aplicações na DÉLIA representa **apenas descoberta ou atalhos para recursos já publicados e autorizados pelo Portal/Core**, sem segundo catálogo, Marketplace, instalador, permission broker ou local registry. `EXISTING_EQUIVALENT=YES` para **owner de apps/rotas** Portal/Core; `REUSE_DECISION=REUSE` por boundary/roteamento. **Disponibilidade de contrato específico e lista autorizada = TO_INVENTORY.**

No rail, “Plugins” é affordance conceitual de produto; não enumerar apps indiscriminadamente. Sem projection oficial, `contract_unavailable` (se aprovada para visualização) ou ocultar; `forbidden` sempre oculto. Seleção de app = navegação aprovada, não ACT nem instalação. Se surgir requisito de gerenciar novos providers ou instalar plugins **dentro da DÉLIA**, `ARCHITECTURE_DECISION_REQUIRED` antes de redesenhar; não estender escopo silenciosamente.

## Implementação bounded 08 — PluginNavigation (2026-10-17)

**Autorização:** Product Master solicitou “Ok, implementar” para o próximo componente após AgentNavigation. **Base HEAD observada:** `bda378050077c3fa3ff79dc230efa53d3813ff0d`. Entrega limitada a um componente frontend render-only e integração de apresentação na DÉLIA; não existe autorização para criar catálogo, adapter, registry, launcher de app, instalar plugin, credenciais, runtime MCP ou ACT.

**Reuse Gate:** `EXISTING_EQUIVALENT=YES` para `ConversationThreeRegionLayout`, `NavigationRail`, `NavigationCategoryPanel`, estados/tokens de AgentNavigation e ProjectNavigation; `REUSE_DECISION=EXTEND` da apresentação. `EXISTING_EQUIVALENT=YES` para **owner** de aplicativos e rotas Portal/Core; `REUSE_DECISION=REUSE` por boundary, sem importar catálogos ou banco de outro MFE. **Feed/contrato oficial autorizado específico = TO_INVENTORY**, `REUSE_DECISION=PENDING_GATE` para integração backend. Conteúdo/projeções de catalogadores e providers continuam untrusted, `discovery != approval`.

**Componente:** `PluginNavigation.tsx` + `PluginNavigation.css` no `plugins/plugin-ui/src/components/conversation`. Props `status?:contract_unavailable|ready|loading|authorized_empty|error`, `items?:readonly {id,title,description?,selected?,external?}[]`, `onOpenApplication?(id)`, `onRetry?;` `className?`. Por padrão, mostra `contract_unavailable` e **nenhuma aplicação fictícia**. `ready` mostra apenas itens da projeção autorizada pelo consumer junto a callback legítimo, lista/heading semânticos, ícone neutro `Blocks`, descrição curta, selected, indicador visual `ExternalLink` quando indicado pelo owner. **Não recebe URL nem renderiza anchor/deep-link**: o consumer tem obrigação de resolver ID por rota oficial com live AuthZ; callback só expressa intenção, não permission nem êxito do negócio. Não há ações Instalar/Conectar/Executar.

**Integração:** `DeliaConversationPage` habilita **Plugins como categoria visual de preview** no rail recolhido. Selecionar expande o único painel existente com `NavigationCategoryPanel category="plugins"` e `PluginNavigation status="contract_unavailable"`. O shell mantém um botão toggle e `ConversationWorkspace` central sem remount intencional. As outras categorias não são modificadas. Navegação entre categorias ainda requer recolher painel; shell persistente rail+painel da spec 103 exige evolução própria e **não** está concluído.

**Estilos e testes:** surface ghost e tokens light/dark, foco visível, linhas >=48px, truncamento e descrição de duas linhas, reduced-motion. Criados `PluginNavigation.test.tsx` e teste de `DeliaConversationPage`: states unavailable/loading/authorized_empty/error, callback por ID, ausência de links/ações inventados, XSS inerte, preservação do centro e retorno à categoria Conversas. Alterados exports `components/conversation/index.ts` e `src/index.ts`, CSS import em `src/styles.css`, gate `scripts/verify-host-exports.mjs`.

**Evidência e limites:** os arquivos e commits publicados em `main` podem ser verificados por API GitHub; `VITEST=TEST_NOT_RUN`, `TSC=TEST_NOT_RUN`, `FEDERATION_BUILD=TEST_NOT_RUN`, `PORTAL_DOCK_QA=TEST_NOT_RUN`, `INDEPENDENT_REVIEW=PENDING`, `PHASE_PROGRESSION=NONE`. A reancoragem integral de .cursor/16→50→17→49→51→52→21→20→25/arquitetura/ledger e git status de workspace não foram verificados nesta execução: `INCONCLUSIVE`. Este documento não transforma o código em `PASS` de produção. `CODE_COMMITTED_CANDIDATE` somente após HEAD final confirmado.
