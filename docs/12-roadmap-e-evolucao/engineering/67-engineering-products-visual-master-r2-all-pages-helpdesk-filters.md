# 67 — ENGINEERING.PRODUCTS.VISUAL.MASTER.R2 — Padrão visual de todas as páginas de Produtos

**Status:** TARGET / PRODUCT-APPROVED VISUAL BASELINE; a presente especificação **não declara implementação nem deploy** de novos recursos.  
**Data:** 2026-10-30  
**Owner UX:** Portal Engenharia. **Fatos e regras:** API DELPI/TOTVS e demais Domain APIs. **Especialista:** EVA, consumidora governada.  
**Documento-base:** [61 — Produtos UX Master R1](61-engineering-products-visual-ux-master-specification.md).  
**Histórico implementado:** [63](63-engineering-products-contract-inventory-master.md), [64](64-engineering-products-e2e-evidence-report.md), [65](65-engineering-products-ux-routing-fix-evidence.md), [66](66-engineering-products-ux-optimization-evidence.md).  
**Referência nova:** padrão visual e funcional dos filtros avançados e gerenciamento de colunas do **Helpdesk Minha DELPI** mostrado pelo usuário; é referência de comportamento/UX, **não contrato de API nem autorização para importar internals do Helpdesk**.  
**Regra de precedência:** doc 67 refina o visual do módulo Produtos; doc 61 continua autoridade de estrutura, nomes e ownership; docs 63–66 são evidência histórica e contracts já inventariados. Não reescrever histórico.

## 1. Linguagem visual comum

- Identidade do Portal Engenharia atual; usar `@delpi/plugin-ui` e seus componentes oficiais, tokens `--en-*`, PageHero, DataTableSection, RichTree/ProductStructureTree, FilePreviewView, FieldLabel/HelpTooltip, badges, timelines, modais e toolbars. Não copiar o visual antigo do TOTVS.
- Light/dark parity; desktop/tablet/mobile; foco acessível, teclado, leitor de tela e touch. Padrão de ajuda no **texto do label** (hover/focus; touch acessível), não vários '?'.
- Layout compacto sem reduzir a legibilidade ou click targets. Evitar scroll global quando a listagem pode utilizar height disponível, scroll **dentro da tabela**, thead sticky e paginação fora do corpo rolável. Em viewport muito baixo, fallback acessível sem cortar controles.
- Códigos com zeros à esquerda, datas/unidades e valores formatados conforme fonte. Estados distintos: loading, empty, not_found, forbidden, unavailable, not_implemented, contract_error e conflito; não inventar descrições (TOTVS pode entregar `#`/`###`).
- Responsividade e retentividade de estado por URL na navegação; não expor preço, custo, fiscal ou dados comerciais protegidos no contexto Engenharia.
- Mudanças em componentes compartilhados apenas aditivas, default off quando adequado; regressão de consumidores LMPs, NC e Helpdesk.

## 2. Página 1 — Catálogo de Produtos (`/apps/engineering/products`)

### 2.1 Hero e layout
- Breadcrumb Início / Produtos.
- PageHero nativo compacto: eyebrow PORTAL ENGENHARIA; título **Catálogo de produtos**; descrição "Consulte produtos, estruturas, fornecedores, aplicações e desenhos técnicos em um só lugar."
- Busca rápida sempre visível: Código, Descrição, Grupo (multiselect), Tipo (multiselect), Ref. cliente; aplicar automaticamente, com debounce para texto, cancel/ignore de requests obsoletos, `page=1` ao alterar, sincronizar URL, preservar sorting.
- Grupo e Tipo obtidos de `filter-options` oficial, com opções reais. Grupo pode apresentar só código quando descrição oficial não existe; Tipo usa nomenclatura oficial. Nunca usar opções fictícias. Não oferecer Situação como filtro até existir contrato no owner.
- Ação **Limpar filtros** no slot superior direito do hero, **somente quando houver filtro aplicado**, sem reservar altura; limpar filtros rápidos, avançados e URL, zerar draft pendente de debounce.
- Altura hero, breadcrumb, espaçamento entre cards e paddings menores; todos os campos rotulados.

### 2.2 Card da listagem e toolbar — padrão Helpdesk
- Uma linha compacta para título **Catálogo de produtos**, contagem única oficial (total/filtrados claramente identificados), ação **Filtros** (abre painel avançado), ordenação ativa e **Colunas** (abre gestor de colunas).
- Manter a busca rápida no hero; filtros avançados complementam a busca, sem constituir sistemas diferentes de dados. Filtros rápidos e avançados compõem uma **única AST/query state canônica**, traduzida apenas para operadores/fields suportados.
- Resumo/chips discretos dos filtros efetivamente aplicados; remover um chip atualiza pesquisa e URL; não duplicar linhas excessivas acima da tabela.
- Tabela ocupando altura restante, com scroll interno, cabeçalho sticky, paginação fixada fora da área rolável; modo tabela é a prioridade. Se houver modo cards futuramente, somente por demanda explícita.
- Não duplicar contagens nem exibir total estimado como exato.

### 2.3 Gerenciamento de Colunas
- Usar controle **Colunas** nativo/padrão Helpdesk, inventariando o componente concreto e API real do kit antes de reutilizar. Permitir exibir/ocultar e, se suportado, reordenar colunas; manter Código e Descrição visíveis por padrão e preservar navegabilidade.
- Colunas iniciais: Código, Descrição, Tipo, Grupo, Unidade, Situação (somente como campo exibido já oficial; não confundir com filtro), com Referência do cliente opcional conforme contrato.
- **Candidatas opcionais, sujeitas a inventário campo-a-campo:** Subgrupo, Código de desenho, Revisão, Linha de produção, Armazém padrão, Unidade secundária, Código de barras e outros campos oficialmente expostos em `view=engineering`. Não exibir campos sem suporte do payload; não gerar N+1 para preencher colunas.
- Toda coluna precisa de: source-field, label, formatação, null semantics, permissão, sorting support (se houver), largura, truncamento acessível e responsividade.
- Preferências por usuário usando serviço oficial da plataforma, se existente e autorizado; caso contrário aplicar estado local seguro por sessão sem alegar persistência cross-device. Não gravar preferências em banco de outro contexto.
- Ações de configurações acessíveis por teclado, com reset para padrão; mudanças não devem causar perda de filtros/paginação ou fuga de permissão.

### 2.4 Painel de filtros avançados — padrão Helpdesk
- Popover/drawer responsivo ativado por botão **Filtros**, seguindo composição oficial do Helpdesk: título "Filtros avançados", descrição, linhas de critérios e ações **Adicionar critério**, **Limpar**, **Aplicar filtros**.
- Cada critério = `campo + operador + valor(es)`. Renderizar widgets conforme tipo: texto, enum/multiselect, código, data, boolean etc **somente para campos presentes e autorizados**.
- **Campos candidatos**: código, descrição, grupo, tipo, unidade, referência do cliente, situação (somente depois de contrato oficial de filtro), subgrupo e outros campos realmente consultáveis. Exibir somente catálogo de filtros implementados, não filtros decorativos.
- **Operadores candidatos sujeitos a contrato**: contém/começa com/igual para texto, igual/é um de para enum, comparadores de intervalo para campos com source legítimo. Sem operadores livres, regex arbitrária ou SQL.
- Composição padrão `AND` entre critérios de campos diferentes e `OR` para valores da mesma seleção somente **quando a API comprovar essas semânticas**. Não fazer interseção/client-side sobre uma página paginada e alegar busca global.
- Adicionar critério não envia requisição; edição no painel é DRAFT e **Aplicar filtros** promove atomicamente para estado aplicado, sincroniza URL, reseta `page=1`, aborta queries antigas e executa uma consulta. Fechar sem aplicar não promove draft; indicador mostra filtros ativos.
- **Limpar** dentro do painel limpa o draft do painel; comando do hero limpa todos os filtros aplicados. Estabelecer e testar exatamente essa semântica para não induzir perda inesperada.
- Se backend atual aceitar somente query params simples, traduzir critérios suportados por adaptador tipado. Se filtro/operador necessário não existir, Contract Gate com API DELPI owner primeiro; frontend não simula. Não alterar o contrato sem testes.
- Respeitar limites de número de critérios, valores e URL length; se necessário definir representação curta com versionamento/compatibilidade sem armazenar dados sensíveis.
- Popover/drawer: focus trap quando modal, Escape/fechar, restore focus, screen reader labels, cliques fora, mobile responsivo.

### 2.5 Colunas e dados
- Cabeçalho sticky, resize/reorder somente se kit suportar, sorting server-side apenas em campos allowlisted, widths flexíveis. Código navegável para Ficha.
- Desc. `#`/`###` de origem permanece honesta (placeholder contextual sem alterar dado oficial). Badges tipo/status oficiais. Revisão não informada = sem valor, jamais inventar.
- Estados de loading/erro/vazio, contagem e paginação coerentes com filtros; foco e teclado.
- **Critérios centrais:** altura compacta, scroll local, filtros avançados reais + colunas personalizáveis, sem lag/races e sem regressão.

## 3. Página 2 — Ficha do Produto (`/apps/engineering/products/:code`)

### 3.1 Shell, navegação e modo
- Breadcrumb Produtos / código; hero compacto com "Ficha do Produto", código, descrição e badges oficiais de tipo/situação; ações Visualizar (default) e Editar apenas quando contrato WRITE/owner/AuthZ existir. Não colocar falsa edição; pode exibir disabled com motivo.
- Deep links e `?tab=overview|structure|where-used|suppliers|drawings|history`, back/forward, refresh e produto trocado sem stale data. Preservar contexto de listagem quando viável.
- Abas nesta ordem e lazy-load independente, com loading/error/forbidden/not_found separados: Visão geral, Estrutura, Onde é usado, Fornecedores, Desenhos, Histórico.
- Cards compactos, headers informativos, ações contextuais, sem excesso de padding/margens; sem duplicar dados.

### 3.2 Aba Visão geral
- Grupos de leitura: Identificação; Engenharia; Estoque e logística; campos e labels oficiais já implementados. Codificação, tipo, grupo, unidade, código de desenho, NCM, etc, conforme campos permitidos; placeholders honestos.
- Help em labels via kit. Se PA com desenho permitido, card-resumo com link para aba Desenhos; não fazer N+1. Informações comerciais/custo só quando autorizado pelo owner e contexto adequado.
- Exibir revisões, datas e medidas somente como recebidas oficialmente.

### 3.3 Aba Estrutura
- Usar **ProductStructureTree/RichTree** oficial reutilizado; hierarquia expandir/recolher por nó; PA/PI/MP badges; código navegável para ficha do componente; quantidade/unidade e profundidade.
- R2 visual: card com título **Estrutura do produto** e contagem oficial; toolbar Expandir todos/Recolher todos somente se suportada sem perda de performance. Apresentar regiões/colunas visualmente alinhadas para código, tipo, descrição, quantidade, mantendo indentação reconhecível e parent-child claro.
- Melhorar densidade sem achatar árvore; linha de cada nó legível, descrições longas acessíveis e quantidades tabulares no mesmo eixo. Componentes repetidos em ramos distintos não são deduplicados visualmente.
- Estado árvore vazia distinto de unavailable/forbidden; evitar `undefined.length` por validação no API boundary, manter Error Boundary.
- Estrutura de referência para homologação: produto 90264258, multinível, somente dados oficiais.

### 3.4 Aba Onde é usado
- Consulta reversa oficial (parents), sem supor lista global completa se fonte parcial. Reusar RichTree quando representar verdadeiramente relações hierárquicas; alternativamente tabela no padrão do Portal se relações forem planas.
- Código navega para ficha; tipo, descrição, relação, contagem e estado vazio com mensagem precisa; timeout/unavailable não é "nenhuma estrutura".
- Não aplicar filtros inexistentes no owner.

### 3.5 Aba Fornecedores
- Card/tabela compacta com vínculo oficial fornecedor–produto, código fornecedor, nome, part number, lead time quando informado (null ≠ 0), paginação e estados honesto. Não expor custos/preços sem permissão específica.
- Reusar padrões de DataTable; labels/help, navegação e responsividade consistentes.

### 3.6 Aba Desenhos
- Manter desenho automático via **useFilePreviewLoader + FilePreviewView** oficial; load autenticado owner→façade, Blob URL revogada no cleanup, sem token em URL/file share direto.
- R2 visual: **um workspace prioritário para o desenho**: barra/cabeçalho compacto com arquivo, revisão/variante (se existentes), tipo/tamanho/data em metadados secundários; ações Abrir ampliado/Baixar quando autorizadas; **viewer PDF ocupa a maior altura útil**.
- Evitar duas caixas grandes com espacamento excessivo; preview sem clique inicial. Controles zoom/navegação/fullscreen herdados do browser/kit, nunca fingir toolbar custom.
- PDF sem revisão oficial: "Revisão não informada", não inventar; 403/404/unavailable/render-error diferenciados.
- Produto de referência 90264258, arquivo PDF oficial visualizado na captura produtiva do usuário.

### 3.7 Aba Histórico
- Diferenciar histórico real disponível e `revision_history:not_implemented` no owner; renderizar timeline somente para eventos oficiais; datas isoladas não geram eventos inventados.
- View consistente com demais abas; fontes comerciais estritas não são expostas por conveniência.

### 3.8 Modo Editar
- Estado OWNER_BLOCKED atual: sem contrato WRITE; Editar desabilitado com ajuda, não criar formulário editável falso.
- Evolução futura: campos whitelist com owner/autorização live, Save/Cancel, dirty-state, concorrência, auditoria, idempotência e revisão/approval para artefatos técnicos; não reutilizar flag ACT de NC para editar TOTVS.
- Novos controles editáveis só após Contract Gate.

## 4. Padrão Helpdesk: limite de reutilização

- Inventariar **componente concreto** de filtros, operadores, painéis, chooser de colunas e preferências do Helpdesk e respectivos exports/documentação. Preferir `@delpi/plugin-ui`/shared já neutro.
- Não importar componentes, hooks, services ou tabelas internos do bounded context Helpdesk diretamente no MFE Engenharia. Se o padrão ainda for privado ao Helpdesk, extrair contrato neutral com owner e testes somente após Abstraction Gate ou compor com kit existente.
- Preservar separação read/write, authorities e design; UX semelhante ≠ acesso ao banco/permissions Helpdesk.
- Ao adicionar novos filtros oficiais, atualizar `api-delpi`/façade/allowlist EVA `product.search` no mesmo contrato, com testes de parity. A EVA não recebe uma sétima tool.
- Quem não tiver acesso a campo/filtro nunca recebe dados via customização de colunas, URL ou EVA.

## 5. Blueprint de interação e estado

`quickFiltersDraft` (debounced) + `advancedDraft` (aplicado por botão) + `appliedQuery` (único) + `tableColumns` (preferência) + `sort/page` (URL) → contrato de busca governado.

- Uma alteração rápida não deve apagar critérios avançados aplicados; e um Apply avançado não deve perder quick filters.
- URL/copy/deep link devem reconstruir estado aplicado; draft não aplicado pode ficar somente local.
- Limpar global limpa drafts e aplicados simultaneamente, cancela debounce pendente e requisições antigas; retornar `page=1`.
- Mudança de coluna não deve disparar nova busca sem necessidade; persistência de preferências sem extrapolar permissão.
- Guardar limites de query e normalizar opções desconhecidas/descontinuadas com feedback sem quebrar página.
- Buscar em backend (paginação global), nunca fake filtering em `items` já paginados.

## 6. QA visual e funcional obrigatório

- Inventariar padrões Helpdesk/Plugin UI antes de implementar; comparar antes/depois com screenshots de Prod atuais, sem declarar equivalência só por snapshot de build.
- Matriz viewport desktop, tablet e mobile × light/dark. Zoom 125% quando útil.
- Listagem: altura útil, sticky header, scroll interno, paginação, hero compact, filtros rápidos, drawer/popover avançado, seleção múltipla, chips, Apply/Clear, back/forward, query URL, sort, columns visibility/persistence/responsiveness, opções sem fonte, sem dupla contagem.
- Ficha: 6 abas + deep links; árvore multinível colapsável com tipo, unidade, qtde e navegação; PDF realmente renderizado e cleanup; Fornecedores null; Onde é usado timeout; histórico parcial honesto; Editar bloqueado.
- Segurança: 401/403, filtros desconhecidos rejeitados, campos sensíveis nunca expostos, sem N+1/SQL arbitrário, OAuth delegado/EVA parity.
- Regressões em NC, LMPs, Home, Helpdesk, viewer PDF, e MCP semântico. Testar no SHA final; smoke produtivo após deploy, sem writes sobre cadastro oficial.

## 7. Critérios de aceite refinados R2

| ID | Critério |
| --- | --- |
| PRVIS-01 | Hero/catalogo compacto e sem botão Limpar quando sem filtros |
| PRVIS-02 | Toolbar única: título, contagem não duplicada, Filtros, Colunas, sorting |
| PRVIS-03 | Tabela ocupa área útil e scroll próprio; sticky/paginação acessíveis |
| PRVIS-04 | Grupo e Tipo multiselect oficial; busca rápida reativa com debounce seguro |
| PRVIS-05 | Painel avançado estilo Helpdesk usa componentes reais e acessíveis |
| PRVIS-06 | Adicionar/remover critérios e operadores tipados válidos |
| PRVIS-07 | Draft avançado separado de aplicado, Apply atômico, sem requests a cada edição |
| PRVIS-08 | Quick+Advanced combinam sem conflitos; URL e voltar/avançar reconstroem filtros |
| PRVIS-09 | Limpar global cancela drafts/debounce/requests e limpa ambos conjuntos |
| PRVIS-10 | Colunas visíveis/opcionais conforme contract/permission, preferências coerentes |
| PRVIS-11 | Sorting/paging compatíveis com filtros e visibilidade de colunas |
| PRVIS-12 | Células e nulls oficiais, sem dados/colunas inventados |
| PRVIS-13 | Ficha hero + abas ordem e deep links preservados |
| PRVIS-14 | Visão geral compacta, campos agrupados e help em label |
| PRVIS-15 | Estrutura oficial colapsável com leitura clara e ações contextuais |
| PRVIS-16 | Onde é usado coerente com consulta reversa oficial |
| PRVIS-17 | Fornecedores legíveis e sem preço/custo não autorizado |
| PRVIS-18 | Desenhos em workspace compacto, PDF automático autenticado |
| PRVIS-19 | Revisão/proveniência e estados de PDF honestos |
| PRVIS-20 | Histórico oficial ou estado not_implemented explícito |
| PRVIS-21 | Editar depende de contrato WRITE, sem falsa capacidade |
| PRVIS-22 | Light/dark, desktop/tablet/mobile, keyboard/touch, sem overflow |
| PRVIS-23 | Core AuthZ e API DELPI owner; nenhuma elevação por filtros/colunas |
| PRVIS-24 | EVA acompanha toda ação/field filtrável PROVEN sem nova tool |
| PRVIS-25 | Testes no SHA final, browser com SSO e screenshots verificados |
| PRVIS-26 | Deploy SSH Operator e runtime realmente comprovados, rollback disponível |
| PRVIS-27 | Docs 61/63/67/ledger atualizados por gate sem reescrever histórico |
| PRVIS-28 | Bloqueios de contrato identificados como OWNER_BLOCKED, não simulados |

## 8. Implementação incremental recomendada

1. Inventory Helpdesk + Plugin UI (filtros, popover, colunas e preferências) e contrato product search (doc 63).
2. Ajustar card toolbar e gestor de colunas com campos existentes; compactação e responsividade.
3. Implementar filtro avançado com operadores efetivamente suportados, estado draft/applied, URL, limpar e paginação. Estender owner apenas mediante Contract Gate.
4. Refinar as seis abas: estrutura mais clara; PDF workspace; consistência visual de fornecedores/onde-usado/histórico/visão geral.
5. Preservar paridade EVA; executar testes, Playwright, regressão, commit/push e deploy canônico com owner approval.
6. Publicar relatório de execução no próximo número livre (não alterar este doc como se tivesse sido implementado).

**Meta:** uma experiência de Produtos nativa, compacta, configurável, consistente com o Helpdesk, preservando contratos oficiais e a capacidade da EVA de consumir qualquer nova funcionalidade real.
