# 51 — Auditoria de lacunas UX das tabelas R01/R02 e R03 — handoff Devin

**Data:** 2026-10-21. **Status:** VISUAL_REWORK=TARGET / RUNTIME_NOT_AUTHORIZED. **Fontes:** capturas reais fornecidas pelo PO das paginas Baixas financeiras e Estoque historico P7, mockups ilustrativos de ambas, relatorio do executor do commit `1390e248c0`, codigo atual e documento 50. Captura nao prova comportamento interativo nem SHA de deploy. O novo documento detalha lacunas; NAO comprova ausencia de implementacao apenas por observacao visual.

## 1. Escopo e regras imutaveis

Dois percursos: `/apps/controllership-finance/closing/financial-settlements` (R01/R02) e `/apps/controllership-finance/closing/stock-inventory` (R03). Seguir instrucoes oficiais, regras .cursor, ADRs, contratos, HEAD, padrao visual, doc 30, 48, 49 e 50. `@delpi/plugin-ui` primeiro; utilizar `DataTableSection` existente, sem copiar dominio do Portal Comercial nem criar nova tabela. Sem mudar backend, SQL, Core, S2S, permissions, segregacao por filial, sem quebrar auto-query, loading, debounce, paginacao server-side ou status de snapshots. So `controllership-finance.access` / `.manage`. Nenhum valor dos MOCKUPS corresponde necessariamente ao ERP.

## 2. Evidencia atual vs referencia

**PROVEN no codigo/relatorio:** `DataTableSection` com toolbar titulo/contagem, itens por pagina, Colunas e Fonte; KPI wrap; baixas com celulas de duas linhas (fornecedor, natureza, movimento), badges de direcao e vinculo; P7 com produto enfatizado e badge neutro de tipo, filial legivel, valores alinhados. Testes 91/91 e estruturais 17/17 relatados pelo executor, NAO reexecutados nesta auditoria. A captura autenticada do PO mostra estes comportamentos visuais (sem validar interacao).

**GAPS visuais em relacao aos mockups:** (a) toolbar ainda pouco expressiva: titulo, contagem e ajustes separados em duas linhas sem agrupamento visual semelhante ao Comercial; (b) ausencia de iconografia/etiquetas de acao no cabecalho da tabela; (c) colunas muito densas e textos compridos, especialmente baixas, demandando avaliacao de min-width, scroll dentro do painel, celulas multi-linha e header; (d) P7 mantem linguagem de lista compacta e tipo em badge neutro, enquanto mockup sugere chips coloridos e acoes por linha — NAO aprovado; (e) nenhuma alternancia tabela/cards nem Excel, pois fora do contrato demonstrado; (f) falta prova visual em tema claro e mobile; (g) comentarios sobre funcionalidade exata do header de ordenacao e paginação exigem teste real. **Nao classificar ausência de Excel/Cards como bug**.

## 3. Matriz de gaps e decisões

| ID | Local | Atual observado/verificado | Referencia visual | Proposta autorizavel sem novo contrato | Classificacao | Evidencia aceite |
|---|---|---|---|---|---|---|
| T01 | Comum, topo da tabela | Titulo acima, count no canto; page size a esquerda, Fonte/Colunas a direita | Header compacto com contagem ao lado do titulo e toolbar alinhada | Reorganizar slots oficiais de `DataTableSection` ou wrapper minimo somente se suporte comprovado; nao duplicar controles | VISUAL_REWORK | desktop e mobile comparados; todos botoes funcionais |
| T02 | Comum, registros | "529 registros" / "7813 registros" em texto secundario | contador tipo pill discreto ao lado de titulo | Reusar badge/chip oficial se possivel; contar a partir da paginação API | REUSE/LOCAL_ADAPTER | valor correto ao filtrar e paginar |
| T03 | Comum, botoes | Fonte - 13px + e Colunas | Toolbar do Comercial com agrupamento e espacamento | Afinar layout, tooltips/foco, tamanhos e overflow; manter apenas acoes existentes | VISUAL_REWORK | navegacao teclado e viewport estreito |
| T04 | Comum, cabecalho | headers densos; ordenacao da pagina via filtros | Icones de sort por coluna no mockup | NAO adicionar sorts visuais onde api nao suporta serverSort por campo; documentar suporte contrato e manter headers honestos | TO_INVENTORY | acao somente se ordena universo global |
| T05 | Comum, export | Sem Excel | Excel no mockup | Avaliar capacidade real, escopo completo, privacidade, API e limites; **nao implementar neste rework** | DECISION_REQUIRED | contrato de export e testes de recorte |
| T06 | Comum, modes | Apenas tabela | Tabela/Cards (e Board no Comercial) | NAO exibir toggle sem renderCard/modelo aprovado, manter futuro | TARGET_FUTURE | decisao PO e plano dedicado |
| T07 | Comum, responsividade | Capturas desktop; barra lateral reduz area visivel | Tabela legivel tambem em tablet e mobile | min-width/scroll interno conforme plugin-ui, prioridades de coluna existentes, sem cortar valor ou deslocar pagina toda | VISUAL_REWORK | 3 viewports e 2 temas |
| T08 | R01/R02 documento/fornecedor | Duas linhas, fornecedor com codigo e loja, muitos chars | Identidade mais escaneavel com icones/avatares | Ajustar hierarquia e quebra sem avatar ficticio nem link inerte | VISUAL_REWORK | nomes e IDs completos, sem troca de campos |
| T09 | R01/R02 natureza/tipo | Codigo em destaque + descricao secundaria | Badge colorido por categoria no mockup | manter codigo e descricao sem cor de negocio inventada; usar badge somente para significado autorizado | REUSE | sem misclassificar BA/VL/ES/CP |
| T10 | R01/R02 direcao/vinculo | Badges ja presentes; codigo cru preservado | chips de status coloridos | refinamento leve de alinhamento/contraste/semantica; manter exatamente side e code reais | VISUAL_REWORK | 401/403 nao mascarado; vinculos ausentes distintos |
| T11 | R01/R02 valor/moeda | Codigo moeda 01; valor sem prefixo inventado | R$ e BRL no mockup | alinhar numeros e preservar codigo da origem; NAO acrescentar R$ sem mapeamento canonical | PROVEN/KEEP | valores sem arredondamento sem prova |
| T12 | R01/R02 links/acoes | sem links por linha | OP/Pedido, menu ... | sem endpoint/ownership/rule: **nao criar** | DECISION_REQUIRED | contrato navegação e autorização |
| T13 | R03 produto/descricao | codigo forte, descricao single line em desktop | tipo colorido e descricao navegavel | preservar descricao, melhorar quebra/espaco; evitar truncamento de produto | VISUAL_REWORK | textos compridos legiveis |
| T14 | R03 tipo/grupo | Badge cinza para MP/II/etc; grupo codigo | chips por MP/PI/PA e grupo nominal | mapa de cores so depois de padrao oficial; grupo nominal so com mapping real; NAO inventar | TARGET_FUTURE | sem atribuir falso status |
| T15 | R03 filial/armazem | separados; filial explicita | armazem em label, filial contextual | preservar chave filial+armazem, alinhar visual | PROVEN/KEEP | nao fundir armazem 01 de filiais distintas |
| T16 | R03 quantidade/valor | direito; formatacao vigente | R$ e barras comparativas | manter precisao/codigo de unidade; NAO adicionar R$ ou % sem contrato | PROVEN/KEEP | crosscheck itens/totais |
| T17 | R03 competencia por linha | sem coluna adicional | competencia em todas as linhas do mockup | competencia ja no filtro e response; adicionar coluna somente apos avaliar valor UX/custo e consentimento PO | DECISION_REQUIRED | evitar coluna redundante |
| T18 | Estados | loading/empty/error via kit; source_missing pode mostrar tabela vazia e aviso | banner proeminente integrado | verificar distincao empty legítimo vs snapshot ausente; mensagem/zero fieis, sem duplicidade | VISUAL_REWORK | test snapshot missing/incomplete/no_matching_items |
| T19 | Acessibilidade | nao comprovada por print | keyboard, foco, zoom, tema claro | testes e verificacao visual; zero controles inertes, header hints acessiveis | VERIFY_REQUIRED | teclado, zoom, 2 temas e 3 viewports |

## 4. Blueprint proposto para a toolbar (nao reimplementar tabela)

Ordem de preferencia: API nativa do `DataTableSection`, usando `toolbarLeading`/`toolbarExtra` apenas se existirem e forem adequadas no HEAD; caso contrario adaptador visual fino, sem duplicar state/paginacao. Layout:

- Desktop: titulo forte + contador adjacente na primeira linha; ferramentas reais (Colunas, Fonte, itens/pagina) agrupadas e alinhadas, sem volume excessivo.
- Tablet: titulo e contador em linha propria, ferramentas com wrap e tab order.
- Mobile: controles em linhas acessiveis; tabela scrola dentro de container, sem scroll horizontal global; respeitar mecanismo responsivo nativo.
- Feedback: `CfLoadingCard` e banners existentes; um unico estado por situacao. Sem fake buttons.
- Headers: indicadores de sort SOMENTE nos campos com ordenacao global comprovada na API; paginacao server-side nao justifica sorting client side de 50 itens.

## 5. Contratos e testes obrigatorios

- BFF continua unica porta da UI. Nenhum novo permission code ou discriminacao de filial.
- API paginada: `recordsCount`/total representam universo do filtro, nao a pagina; pagina 1 quando filtros mudam; retry nao duplica. Data civil timezone correto.
- R01/R02: nao confundir estorno/compensacao com pagamento; moeda 01 nao e BRL sem prova; codigo `paymentDirection` permanece no campo.
- R03: `available` / `incomplete` / `source_missing` / `no_matching_items` distintos; ausencia nao equivale zero; `officialP7:false`.
- Tests: Vitest + estruturais + ESLint + typecheck + build + capturas real desktop/tema escuro e claro, tablet e mobile + smoke filtro/paginacao/toolbar via navegador autenticado. `TEST_NOT_RUN` quando nao executado.
- Evidence ledger: antes/depois por pagina e viewport, classe/componente reutilizado, arquivos, SHA, deploy e smoke separados; evitar conclusao a partir de HTTP 200.

## 6. Execucao em gates e Definition of Done

G0 READ: HEAD/status + instructions + cursor + doc 30/48/49/50/51 + codigo dos producers/consumers/testes. G1 INVENTORY: listar props reais do DataTableSection, diferencas do Comercial e limites contratos. G2 DESIGN: propor diff por T01-T19, recusar features em `DECISION_REQUIRED`; somente arranjo visual e reuse existente pode ir a runtime apos gate transversal explicito. G3 IMPLEMENT: primeiro R01/R02, depois R03, menor diff; nao reabrir hero. G4 VERIFY: testes + prova real; G5 DOCUMENT/COMMIT/PUSH/DEPLOY (somente com autorizacao operacional explicita nesta task, runbook e rollback).

**AC de aceite:** T01-T04 e T07-T10/T13/T18 devem estar comprovadamente melhores; T05/T06/T12/T14/T17 excluidos sem falsos botoes; T11/T15/T16 preservados. Sem output enganoso ou paridade MATR460 inferida. Veredito somente `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

## 7. Entrega inicial exigida do Devin

```text
HEAD_STATUS:
DESIGN_AUTHORITY:
PLUGIN_UI_TABLE_SUPPORTED_SLOTS:
COMMERCIAL_TABLE_REUSE_MATRIX:
TABLE_GAP_T01_T19:
REAL_DATA_CONTRACT_LIMITS:
VISUAL_ONLY_DIFF:
FEATURES_BLOCKED_DECISION_REQUIRED:
TEST_PLAN:
RUNTIME_GATE: PENDING
```
