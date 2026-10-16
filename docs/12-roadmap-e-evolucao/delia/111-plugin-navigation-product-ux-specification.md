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
