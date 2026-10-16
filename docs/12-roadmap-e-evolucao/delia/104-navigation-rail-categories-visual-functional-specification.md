# 104 — DÉLIA | NavigationRail — Rail permanente de categorias

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`. **Documentação somente**: sem frontend, backend, dados mock de produção, deploy, mudança de fase ou aceite.  
**Produto:** DÉLIA standalone. `plugin-ui` é owner de apresentação compartilhada; `plugins/delia` compõe o produto e seu estado. O Portal continua host/navegação global; Core resolve autorização; APIs de domínio são autoridade final; MCP/A2A não conferem permissão.  
**Reancoragem obrigatória antes de executar:** HEAD/git status e .cursor/Project Instructions → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → documentos temáticos → ledger; evidência conflitante exige `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`.  
**Base verificada nesta documentação:** GitHub `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b`. Não presumir que será o HEAD de implementação.  
**Gates universais:** `read != write`, `draft != send`, `PREPARE != ACT`, `discovery != approval`, `model output != FACT`, `JWT != live AuthZ`; layout não concede authority.  

**Master:** [103](./103-delia-navigation-sidebar-master-product-ux-specification.md).

## Responsabilidade

Faixa vertical persistente de entrada para `Conversas`, `Projetos`, `Agentes` e `Plugins/Aplicações`; pode conter ação de expansão e opções pertencentes à DÉLIA. **Não é a navegação global do Portal**; não deve replicar atalhos institucionais já hospedados pelo Portal. Cada ícone representa apenas um destino aprovado, nunca disponibilidade inferida de metadata de provider.

## Alvo visual e geometria

```text
┌──────┐
│ [≡]  │ botão único de recolher/expandir
│      │
│ [▤]  │ Conversas — selected
│ [▣]  │ Projetos
│ [♙]  │ Agentes
│ [▦]  │ Plugins
│      │
│ ...  │ spacer
│ [⚙]  │ Opções da conversa, apenas quando houver callback
└──────┘
```

- Largura alvo 56–64px desktop, 52px compact se utilizável; itens em área 40–44px, ícones 18–20px com traço consistente Lucide; gap 8–12px.
- Fundo contínuo do design system, borda direita hairline, **sem cartões permanentes cinza** em ícones ociosos; selected indica categoria por marca lateral/acento tonal e `aria-current` apropriado, não apenas cor.
- Ferramentas de expansão apresentam `PanelLeftOpen/Close`, ghost em repouso, hover cinza tonal nos dois temas; **um só toggle** em cada estado, conforme R5 do doc 99.
- Tooltips: `Conversas`, `Projetos`, `Agentes`, `Plugins`; nome acessível sempre presente quando só houver ícone.
- Não apresentar ícones de agentes/personas específicas no rail global; apenas a categoria. O catálogo correspondente aparece no painel.

## Estados e interações

| Estado | Comportamento |
|---|---|
| `default` | ícone neutro acessível |
| `hover` | tom sutil, tooltip após atraso curto |
| `selected` | indicador persistente e não dependente de cor |
| `disabled` | recurso planejado sem contrato, com explicação curta sem tooltip enganoso |
| `forbidden` | item omitido/restrito, sem vazamento de nomes |
| `collapsed_panel` | rail íntegro; centro ocupa espaço liberado |
| `expanded_panel` | item ativo alinhado ao painel correspondente |
| `compact` | rail pode virar entrypoint único se largura insuficiente |
| `focus` | outline claro e navegação keyboard |

Click category: escolhe a categoria visual e expande painel, **somente se a seção puder ser exibida de maneira honesta**; do contrário, mostrar estado unavailable sem simular conteúdo. Categoria selecionada não muda a conversa por si só. Contra clique repetido, idempotência de estado. Não construir keyboard shortcut global conflitando com Portal/composer.

## Eventos e contrato visual sugerido

`selectedCategory`, `onSelectCategory(category)`, `isPanelExpanded`, `onTogglePanel()`, `availableCategories[]` (projeção de availability). Props render-only, controladas pelo consumer quando necessário; sem fetch, Core ou provider mechanics.

## Layout/QA

Testar 1440/1280/1024/768/420/375/320px, Dock, dark/light, zoom 200%; nenhuma label deve truncar por estar sempre só no ícone. Ao colapsar, o foco permanece no toggle correspondente; ao selecionar categoria, foco permanece na categoria ou se move ao heading do painel conforme teste A11y. Tab order não atravessa opções ocultas.

**Reuse:** `EXISTING_EQUIVALENT=YES` para `IconButton`, `ConversationThreeRegionLayout` rail e CSS; `REUSE_DECISION=EXTEND`. `TO_INVENTORY` para `NavigationRail` genérico já existente antes de criar arquivo novo.

## Critérios transversais de qualidade

- **Design system:** usar tokens, typografia, `IconButton`, feedback e superfícies do `plugin-ui`; ícones Lucide, sem cores hardcoded como identidade; no claro e escuro, ícone ghost transparente em repouso, hover tonal, foco visível, estados pressed/selected distinguíveis.
- **Responsividade:** medir container do Portal, não assumir viewport global. Cobrir página ≥1440, 1280, 1024, 768, 420, 375, 320px, zoom 200%, além do Companion Dock; não renderizar lista legível em rail estreito.
- **Movimento:** transição curta 180–240ms conforme tokens existentes; `prefers-reduced-motion` instantâneo; nunca remount do `ConversationWorkspace` nem perda de draft ao selecionar categoria.
- **Acessibilidade:** landmarks únicos, labels de ícones e hints por teclado, `aria-current` para navegação, `aria-expanded`/`aria-controls` para expansão, ordem de Tab previsível, Escape apenas em overlays, restauração de foco, contraste e screen reader.
- **Sem falso runtime:** nada de nomes de conversas, projetos, agentes, plugins, datas, métricas ou permissão inferidos. Loading só com requisição real; vazio = resultado autorizado real, indisponível = contrato inexistente, proibido = sem revelação de recursos.
- **Segurança:** nenhum item visual executa domínio, MCP, ferramenta, automação ou write por clique sem fluxo autorizado. Dados externos são não confiáveis; labels/snippets renderizados como texto inerte.
- **Validação:** testes de props/callbacks/estados e negativos de AuthZ, QA page/dock light/dark, check de exports/federação, prova de generalização em cenários de navegação e revisão independente no SHA executado. `TEST_NOT_RUN` não equivale a PASS.



## Rework R1 — controle único, seleção e categoria indisponível

Aplica o [103 — Rework R1](./103-delia-navigation-sidebar-master-product-ux-specification.md). O rail é **parte da área esquerda existente**, não segunda sidebar; seu owner de estado é `DeliaConversationPage`/consumer. **Quando o painel está aberto, o controle de recolher fica apenas no header do painel; quando fechado, apenas no topo do rail.** Não há dois botões presentes simultaneamente no DOM. Em `launcher_only`, o rail não é exibido e existe um único disparador acessível na área central.

A ordem/alvos `Conversas → Projetos → Agentes → Plugins` é direção visual de produto. `forbidden` oculta item/metadata; `contract_unavailable` representa categoria aprovada para preview com botão disabled e descrição honesta; `authorized_empty` só após contrato/consulta real. Os indicadores de categoria selecionada não se confundem com disponibilidade, autorização ou status de carga. Em seleção, não destruir workspace nem alterar sessão; item ativo deve continuar semanticamente identificável quando painel recolhido. Ícone não disponível não recebe callback funcional. Para categorias proibidas, não mostrar tooltip revelador.

**A11y:** `nav` com nome singular, botões para mudança de painel e links apenas com rotas reais, `aria-current` para active quando semanticamente aplicável, `aria-expanded` para toggle com `aria-controls` apontando conteúdo efetivo; renderizar tooltips acessíveis. Em dark/light fundo ghost só em hover/focus/press. `REUSE_DECISION=EXTEND` do rail já existente, não substituição.
