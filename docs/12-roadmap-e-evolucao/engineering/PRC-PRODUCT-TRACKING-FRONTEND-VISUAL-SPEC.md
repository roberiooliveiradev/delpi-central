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

**Próximo desenho a fechar:** Página 2 — Detalhe do produto acompanhado, aba **Ficha técnica**. Não antecipar sua aprovação.
