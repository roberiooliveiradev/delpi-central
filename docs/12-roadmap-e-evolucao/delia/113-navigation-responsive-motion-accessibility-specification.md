# 113 — DÉLIA | NavigationSystem — Responsividade, movimento e acessibilidade

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`; **documentação somente**.  
**Master:** [103 — DeliaNavigationSidebar](./103-delia-navigation-sidebar-master-product-ux-specification.md).  
**Base verificada:** `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b` antes dos commits desta série. Documentação não é runtime nem autorização de execução.  
**Autoridades para reancoragem antes de código:** HEAD/git status + Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura → product spec → temática → ledger. `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED` em conflito.  
**Owner de apresentação:** `plugin-ui`; **consumer/estado:** DÉLIA; Core/Portal/Domain APIs preservam seus boundaries.  


## Contrato responsive por container (alvos de QA)

| Container disponível | Rail | Painel de categoria | Centro / contexto |
|---|---|---|---|
| ≥1440px | 56–64px | 248–288px por default | centro amplo, popover flutuante |
| 1280–1439px | 56–64px | aberto quando há largura útil | centro preservado |
| 1024–1279px | 56–64px | aberto ou overlay conforme largura real | sem compressor de composer |
| 768–1023px | 52–60px se viável | overlay opcional ao selecionar | centro prioritário |
| 421–767px | rail compacto ou launcher | drawer/modal só por interação | ocupar viewport do host |
| ≤420px, Dock | launcher único se rail inviável | drawer acessível | 100% área central útil |

Limiares são **candidatos**, não CSS congelado. A implementação deve provar por `ResizeObserver`/container queries que nada ocupa `100vw` ou `100vh` indevidamente no Portal. Zoom 200%, landscape e tela redimensionada durante overlay entram no QA. Se drawer e card Contexto coexistirem, aplicar regra de uma superfície modal/overlay dominante em narrow, sem esconder confirmação governada.

## Motion e mudança de layout

Rail não desaparece no desktop; painel anima `inline-size`/transform sem reflow de mensagens em toda a timeline; feedback 180ms, painel 240ms e curva `ease-out` existente como orientação. Conteúdo não entra em foco antes de estar visível, oculto não fica tabulável, `prefers-reduced-motion` remove movimento. Evitar `will-change` permanente ou animações de largura em milhares de itens.

## Keyboard/foco/landmarks

`nav aria-label="Navegação da DÉLIA"`, com links/buttons semanticamente corretos e nomes em ícones. Rail não deve renderizar `role=tab` a menos que padrão ARIA de tabs completo (roving focus, tablist, painel associado) seja comprovado; preferir nav simples com `aria-current`, controles de expansão `aria-expanded` e `aria-controls`. Painel tem heading próprio, lista semântica, scroll independente; foco retorna ao rail quando overlay fecha. Escape fecha somente overlay, não interrompe turnos/cancelamento. Menu contextual de um item controla seu próprio foco; screen readers não recebem alertas duplicados.

## Estados de rede e dados

Sem histórico persistido, não apresentar lista de conversas nem estado “0 conversas” afirmado como consulta. Projetos/agentes/plugins só são exibidos quando contrato e owner aprovados; categorias sem contrato podem manter affordance desabilitada com nome e explicação neutra se approved. Erro de catálogo não bloqueia o centro. Nenhuma mudança de categoria desmonta composer ou limpa draft; restore de scroll é local e não confere authority.

## Design tokens e light/dark

Cores/surfaces somente por tokens compartilhados, contraste ≥WCAG AA para texto normal e foco, contornos não dependentes só de cor, hover tonal e ícones ghost transparentes em repouso. Density do Portal/Dock deve reutilizar tokens reais existentes, não inferir nova paleta. Usar hit targets de 40–44px; labels podem truncar só no painel expandido, com nome acessível completo.

## Plano de testes e evidência

- Componente: toggles, seleção, resize e category panel open/close, teclado, disabled e reusability.
- Integração: `ConversationWorkspace` permanece montado e draft conserva texto em 4 categorias, streaming em andamento, contexto flutuante e tooltips.
- AuthZ: catálogos não revelam recursos indevidos e revogação live remove acesso; no provider metadata grants.
- Visual: screenshots antes/depois, Chrome/Firefox, light/dark, 1440/1280/1024/768/420/375/320, zoom 200%, Dock e reduced motion.
- Build/module federation do kit + consumer DÉLIA no mesmo SHA e configuração; checks dos exports host-only.
- Review independente `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`, sem concluir PASS com TSX apenas.

**Reuse:** `EXISTING_EQUIVALENT=YES` para shell existente, shared tokens e `ConversationWorkspace`; `REUSE_DECISION=EXTEND` visual. Acessibilidade, observabilidade e segurança existentes devem ser reutilizadas, não criar infra/engine.

## Contrato de qualidade transversal

Usar cores/tokens do kit em light/dark, sem tons cinzas permanentes em botões ghost de repouso. Ícones 16–20px, hit target 40–44px, foco 2px, labels reais, keyboard e tooltip acessível; movimento 180–240ms ou nulo em `prefers-reduced-motion`. Validar container 1440/1280/1024/768/420/375/320px, zoom 200% e Companion Dock; sem overflow horizontal, remount de conversa ou perda de draft. Snapshots ou exemplos de UI nunca substituem dados/permission reais. Testes e browser QA permanecem `TEST_NOT_RUN`; independente `PENDING`.


