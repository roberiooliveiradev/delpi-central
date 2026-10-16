# 114 — DÉLIA | Revisão independente documental da navegação 103–113

**Data:** 2026-10-16  
**Objeto:** documentos [103](./103-delia-navigation-sidebar-master-product-ux-specification.md) a [113](./113-navigation-responsive-motion-accessibility-specification.md), revisados como conjunto após decisão do Product Master de adotar rail permanente de categorias + painel expansível.  
**Base:** `main` `0b1a2f9044fe32d38c5d89e432eb31be4d5c065f` no início desta revisão.  
**Veredicto:** `REWORK` **documental**; `CODE_REVIEW=NOT_REQUESTED`; `RUNTIME_TESTS=TEST_NOT_RUN`. Esta revisão não altera aprovação de fase nem concede execução.  
**Escopo de evidência:** conteúdo integral dos documentos 103–113 e consultas aos componentes atuais `ConversationSidebar` e `ConversationThreeRegionLayout`, além dos documentos 97–100. Foi possível consultar o HEAD e arquivos via conector GitHub. **Não foi feito inventário integral dos documentos canônicos 16/50/17/49/51/52/21/20/25, .cursor ou ledger**, nem execução de build/test/browser. Portanto nenhuma afirmação de conformidade canônica total ou de readiness da fase é autorizada.

## 1. Síntese do review

**Direção de produto consistente:** rail de categorias + painel expansível, conversa central preservada, contexto direito como popover; classificação `PLANNED` e intenção de reaproveitar `plugin-ui`. As restrições `discovery != approval`, `MCP result != FACT`, autorização por owners legítimos e ausência de históricos inventados estão majoritariamente presentes.

**Resultado não liberável para implementação integral:** cinco problemas de decisão/contrato ainda exigem resolução antes de gerar todos os subcomponentes. As telas e geometria são candidatas, não contratos visuais congelados. Um executor não deve converter nomenclaturas UX em 10 arquivos automaticamente.

## 2. Achados por severidade

### R-01 — BLOQUEANTE: slot único para expandir/recolher e rail versus painel

**Fontes:** 104 define toggle no topo do rail e 105/112 determinam que ele migra para o header do painel quando expandido. A intenção de **um só botão** aparece nos textos, mas o contrato de composição (render slot, ownership de estado e posição em transição) não é tipado. O `ConversationThreeRegionLayout` atual já controla expansão e renderiza um botão em sidebar existente. Sem uma regra efetiva, a implementação pode duplicar novamente controles ou montar um segundo shell.

**Correção requerida:** congelar **um único owner** do estado `expanded/collapsed/overlay` na composição DÉLIA e **um único local visual por estado**, especificando DOM/slot/focus e reuso do shell. Confirmar se rail e painel são duas áreas *dentro* da região left atual; não criar outro nav persistente ao lado da sidebar antiga. Especificar transição sem remount do workspace.

### R-02 — BLOQUEANTE: modelo de disponibilidade/visibilidade de categorias

**Fontes:** 103/104 sugerem quatro categorias persistentes e também descrevem `forbidden` como ocultação e `disabled` como ausência de contrato; 109–111 exigem owners ainda `TO_INVENTORY`. Não há matriz fechada para categoria “planejada mas visível”, “desconhecida”, “sem permissão”, “sem contrato”, “com catálogo autorizado porém vazio”.

**Correção requerida:** sem interface de catálogo oficial, exibir apenas affordances de produto explicitamente aprovadas, sem sugerir capacidade real. Definir a matriz `approved_visible | contract_unavailable | loading_real | authorized_empty | forbidden | error | revoked`. Autorização final é backend; UI state não é policy. Diferenciar especificação visual de funcionalidade publicada; não declarar nenhuma das quatro categorias pronta por constar no rail.

### R-03 — BLOQUEANTE: regra objetiva para desktop, compact, mobile e Companion Dock

**Fontes:** 103, 105 e 113 fornecem faixas propostas, mas usam expressões como “se couber”, “quando necessário” e “launcher único se inviável”, deixando o limiar ao implementador. As telas devem ser tratadas por **container do host**, não viewport global.

**Correção requerida:** documentar algoritmo de prioridade: mínimo de largura útil do centro/composer → largura do rail → se painel pode estar inline ou deve ser overlay → fallback launcher no Dock. Congelar quem decide close/open ao cruzar breakpoint e quando restaura preferência. Definir coexistência com ContextPopover, backdrop, Escape, foco e confirmações governadas. Valores finais somente após QA do Portal/Dock.

### R-04 — ALTO: contratos de ações e guardas do estado da conversa

**Fontes:** 106–108 e 112 listam seleção, Nova conversa, fixar, renomear, arquivar, excluir, pesquisa e opções, mas não há **uma matriz única** de `READ`, `PREPARE`, `ACT`, owner, AuthZ live, confirmação, idempotência e postcondition por ação. `onNewConversation` sozinho não congela o contrato de criação de sessão persistida.

**Correção requerida:** separar componentes exclusivamente visuais de jornadas com backend. Seleção/leitura exige autorização e recuperação do conteúdo; alterações/fixação/remoção exigem owner e write gates. Proteger draft, streaming e PREPARE/ACT pendentes, sem usar `setTurns([])` como criação de conversa. Reutilizar doc 97 para search backend-only. Até contrato aprovado, botões podem existir visualmente em estado honestamente indisponível sem executar.

### R-05 — ALTO: duplicação potencial da navegação Portal/Core em Plugins/Aplicações e Projetos

**Fontes:** 109 ainda descreve “projeto” como recurso sem owner comprovado; 111 reconhece que Plugins/Aplicações pode repetir o catálogo global. 110 distingue corretamente agentes de MCP discovery, mas o catálogo aprovado ainda está `TO_INVENTORY`.

**Correção requerida:** antes de implementar listagem real, inventariar Domain API/Core/Portal, registry/capability já existentes, adapters legítimos, consumidores e contratos. `EXISTING_EQUIVALENT=TO_INVENTORY` para recursos que não estão comprovados; `REUSE_DECISION=PENDING_GATE`. Se o Portal já oferece Apps como navegação global, a DÉLIA só pode exibir atalhos/deeplinks aprovados, ou devolver a decisão ao owner — não montar segundo gerenciador/catálogo.

### R-06 — MÉDIO: sobreposição de nomes, semântica de navegação e modelo acessível

**Fontes:** 103 enumera 10 responsabilidades como “subcomponentes”, mas algumas são apenas listas, menus ou estados; 104 propõe nav com `aria-current`, 113 reconhece o risco de usar tabs sem padrão ARIA completo.

**Correção requerida:** congelar API mínima de composição antes de criar arquivos: `NavigationRail` + `NavigationCategoryPanel` + conteúdo render-only da categoria via slots, usando `ConversationSidebar` existente. Não criar `NavigationPanelToggle`, `PinnedConversations`, `ConversationNavigationOptions` ou agentes/projetos/plugins como componentes novos apenas porque foram nomeados. Definir landmark único e relação do rail com o painel, `aria-current`/label, suporte teclado e foco ao colapsar/trocar seção.

### R-07 — MÉDIO: estados vazios e placeholders em protótipos

**Fontes:** 103/106/109–111 usam wireframes com nomes ilustrativos e disponibilidade futura; restrições anti-mock existem, mas continuam distribuídas.

**Correção requerida:** um único contrato cross-component de `unavailable` versus `authorized_empty` versus `forbidden` e `stale`. No frontend visual, se categoria foi escolhida e não há backend, mostrar orientação curta **sem falso dado**, no máximo uma por categoria. “Recentes”, “Fixadas”, contagem e títulos não podem aparecer como se viessem de consulta real.

### R-08 — MÉDIO: governança de design system e teste não comprovados

**Fontes:** 103–113 mencionam tokens/ícones/tamanhos, mas não há screenshot comparativo target no Portal e Dock, nem typecheck/build/federation/browser executados para esse design. As durações e breakpoints continuam alvos.

**Correção requerida:** inventariar componentes compartilhados de rail/drawer/navigation, verificar CSS final light/dark, reduced motion, screen reader, viewports e resize real. Registrar QA depois de código e no SHA/config efetivo. Não declarar UI ACCEPT com base em documentação.

## 3. Matriz de status de revisão

| Item | Condição documental | Veredicto do item |
|---|---|---|
| 103 — Master | Visão/propriedade boas; falta freeze da composição e do estado | REWORK |
| 104 — Rail | Visual claro, mas controle único e availability ambíguos | REWORK |
| 105 — Painel | Necessita contrato de slot, overlay, foco e breakpoints | REWORK |
| 106 — Conversas | Correta dependência de persistência; falta matriz ação × gate | ACCEPT_WITH_RESIDUAL |
| 107 — HistoryItem | Apresentação definida; backend ACL e actions pending | ACCEPT_WITH_RESIDUAL |
| 108 — Fixadas | Correto tratar fixação como write; owner/contrato pending | ACCEPT_WITH_RESIDUAL |
| 109 — Projetos | Entidade/owner ainda não inventariados | INCONCLUSIVE |
| 110 — Agentes | Limites MCP/A2A corretos; catálogo/lançamento não provados | INCONCLUSIVE |
| 111 — Plugins/Apps | Potencial sobreposição Portal/Core não resolvida | REWORK |
| 112 — Ações | Reuse adequado; gates por ação precisam ser congelados | REWORK |
| 113 — Responsive/Motion/A11y | Bons alvos; regras de corte e regressão incompletas | REWORK |

Os status por item refletem **revisão documental**, não aceite de implementação. Em particular, “ACCEPT_WITH_RESIDUAL” não prova backend, permission nem execução.

## 4. Decisões a levar ao Product Master / coordenação

1. Ratificar que a DÉLIA exibirá sempre as quatro categorias no rail como affordance visual, mesmo quando seus conteúdos estiverem indisponíveis, ou ocultará categorias não autorizadas. **Sem decisão, não congelar matriz final.**
2. Confirmar se Plugins/Aplicações será apenas gateway de navegação ao Portal ou se precisa de uma categoria própria dentro da DÉLIA. A segunda opção exige owner/contrato/aprovação.
3. Congelar a regra visual de posicionamento do toggle, sem criar novo controle dentro do header central.
4. Confirmar o comportamento de projetos/agentes quando ainda não houver contratos: categoria visual com estado unavailable, desabilitada, ou omitida.

O restante (limites de breakpoints, composição técnica e contratos de ação) é decisão técnica bounded **após reanchor canônico**, com QA e owner aprovados.

## 5. Sequência de correção sugerida, sem autorização para implementar

**Doc-only:** um adendo ao 103 com modelo central de estado e matriz de disponibilidade; adendo 104/105/112 para toggle/slot/semântica; adendo 113 com decision tree responsive; revisão 109/110/111 contra inventário canônico antes de definir feeds; matriz de ações por owner. **Depois** submeter um bounded slice de shell visual render-only para aprovação do Product Master, sem criar listas reais/fakes, sem progresso de fase.

## 6. Evidência, limitations e verdict

```text
REVIEW_SCOPE = DOCUMENTS_103_THROUGH_113
REVIEW_SOURCE = GITHUB_MAIN
SOURCE_HEAD_BEFORE_REVIEW = 0b1a2f9044fe32d38c5d89e432eb31be4d5c065f
CANONICAL_FULL_REANCHOR = INCONCLUSIVE
EXISTING_EQUIVALENT_VISUAL = YES
REUSE_DECISION_VISUAL = EXTEND
EXISTING_EQUIVALENT_DATA_CATALOGS = TO_INVENTORY
REUSE_DECISION_DATA_CATALOGS = PENDING_GATE
DOCUMENTATION_VERDICT = REWORK
RUNTIME_TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
INDEPENDENT_RUNTIME_ACCEPTANCE = PENDING
EXECUTION_AUTHORIZATION = NONE
PHASE_PROGRESSION = NONE
```
