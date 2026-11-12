# PRC — Especificação visual e de interação: Solicitações e Produtos acompanhados

> **Data:** 2026-11-12  
> **Estado:** UX_DEFINED / TARGET; referência funcional e visual, **não** prova de implementação.  
> **Fonte:** decisões do Product Owner e capturas de tela do Portal Engenharia e Catálogo de Produtos discutidas em 12/11/2026.  
> **Regra de domínio vinculante:** [Registro, versões confirmadas e flags transversais](./PRC-PRODUCT-TRACKING-VERSIONS-TRANSVERSAL-FLAGS-DECISIONS.md).  
> **Sem autorização** para código, migrations, deploy ou alteração de owner.

## 1. Objetivo e referências visuais

Manter **Controle e Cadastro de Produtos** como ferramenta única no Portal Engenharia, combinando tratamento de solicitações e consulta de produtos acompanhados. Reutilizar padrões já conhecidos, sem segunda top bar e sem transformar o acompanhamento no Catálogo TOTVS.

Referências fornecidas:
- **Fila PRC** em `/apps/engineering/product-registration`: hero azul, busca/filtros, sinalizações, seletor Tabela/Cards/Kanban, tabela de solicitações.
- **Catálogo de Produtos** em `/apps/engineering/products`: hero com filtros e tabela de produtos; **Ficha do Produto** em `/apps/engineering/products/:code`: hero de identidade, abas e cards técnicos. Referência de consistência, **não** fonte de dados do acompanhamento.
- **Detalhe de solicitação PRC** em `/apps/engineering/product-registration/:requestId`: cards por seção (Identificação e classificação, Estoque e contabilidade), fornecedores em tabela, ícone de bandeira junto ao label, hover para ação, faixa de acompanhamento técnico e modal de bandeira (Título/Descrição/valor contextual).
- **UPDATE PRC**: comparação Antes/Solicitado apenas dos campos solicitados; preservar esse comportamento na solicitação, sem confundi-lo com ficha completa do produto acompanhado.

Não há design tokens exatos, dimensões, cores hexadecimais ou componentes comprovados por inspeção de código neste documento. **Inventariar o kit e componentes atuais antes de implementar.**

## 2. Mapa de telas e hierarquia

| Tela | Papel | Elementos principais |
|---|---|---|
| Controle e Cadastro de Produtos — Solicitações | Entrada padrão e operação PRC | Top bar global existente; breadcrumb; **hero único**; seletor Solicitações/Produtos acompanhados; filtros PRC; fila e ações existentes |
| Controle e Cadastro de Produtos — Produtos acompanhados | Consulta do conjunto acompanhado | **Mesmo hero** e seletor; filtros próprios; tabela uma linha por produto |
| Detalhe de produto acompanhado — Ficha técnica | Consultar snapshot e gerir flags | Hero de identidade e versão; abas **Ficha técnica / Versões**; seletor de versão; cards técnicos; fornecedores em tabela; bandeiras por alvo |
| Detalhe de produto acompanhado — Versões | Navegar e comparar evolução | Mesmo hero; histórico V1…Vn; origem PRC; comparação de duas versões quaisquer; link para ficha da versão |
| Modal/detalhe de bandeira | Criar ou tratar acompanhamento técnico | Reuso do padrão PRC; campo/vínculo, valor contextual, título, descrição, estado, histórico e ações autorizadas |

Não adicionar menu global, segunda top bar, aba principal Flags, aba principal Fornecedores, nem card separado de flags abertas.

## 3. Página principal: hero único e dois segmentos

**Top bar global e breadcrumb:** permanecem como no Portal. O hero fixo usa o título **Controle e Cadastro de Produtos**, subtítulo breve e seletor segmentado **Solicitações | Produtos acompanhados**, posicionado **dentro do hero, após título/subtítulo e antes dos filtros**. Não usar toggle liga/desliga. O botão **Nova solicitação** aparece no contexto Solicitações; não criar botão Novo produto acompanhado.

**Solicitações (padrão):** preservar busca por número/código/descrição, filtros Status/Tipo, indicador contextual Campos sinalizados, visualizações Tabela/Cards/Kanban, ações e realtime. A alternância não deve descartar estados em edição nem provocar navegação destrutiva.

**Produtos acompanhados:** o mesmo hero muda somente filtros e ações contextuais; busca por código oficial/descrição, filtro de flags abertas e ordenação por última evolução. Tabela inspirada no Catálogo, mas colunas próprias: **Código oficial | Descrição | Versão atual | Flags abertas | Última evolução**; solicitação de origem opcional conforme espaço/contrato. Uma linha por identidade acompanhada; clicar abre detalhe. Sem Kanban obrigatório, sem tabela de todas as versões, sem exibir produtos do catálogo que nunca foram acompanhados.

**URL:** manter deep links de solicitação e Catálogo; definir subrotas próprias do acompanhamento após inventário de router. Alternância deve ser navegável por URL/back-forward/F5. Os caminhos exatos são TARGET, não contratos existentes comprovados.

## 4. Detalhe: hero, abas e ficha

**Hero do detalhe:** código oficial em destaque, descrição da versão identificada, selo textual da versão acompanhada selecionada e data/solicitação de origem quando disponível. Evitar selo de situação oficial TOTVS sem contrato específico. Não exibir botão de edição direta do cadastro oficial. Diferenciar versão de acompanhamento da revisão nativa do ERP.

**Somente duas abas:** **Ficha técnica** (inicial) e **Versões**. Sem Visão geral, Flags ou Fornecedores como abas adicionais.

### 4.1 Ficha técnica

- **Padrão dominante:** cards de seções e campos da ficha PRC atual, com label, valor e ação de bandeira associada ao label. Reutilizar seções técnicas disponíveis no snapshot; não fabricar atributos ausentes. A organização deve seguir a ficha PRC existente, não substituir cards por tabela genérica.
- **Fornecedores:** exceção intencional; tabela com Código, Loja, Razão social, Part Number e Catálogo quando presentes. Flags por atributo/célula do vínculo estável, não por posição da linha.
- **Flags:** bandeira junto ao campo (aberta em vermelho segundo padrão existente); hover no label revela ação, mas teclado/foco e toque precisam oferecer a mesma capacidade. Reutilizar modal **Nova bandeira** e detalhe/tratamento com título, descrição, valor contextual, estado e ações autorizadas. Sem card dedicado de flags abertas. A faixa leve **Acompanhamento técnico**/legenda da PRC pode ser reutilizada sem duplicar dados.
- **Seletor de versão:** na ficha, visível e próximo à identificação da ficha; padrão última versão. Ao escolher V3, atualizar **todos** os valores para o snapshot V3, identificar claramente **Versão histórica — somente leitura dos dados técnicos**. Troca de versão não altera cadastro oficial.
- **Flag atual versus histórica:** na última versão, mostrar flags atuais. Na V3, mostrar as existentes e seu estado no corte da V3, com link/ação explícita para consultar o estado atual. Uma resolução posterior não apaga a marca histórica.
- **Mutação de flags:** possível a partir da ficha atual para usuários autorizados mesmo após fechamento da solicitação, sem gerar Vn+1. Para versões históricas, **proposta TARGET sujeita a ratificação**: consultar histórico e navegar para o alvo atual; criação de nova flag apenas na última versão, com validação de existência do alvo.
- **Conflito:** se há flag OPEN para o mesmo produto/alvo, abrir a flag existente para tratamento; não exibir um segundo formulário de criação que resulte em duplicata. Backend deve garantir unicidade e conflito concorrente.

### 4.2 Versões

- **Histórico:** V1, V2…Vn, mais recente primeiro; cada entrada indica data, solicitação PRC de origem, tipo criação/alteração e resumo das mudanças efetivamente confirmadas. Uma V1 de primeiro acompanhamento via UPDATE não deve ser rotulada como criação do produto no ERP.
- **Navegação:** ação **Ver ficha desta versão** seleciona Vn e abre Ficha técnica; retornar à lista preserva contexto quando viável.
- **Comparação:** dois seletores **Versão de origem** e **Versão de destino**; aceitar versões não consecutivas, p.ex. V1 × V5. Mostrar somente diferenças comprovadas entre snapshots, organizadas por seção/campo; para fornecedores, inclusão/remoção/alteração por identidade de vínculo. Colunas **Antes | Depois** (ou rótulos Vx | Vy) com valores formatados, sem `[object Object]`.
- **Flags na comparação:** eventos de abertura/resolução/reabertura devem ser apresentados separadamente de alterações do cadastro oficial; não atribuir alteração de flag a mudança de campo TOTVS nem criar versão por flag.
- **Vazio:** se existe apenas V1, histórico consultável e comparação indisponível com explicação, não erro.

## 5. Estados, responsividade e acessibilidade

| Estado | Comportamento esperado |
|---|---|
| Carregando | Skeleton/feedback nos filtros, tabela e cards sem deslocamentos excessivos |
| Nenhum produto acompanhado | Empty state específico: ainda não há produtos registrados por conclusão PRC; não sugerir que o TOTVS está vazio |
| Sem resultado para filtros | Mensagem distinta de ausência global; permitir limpar filtros |
| Snapshot parcial/atributo ausente | `Não disponível` ou `Não informado no cadastro oficial` conforme contrato; nunca inventar valor nem converter objeto em texto bruto |
| Flag sem permissão | Ocultar/desabilitar mutações, manter leitura somente se autorizada; backend retorna 403 quando aplicável |
| Flag alterada em outra sessão | Mostrar conflito e reconciliar dados, preservando texto não enviado quando possível |
| Erro de API/timeout | Erro recuperável com retry; não exibir snapshot antigo como atual sem aviso |
| Versão histórica | Identificação persistente de versão/corte e leitura histórica; sem mutação de atributos |
| Mobile | Hero/seletor e filtros empilháveis; cards responsivos; tabela de fornecedores com overflow controlado e labels legíveis |
| Acessibilidade | Foco visível, navegação teclado, labels de ícones, ações por toque, estado não dependente apenas da cor, diálogo com foco gerenciado |

Reutilizar tema claro/escuro e design system existente. Não fixar tokens novos sem inventário.

## 6. Navegação e contratos de apresentação

- A solicitação concluída pode oferecer **Ver versão do produto**; cada versão aponta para **Ver solicitação de origem**, quando o usuário tem acesso.
- Hero e tabela não são autorização. Leituras e mutações usam Engineering API com AuthZ live e contratos próprios de acompanhamento; catálogo TOTVS não substitui snapshots históricos.
- Realtime, quando existente e autorizado, transporta aviso leve e refetch; não usar socket como source of truth nem interromper formulário/modal em edição.
- Dados de flags exigem identidade estável de produto, alvo FIELD ou SUPPLIER_LINK e referência temporal; ações governadas e auditáveis.
- Reuso de componentes requer **inventário + Abstraction Gate**. Não inferir que componentes compartilhados já existem; evitar importação entre bounded contexts.

## 7. Critérios de aceite visual e funcional

| ID | Critério |
|---|---|
| UX-01 | Uma única top bar e um único hero com seletor Solicitações/Produtos acompanhados; filtros mudam por contexto |
| UX-02 | Solicitações mantém layout, ações e visualizações existentes, sem regressão |
| UX-03 | Produtos acompanhados usa tabela padrão do catálogo, mas só mostra produtos registrados pela Engineering API |
| UX-04 | Detalhe usa hero e **somente Ficha técnica / Versões** |
| UX-05 | Ficha mantém cards técnicos PRC; fornecedores em tabela, sem aba separada |
| UX-06 | Flags aparecem junto aos labels/células, sem card dedicado; hover, teclado e toque funcionam |
| UX-07 | Modal de bandeira reutiliza padrão PRC, com alvo e valor contextual corretos |
| UX-08 | Criar/tratar flag autorizada não altera snapshot nem gera nova versão; flag OPEN existente não duplica |
| UX-09 | V3 mostra dados/flags do corte V3, com indicação histórica e acesso distinto ao estado atual |
| UX-10 | Histórico permite navegar para qualquer versão e comparar duas versões não consecutivas |
| UX-11 | Comparação mostra somente diffs reais, fornecedores por vínculo e eventos de flag em seção separada |
| UX-12 | Empty/loading/error/403/partial, desktop/mobile, teclado, tema e F5/back-forward cobertos |
| UX-13 | Deep links existentes de catálogo e solicitação preservados; nenhuma segunda barra ou aplicativo novo |
| UX-14 | Autorização backend-first e testes de concorrência/conflito de flag sem duplicação |

## 8. Pendências de inventário e decisões

1. Localizar componentes PRC efetivos (cards, campo com hover, flags, modal, tabela de fornecedores, legenda) e tokens do kit; registrar equivalentes antes de criar abstrações.
2. Verificar rotas atuais e compatibilidade de deep links do catálogo e PRC.
3. Validar cobertura do snapshot técnico e a forma de renderizar valores parciais.
4. Ratificar política de mutação de flag a partir de versões históricas, unicidade por produto/alvo, migração D16 e AuthZ por objeto (**ARCHITECTURE_DECISION_REQUIRED** se alterar owner/authority).
5. Definir estados e DTOs de comparação de versões sem inventar dados ausentes; confirmar contratos antes de codificar.
6. Provar visualmente em browser real, desktop/mobile, claro/escuro e acesso por teclado; nesta documentação, **TEST_NOT_RUN**.

**Classificação:** decisões de UX do usuário = **TARGET documentado**; existência/compatibilidade dos componentes, contratos e runtime = **TO_INVENTORY**. Nenhum teste de frontend foi executado nesta tarefa documental.

## 9. Página 1 — Controle e Cadastro de Produtos: composição visual APROVADA pelo PO (2026-11-12)

**Status:** `UX_APPROVED / TARGET_IMPLEMENTATION`. Aprovação funcional/visual do desenho conceitual, **não** implementação ou QA browser.

### Hierarquia fixa

1. **Top bar global do Portal** (host; não duplicar no MFE).
2. **Breadcrumb** com `EngineeringPagePath`.
3. **Um único hero compacto** `EngineeringPageHero`, título **Controle e Cadastro de Produtos** e subtítulo **Gerencie solicitações e acompanhe evoluções confirmadas de produtos.**
4. **Seletor segmentado dentro do hero, logo após título/subtítulo:** `Solicitações | Produtos acompanhados`, via `EngineeringSegmentToggle` do Plugin UI; **Solicitações** é o segmento padrão.
5. **Filtros dentro do próprio hero**, trocando com o segmento, sem segunda barra de cabeçalho.
6. **Conteúdo logo abaixo do hero**, conforme segmento, com estados loading/empty/error e paginação.

### Segmento Solicitações

Preservar o comportamento atual da fila PRC: busca por número/código/descrição, filtro de status e tipo, indicador Campos sinalizados, ação **Nova solicitação** apenas neste segmento, e alternância de visualizações **Tabela / Cards / Kanban**. A mudança de hero não autoriza regressão de realtime, ações, filtros, fluxo ou deep links existentes.

### Segmento Produtos acompanhados

Mostrar **somente** produtos que têm versões confirmadas de acompanhamento na Engineering API; não listar o universo do Catálogo TOTVS. Filtros: busca por **código oficial ou descrição**, estado de bandeiras (**todas/com abertas/sem abertas**), ordenação (**última evolução** como padrão; código; descrição), sempre sujeitos a contrato e AuthZ.

Tabela em desktop com **cinco colunas prioritárias nesta ordem**:

| Código oficial | Descrição | Versão atual | Flags abertas | Última evolução |
|---|---|---|---|---|
| código do snapshot confirmado | descrição do snapshot confirmado | Vn | número de flags OPEN atuais | data da última evolução confirmada |

Sem coluna de status do cadastro oficial TOTVS, sem ação Novo produto acompanhado e sem Kanban obrigatório nesse segmento. Uma linha por identidade de produto acompanhada, não por versão; clique/teclado abre o detalhe, quando autorizado.

### Comportamento responsivo alvo

| Largura viewport | Hero/filtros | Conteúdo e layout | Envelope lateral proposto |
|---|---|---|---|
| Desktop ≥1024px | título, seletor e filtros dentro do hero; busca larga e dois filtros lado a lado quando couber | tabela completa; ações no contexto | 20–24px TARGET |
| Tablet 768–1023px | busca largura total + dois filtros em duas colunas; quebra natural do seletor/ações | tabela com overflow interno controlado | 16px TARGET |
| Celular 320–767px | título, seletor e filtros empilhados; alvos acessíveis por toque | tabela com rolagem horizontal controlada **ou apresentação compacta via componentes existentes do Plugin UI**, a validar na implementação sem perder informação/acesso | 12px TARGET |

Espaçamento entre seções proposto: 20–24px desktop, 16px tablet/mobile (12px apenas em telas muito estreitas, se o kit permitir). **Paddings intrínsecos do hero, tabela e inputs são do Plugin UI e não devem ser sobrescritos por valores arbitrários.** Usar tokens após inspeção. Garantir navegação teclado, foco, contraste claro/escuro, 320px sem overflow da página.

### Navegação e estado

- Alternância de segmentos, filtros, ordenação e paginação representados por estado navegável/URL apropriada, com F5, back/forward e retorno do detalhe preservando o contexto.
- Não descartar dados de formulário em andamento sem tratamento; manter o workflow PRC atual.
- Separar empty state **nenhum produto acompanhado** de **sem resultados para filtros** e de erros 403/API.
- Componentes visuais devem vir do `@delpi/plugin-ui/index` (diretamente ou via façade); **nenhum novo primitivo visual local de Engenharia**.
- O plano [PRC-UI-EXTRACT-01](./PRC-PLUGIN-UI-COMPONENT-EXTRACTION-MIGRATION-PLAN.md) continua com evidência visual e commit final pendentes segundo relatório do executor. Aprovação desta página não libera implementação antes dos gates.

### Critérios de aceite específicos (P1)

1. Uma top bar e um hero; segmentado logo abaixo do título; filtros no hero.
2. Segmento Solicitações padrão e funcionalidade existente preservada.
3. Produtos acompanhados com cinco colunas exatas prioritárias, sem status TOTVS e sem cadastro manual.
4. Busca/filtros/ordenação isolados por contexto; resultado autorizado, paginação e estado de URL consistentes.
5. Layout responsivo desktop/tablet/mobile, incluindo 320px sem overflow de documento, controles acessíveis por teclado e toque.
6. Kit-first: todos os primitivos/visuais compartilháveis importados do Plugin UI; nenhuma duplicação no MFE.

**Página 2 — Ficha técnica:** aprovada pelo PO e detalhada na seção 10 abaixo.

## 10. Página 2 — Detalhe do produto acompanhado / Ficha técnica — APROVADA pelo PO (2026-11-12)

> **Status:** `UX_APPROVED / TARGET_IMPLEMENTATION` — aprovação do desenho conceitual pelo Product Owner, sem implementação, QA visual ou validação runtime. **Não autoriza desenvolvimento antes dos gates de Plugin UI, persistência e contratos.** A aba Versões ainda receberá detalhamento próprio na Página 3.

### 10.1 Hierarquia e navegação

1. Preservar top bar global do Portal; breadcrumb `Controle e Cadastro de Produtos / Produtos acompanhados / {código}`, via `EngineeringPagePath`.
2. Hero único do **produto acompanhado**, via `EngineeringPageHero`, com **código oficial em destaque**, descrição do snapshot selecionado, identificação legível da versão acompanhada (`Vn`), data da evolução confirmada e vínculo para solicitação PRC de origem **quando autorizado**. Não representar a versão como revisão oficial do TOTVS nem exibir informação não disponível no snapshot.
3. Apenas duas abas, `Ficha técnica | Versões`, via `EngineeringTabs`; Ficha técnica inicial. A aba Versões terá especificação de comparação e histórico à parte.
4. **Seletor de versão dentro da aba Ficha técnica, acima dos cards**, inicialmente apontando à última versão. Não criar página separada para V1/V2/Vn: selecionar uma versão atualiza a ficha no mesmo detalhe. O hero permanece identificando o produto e deve atualizar a indicação da versão/descrição de maneira coerente com o snapshot selecionado.
5. Faixa **discreta** de acompanhamento técnico com contagem de abertas/resolvidas e acesso à legenda, sem novo card autônomo de flags.

### 10.2 Ficha técnica: o mesmo padrão PRC existente

- Fonte de apresentação prioritária `PrcTechnicalSheetView` do `@delpi/plugin-ui/index`, **sem passar snapshot confirmado como `draft` por conveniência sem adaptar explicitamente o contrato**. O componente atual é orientado à solicitação PRC; mapear o novo modo de snapshot por contrato e sem regressão em CREATE/UPDATE e Minhas Solicitações.
- Manter **cards por seções**, começando por `Identificação e classificação` e `Estoque e contabilidade`, com os mesmos labels, agrupamentos, ordem e ajuda do padrão PRC. Renderizar outros grupos somente quando representados no contrato e com dados/proveniência disponíveis.
- Em desktop, grade **de duas colunas dentro dos cards** (`.delpi-prc__sheet-grid` comprovada no CSS); cada campo contém label, valor legível e bandeira contextual junto ao label. Valores técnicos são **sempre somente leitura**, inclusive na última versão.
- **Fornecedores na mesma aba, em tabela** com `Código | Loja | Razão social | Part Number | Catálogo`, sem aba própria. A bandeira em atributo precisa corresponder ao vínculo fornecedor+loja+atributo, não ao índice da linha.
- Não criar tab `Flags`, card avulso de bandeiras, edição direta do cadastro, nem segunda ficha visual concorrente à PRC.

### 10.3 Bandeiras: componentes compartilhados e limites

Conforme a migração **PRC-UI-EXTRACT-01 reportada pelo executor**, a apresentação alvo reutiliza `FlagFieldAction`, `FlagSummaryView`, `FlagLegend` e `FlagEditorDialog` do Plugin UI. **Status de disponibilidade runtime ainda condicionado ao aceite/commit da migração**; confirmar export MF no HEAD de implementação.

- Bandeira **azul para adicionar**, **vermelha OPEN** e **verde RESOLVED** conforme o padrão atual. OPEN tem precedência visual. Não depender exclusivamente de cor: label/tooltip/aria e foco/teclado/toque.
- Clique em bandeira existente apresenta e trata **o mesmo registro**, sem duplicação; criação, resolução e reabertura somente quando backend autoriza. O diálogo apresenta contexto do campo/alvo, valor técnico, título, descrição e ações disponíveis, sem editar dados do snapshot.
- Na **última versão**, exibir flags atuais, permitir criar/tratar conforme AuthZ live do objeto. Mudança de flag **não cria Vn+1**.
- Em **versão histórica**, apresentar valores e flags **no corte daquela versão** com aviso inequívoco `Versão histórica — somente leitura dos dados técnicos`; permitir consultar estado atual separadamente. Regra proposta a ratificar: novas flags apenas na última versão, com navegação para o alvo atual antes de mutação.
- Ao trocar versão, atualizar **todos** os cards, vínculos de fornecedores, indicação de versão e flags históricas de maneira consistente; não misturar valores V3 com bandeiras V5.
- O Plugin UI não detém HTTP, autorização, `requestId`, regras de ciclo ou fonte oficial. Engineering API continua autoridade; MFE somente adapta e compõe.

### 10.4 Responsividade e dimensões

| Largura | Composição da ficha | Comportamento de flags/fornecedores | Espaçamento externo proposto |
|---|---|---|---|
| Desktop ≥1024px | Hero de produto; abas; seletor junto ao cabeçalho da ficha; cards largura total, campos em duas colunas | Tabela fornecedor completa, tooltip/foco acessível | 20–24px TARGET |
| Tablet 768–1023px | Hero e metadados com quebra; abas visíveis; seletor junto à ficha; duas colunas de campo enquanto houver espaço | Tabela com overflow horizontal **contido**, sem overflow do documento | 16px TARGET |
| Celular 641–767px | Hero compacto; abas e seletor empilháveis; grade segue comportamento real do kit (2 colunas até 640px) | Ações de flags acessíveis por toque, sem dependência de hover | 12px TARGET |
| Celular ≤640px (inclusive 320px) | **Uma coluna por card** conforme CSS comprovado em `.delpi-prc__sheet-grid`; seletor largura disponível | Fornecedores com rolagem horizontal contida e indicação, labels e botões acessíveis | 12px TARGET |

**Valores CSS PROVEN (Plugin UI):** gap da grade `12px 16px`; label `0.85rem`/peso `600`; `gap:6px` label/ícone; `margin-top:4px` label→valor; tabela de fornecedores `font-size:.85rem` e `padding:6px 8px` nas células; breakpoint `max-width:640px` para uma coluna. Padding interno dos cards, do hero e do modal vem do kit — **não inventar override**.

### 10.5 Estados e critérios de aceite

1. Abrir produto acompanhado mostra identidade, versão atual confirmada e vínculo PRC autorizado, sem status de catálogo TOTVS não contratado.
2. Somente `Ficha técnica` e `Versões`, com seletor de versão **dentro da ficha**; nenhuma rota nova por versão.
3. Cards, grupos de atributos e fornecedor em tabela seguem a composição compartilhada PRC; campos técnicos não editáveis.
4. Flags inline por campo e atributo de fornecedor; azul/vermelho/verde, mouse/teclado/toque, modal do kit e sem duplicação.
5. Selecionar V3 em produto V5 substitui **todo** o snapshot e estado de flags no corte de V3; aviso histórico explícito; consulta ao estado atual separada.
6. Usuário autorizado pode criar/tratar flag no produto atual sem criar nova versão; backend impõe autorização, unicidade, auditoria e conflitos.
7. Desktop/tablet/celular (incluindo 320px), tema claro/escuro, tabelas largas, modal host-contained, teclado, carregamento, empty state, snapshot parcial, 403/409 e F5/back-forward devem ser verificados.
8. Nenhum novo componente visual primitivo/personalizado local; consumir Plugin UI; PRC-UI-EXTRACT-01 necessita fechamento de evidências antes da implementação.

**Página 3 — Versões e comparação:** aprovada pelo PO; ver seção 11.

## 11. Página 3 — Aba Versões e comparação — APROVADA pelo PO (2026-11-12)

> **Status:** `UX_APPROVED / TARGET_IMPLEMENTATION`. Trata-se da segunda aba do detalhe do produto acompanhado, compartilhando hero e identidade com a Ficha técnica. Aprovação de UX **não comprova contratos ou runtime** e **não autoriza desenvolver antes dos gates arquiteturais**.

### 11.1 Estrutura aprovada

1. Preservar **breadcrumb**, **hero do produto** (código oficial, descrição e versão acompanhada) e as duas abas `Ficha técnica | Versões` via `EngineeringTabs`. A aba **Versões** fica ativa, sem criar uma terceira aba ou página independente.
2. Organizar o conteúdo em **duas seções verticais, uma abaixo da outra inclusive no desktop**: **Histórico de versões** e **Comparar versões**. Não dispor as seções inteiras lado a lado, pois a comparação exige largura útil para descrições e vínculos.
3. Utilizar `EngineeringTimeline` ou composição equivalente comprovada do Plugin UI para a linha do tempo; `EngineeringDetailCard` para informações expandidas, `EngineeringActionButton` para ações, selects do kit para comparação e `EngineeringStateBanner`/`EngineeringEmptyState` para estados de UI. **Não desenvolver primitivos ou componentes visuais personalizados dentro do MFE Engenharia.** Confirmar exports e comportamento reais antes da implementação.

### 11.2 Histórico de versões

- **Linha do tempo vertical**, em ordem **Vn → V1** (mais recente primeiro); cada entrada indica **Vn, data/hora de confirmação, tipo da solicitação de origem (criação/alteração, quando aplicável), resumo das alterações e link autorizado para a PRC de origem**.
- Destacar visual e textualmente a **versão mais recente**; o marcador `Atual` significa **última versão acompanhada pela Engenharia**, nunca estado ao vivo do TOTVS.
- Cada entrada pode ser **expandida/recolhida** para apresentar metadados e resumo; usar controles com `aria-expanded`, foco visível e suporte a teclado/toque.
- Ação **Ver ficha desta versão** seleciona a versão correspondente e abre a aba **Ficha técnica** dentro do **mesmo detalhe do produto**; a navegação deve preservar contexto por URL/back-forward/F5 conforme contrato de roteamento.
- A **V1** recebe a descrição **Primeiro acompanhamento confirmado**; quando criada a partir de UPDATE não implica que o produto tenha sido criado no TOTVS.
- Se apenas V1 existir, mostrar histórico normalmente; comparação entre versões fica indisponível com explicação, e não um erro.

### 11.3 Comparação entre quaisquer duas versões

- Dois controles selecionáveis: **Versão de origem** e **Versão de destino**, e ação **Comparar versões**. Permitir comparação não consecutiva (`V1 × V5`, `V2 × V4`), com sentido de origem/destino explícito.
- Ao selecionar a **mesma versão** em ambos os controles, desabilitar a comparação e explicar que é necessário selecionar versões distintas; não inferir diff.
- Apresentar **apenas diferenças realmente observadas** entre os dois snapshots imutáveis, organizadas pelos **mesmos grupos técnicos da Ficha técnica**, preservando labels e formatação do Plugin UI. Em cada campo alterado: **Antes (Vx) | Depois (Vy)**.
- Na comparação de fornecedores, reconhecer o vínculo por **identidade estável fornecedor + loja**, e separar **vínculo adicionado, vínculo removido ou atributo modificado** (p.ex. Part Number, Catálogo). Não comparar por índice de linha nem inventar campos não disponíveis.
- As diferenças entre V1 e V5 representam **diferenças acumuladas dos snapshots**, e **não** devem ser atribuídas à última PRC nem a alterações externas como causalidade comprovada. Mostrar solicitação de origem na entrada de cada versão.
- **Eventos de bandeiras** (abertura, resolução, reabertura) aparecem em seção **separada das mudanças oficiais dos dados técnicos**; evento de flag não cria Vn+1. A consulta histórica não reescreve o estado das flags no passado.
- Em caso de **nenhuma diferença** em atributos com cobertura comparável, apresentar mensagem explícita. Dados não observados/incomparáveis são sinalizados como **não disponíveis/incomparáveis**, nunca tratados como igualdade nem como exclusão. A política de no-op continua sujeita ao contrato de domínio.
- Não comparar contra o estado TOTVS live por padrão; trabalhar exclusivamente com snapshots acompanhados, respeitando AuthZ.

### 11.4 Wireframes textuais aprovados

**Desktop (>=1024 CSS px): seções verticais, valores Antes/Depois lado a lado**

```text
[Portal global top bar — host, não duplicar]
[Breadcrumb: Controle e Cadastro / Produtos acompanhados / CÓDIGO]
┌──────────────────────── HERO DO PRODUTO / Plugin UI ────────────────────────┐
│ CÓDIGO OFICIAL — DESCRIÇÃO                           Última acompanhada V5  │
└────────────────────────────────────────────────────────────────────────────┘
[ Ficha técnica ] [ ● Versões ]
┌──────────────────────── HISTÓRICO DE VERSÕES ───────────────────────────────┐
│ ● V5  Atual · Data/hora · Alteração · PRC origem                  [expandir] │
│ │   Resumo técnico · [Ver ficha da V5] · [Ver solicitação]                  │
│ ● V4  Data/hora · Alteração · PRC origem                         [expandir] │
│ │                                                                          │
│ ● V3  ...                                                                  │
│ ● V2  ...                                                                  │
│ ● V1  Primeiro acompanhamento confirmado                                  │
└────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────── COMPARAR VERSÕES ────────────────────────────────────┐
│ [Origem V1 ▼] [Destino V5 ▼]                          [Comparar versões]    │
│ Identificação e classificação                                              │
│ Descrição                                                                  │
│ ┌──────────────── Antes · V1 ───────────────┐ ┌──── Depois · V5 ──────────┐ │
│ │ valor confirmado                         │ │ valor confirmado          │ │
│ └──────────────────────────────────────────┘ └───────────────────────────┘ │
│ Fornecedores                                                               │
│ Fornecedor+loja — [Adicionado/Removido/Alterado]                            │
│ ── Eventos de bandeiras (linha separada, não são dados TOTVS) ──────────── │
└────────────────────────────────────────────────────────────────────────────┘
```

**Tablet (768–1023 CSS px): seções verticais de largura total**, timeline acima da comparação; pares Antes/Depois lado a lado somente se couber sem cortar textos, caso contrário empilhados.

**Mobile (320–767 CSS px): seções verticais, campos Antes/Depois empilhados**

```text
[Hero produto compacto]
[Ficha técnica | ● Versões]
┌──────── HISTÓRICO ────────┐
│ ● V5 · Atual              │
│ │  [Expandir]             │
│ ● V4                      │
│ ● V3                      │
│ ● V2                      │
│ ● V1 · Primeiro acomp.    │
└───────────────────────────┘
┌──── COMPARAR VERSÕES ─────┐
│ [Versão origem ▼]         │
│ [Versão destino ▼]        │
│ [Comparar versões]        │
│ Descrição                 │
│ Antes (V1): valor         │
│ Depois (V5): valor        │
│ Fornecedores              │
│ vínculo e tipo de diff    │
│ Eventos de bandeiras      │
└───────────────────────────┘
```

### 11.5 Dimensionamento e responsividade

| Tela | Hierarquia e grid | Margem externa proposta | Ritmo entre seções |
|---|---|---|---|
| Desktop largo ≥1440px | Histórico largura total **sobre** comparação largura total; em cada diff Antes/Depois em **duas colunas** | 24px `TARGET` | 24px `TARGET` |
| Desktop 1024–1439px | Mesma hierarquia vertical; preservar largura de leitura dos valores | 20px `TARGET` | 20px `TARGET` |
| Tablet 768–1023px | Histórico e comparação em uma coluna; selects e Antes/Depois adaptativos | 16px `TARGET` | 16px `TARGET` |
| Mobile 320–767px | Controles, filtros e pares Antes/Depois **empilhados**; navegação por versão sem hover | 12px `TARGET` | 16px `TARGET` (reavaliar 320px) |

**Paddings intrínsecos, bordas, tipografia, cores e dimensões de botões/cards devem vir dos tokens/componentes reais do Plugin UI**. As medidas externas são referências de composição `TARGET`, não medições do CSS do kit. Não fixar altura de timeline quando expandida; usar fluxo natural. Não criar overflow horizontal de página.

### 11.6 Critérios de aceite específicos (P3)

1. Apenas duas abas no detalhe, sem top bar extra; versão e produto identificados com clareza.
2. Histórico **sempre acima** da comparação, inclusive em desktop, ambos com largura total.
3. Timeline Vn→V1, versão atual identificada e entradas expansíveis acessíveis por teclado/toque.
4. Link **Ver ficha desta versão** abre Ficha técnica com Vn selecionada e URL/back-forward/F5 coerentes.
5. V1 descrita como primeiro acompanhamento, mesmo quando oriunda de UPDATE.
6. Dois seletores permitem comparar versões **não consecutivas**; mesma versão bloqueia comparação com explicação.
7. Diff agrupado como ficha PRC, com Antes/Depois lado a lado em desktop e empilhados no celular.
8. Fornecedores comparados por fornecedor+loja; adição, remoção e alterações de atributos distinguíveis.
9. Eventos de flags exibidos separadamente e não contam como nova versão de produto.
10. V1 isolada, ausência de mudanças, valores parcialmente observados, loading/empty/error/403, acessibilidade e responsividade 320–1920px contemplados.
11. Componentes visuais somente do Plugin UI; integração/contratos, AuthZ e causalidade permanecem no owner correto.

**Estado de execução:** `TEST_NOT_RUN`. **Próximo passo:** consolidar a especificação das três páginas como pacote para implementação, condicionado aos gates de arquitetura, contratos e aceite da migração Plugin UI.
