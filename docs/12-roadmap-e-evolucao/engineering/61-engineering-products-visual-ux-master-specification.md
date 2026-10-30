# ENGINEERING.PRODUCTS.UX.MASTER.R1 — Produtos: listagem, ficha, abas, desenhos e EVA

- **Status:** TARGET — especificação de produto/UX aprovada conceitualmente; **não representa implementação ou deploy**.
- **Data:** 2026-10-30
- **Owner da experiência:** Portal Engenharia.
- **Owner dos fatos, contratos e regras:** Domain APIs/sistemas oficiais (incluindo TOTVS via API DELPI, conforme contratos existentes).
- **Especialista:** EVA, consumidora governada das mesmas capacidades oficiais.
- **Referências visuais:** Home, Visão Geral, LMPs e NC do Portal Engenharia; screenshots de TOTVS Produtos listagem, cadastro e indicadores/fornecedores fornecidos pelo usuário. Os screenshots são referência de informação, **não** de aparência.
- **Trilha:** docs/12-roadmap-e-evolucao/engineering; alinhamento aos docs 51–60, especialmente 54–58 (MCP semântico) e 52/59 (padrão UX NC).

## 1. Decisões de nomenclatura e navegação

| Elemento | Nome aprovado |
| --- | --- |
| Entrada no catálogo/menu | **Produtos** |
| Título da listagem | **Catálogo de produtos** |
| Detalhe | **Ficha do Produto** |
| Ações de detalhe | **Visualizar** (padrão), **Editar** (somente quando existir contrato WRITE e autorização) |
| Ícone | **Package**, da biblioteca oficial |
| Padrão | Hero da plataforma → filtros/busca → tabela; ficha com hero compacto → abas → conteúdo orientado à tarefa |
| Objetivo | Ponto de acesso progressivo a cadastro, estrutura, uso, fornecedores e desenhos oficiais |

Nome amplo de propósito; não denominar "Cadastro TOTVS" nem "Produtos de Engenharia", para comportar novas capacidades sem renomear. Breadcrumbs sugeridos: Produtos / Ficha do Produto / código. Registrar acesso e favoritos pelo catálogo oficial do Portal, sem duplicar navegação.

## 2. Princípios visuais transversais

1. Usar **design system nativo** do Portal e `@delpi/plugin-ui`: cores e tipografia existentes, bordas discretas, cartões, tabelas, badges, empty states, ícones e espaçamentos já adotados na Home/Visão Geral/NC. Azul de destaque do Portal, sem tema ou CSS paralelo.
2. Light/dark parity; desktop, tablet e mobile; sem overflow da página inteira, layout adaptável e tabs navegáveis por teclado/touch.
3. Informações densas divididas por intenção e abas, em vez de reproduzir as dezenas de campos horizontais do TOTVS.
4. Help contextual diretamente no **texto do label** via hover/focus e alternativa acessível em touch, sem fileira de '?' redundantes (padrão NC).
5. Estados distintos: loading, vazio verdadeiro, indisponível na fonte, sem permissão, não implementado, erro e conflito. Não substituir falha por "sem dados".
6. Dados e indicadores sempre da fonte oficial; sem recomputar no frontend, sem inventar revisão, material, tolerância, norma, fornecedor ou quantidade.
7. A listagem é para **encontrar**; a ficha é para **compreender e agir**. A edição é opt-in e limitada aos campos cujo owner disponibilize WRITE oficial.

## 3. Página A — Produtos / Catálogo de produtos

### 3.1 Hero
- Eyebrow: PORTAL ENGENHARIA.
- Título: **Produtos**.
- Descrição: "Consulte produtos, estruturas, fornecedores, aplicações e desenhos técnicos em um só lugar."
- Ícone canônico: Package.
- Atalhos/capacidades: Catálogo, Estruturas, Fornecedores, Desenhos — exibir como navegação contextual apenas se houver rota/capacidade real; não criar links mortos.
- Indicadores ou contagens no hero somente se o backend oferecer métricas oficiais; nenhum número demonstrativo em produção.
- Ações de cadastro, importação ou administração **não são presumidas**; expor apenas após contrato, permissão e UX próprios.

### 3.2 Busca e filtros
- Busca unificada por código, descrição e referências oficialmente pesquisáveis; debounce, Enter e limpar; sincronização com URL onde o padrão do Portal suportar.
- Filtros planejados: tipo (PA, PI/intermediário, MP e demais tipos reais), grupo, situação; mostrar somente filtros suportados pelo contrato da API.
- Chips/resumo de filtros ativos e opção "Limpar filtros".
- Paginação, ordenação e limites **server-side**, definidos pelo owner. Não carregar todo o cadastro no MFE para filtrar localmente.
- Estado inicial útil e limites de resultados para consultas amplas. Mensagens claras quando busca não retornar dados.

### 3.3 Tabela
- Colunas iniciais: **Código**, **Descrição**, **Tipo**, **Unidade**; grupo e situação como colunas adicionais condicionais ao contrato e espaço.
- Código ou linha abre Ficha do Produto; navegação por teclado e foco visível.
- Tipo em badge discreto; descrição truncada com acesso completo; dados ausentes identificados honestamente.
- Cabeçalho semântico, sorting quando disponível, skeleton/loading, empty e error.
- Responsividade: priorizar Código/Descrição/Tipo; reorganizar em linhas/cards no mobile, sem scroll horizontal global; manter ações acessíveis.
- Não fazer N+1 de estrutura, fornecedores ou desenhos para compor a listagem; dados avançados carregam sob demanda na ficha.
- As linhas vistas nos screenshots TOTVS (ex.: código 10010001, produto cabo, tipo MP, unidade MT) servem **somente como exemplos de referência**, não como dados sincronizados ou prova de API.

### 3.4 Ações e estados
- Visualizar ficha (operação inicial).
- Favoritar/últimos acessos usando recursos de navegação oficiais, se existentes.
- Editar na listagem apenas quando fizer sentido e houver contrato; preferencialmente entrar na ficha primeiro.
- Não expor ações mutáveis sem confirmação de contratos, RBAC e postconditions.

## 4. Página B — Ficha do Produto / detalhe

### 4.1 Cabeçalho e hero compacto
- Breadcrumb Produtos → Ficha do Produto; código como identificação principal e descrição completa logo abaixo.
- Badges: tipo (PA/PI/MP conforme cadastro oficial), grupo, origem oficial; disponibilidade e revisão apenas quando comprovadas pela fonte.
- Ações: **Visualizar** (padrão); **Editar** condicionado a política, entidade, campo e autorização; voltar à lista; abrir desenho somente quando disponível/permitido.
- Reutilizar FieldGrid/Detail componentes oficiais; preservar formatos de data, unidade e códigos; exibir referências e timestamps somente da fonte.

### 4.2 Abas e ordem proposta
1. **Visão geral** — identificação, classificações, descrições e informações cadastrais autorizadas.
2. **Estrutura** — BOM/estrutura hierárquica, níveis, componentes, quantidades e unidades quando houver fonte oficial; estado "sem estrutura" para MP quando adequado.
3. **Onde é usado** — consulta reversa: produtos/estruturas superiores que utilizam o código. Requer inventário do contrato oficial; nunca derivar globalmente de amostra parcial como se fosse completo.
4. **Fornecedores** — vínculos produto-fornecedor, códigos de referência, nome, filial, dados autorizados e status; incluir outras colunas somente conforme owner e contratos.
5. **Desenhos** — desenho(s) e documentos oficiais, revisão/proveniência, visualização, download somente se autorizado. Prioridade de descoberta para PA.
6. **Histórico** — revisões e alterações com timeline nativa, se existir histórico oficial; não sintetizar trilha a partir de datas isoladas.

Abas com lazy loading e estados independentes. Disponibilidade por tipo e contratos: aba pode apresentar explicação honesta de não disponibilidade; não declarar uma ação PROVEN antes do backend. Novas abas entram apenas por demanda comprovada, owner, contrato e testes.

### 4.3 Visão geral — agrupamentos
- **Identificação**: código, descrição, grupo, tipo, unidade, NCM e referência cliente/código de desenho quando oficialmente disponíveis.
- **Classificação/cadastro**: linha, subgrupo, status, unidade/armazenagem e demais campos de interesse real; visibilidade com base em contexto e acesso.
- **Dimensões/especificações**: somente se o domínio publicar dados verificáveis; não inferir de descrição.
- **Atalhos contextuais**: abrir estrutura, aplicações, fornecedores, desenho.
- **Para PA com desenho encontrado:** card-resumo do desenho, com revisão e preview quando suportados, levando à aba Desenhos. Para outros tipos, documento também pode aparecer se houver fonte — não bloquear por tipo artificialmente.

### 4.4 Estrutura
- Hierarquia expandível com nível, componente, descrição, quantidade e unidade **somente se comprovados**; distinção entre estrutura parcial e completa.
- Navegação para ficha de componentes, profundidade/limite, paginação ou carregamento incremental conforme contrato.
- Sem alterar BOM, quantidades ou revisões na V1 de consulta. Edição de estrutura é um workflow específico governado, não resultado automático de habilitar "Editar".

### 4.5 Onde é usado
- Busca reversa dos produtos superiores e aplicações; distinguir ligação direta e indireta se a fonte suportar.
- Exibir códigos, descrições, vínculo/nível e unidade, conforme contrato; links para ficha.
- Se não existir API oficial, registrar **TO_INVENTORY/PLANNED**, sem SQL ad hoc em banco alheio.

### 4.6 Fornecedores
- Tabela de amarração produto × fornecedor baseada em fonte oficial (como a área "Amarração Produto x Fornecedor" observada no TOTVS).
- Colunas candidatas: fornecedor, filial, nome, código do produto no fornecedor, referência, status e campos contratuais relevantes. Condições comerciais só com permissões específicas.
- Não assumir editabilidade nem mostrar dados comerciais sensíveis sem autorização.

### 4.7 Desenhos e file server
- Referência de integração: rotas já utilizadas pelo **Cockpit do Operador** para buscar desenhos no file server. **Inventariar** owner, API/adapter oficial, mecanismo de busca, revisão, autorização, media type, preview e download; não presumir código/endpoint exato.
- Fluxo-alvo: produto/código → contrato oficial → metadados/revisão → documento autorizado → viewer.
- Não montar caminho de share no frontend; sem URL de arquivo arbitrária, bypass do gateway ou acesso direto ao file server pelo MFE/EVA.
- Aba Desenhos: lista/documentos relacionados, tipo, revisão e fonte; viewer PDF/imagem quando suportados, abrir ampliado, download se permitido.
- Para PA: destaque do desenho na Visão geral quando existir. Para MP/PI: permitir documentos disponíveis, sem inventar desenho.
- Estado "não localizado" diferente de "acesso negado" ou "fonte indisponível". Se metadados não incluírem revisão, mostrar "revisão não informada".
- Documento oficial permanece governado; EVA pode interpretar/analisar quando houver contratos reais, mas resultados são análise, não desenho oficial, sem inventar cotas/tolerâncias/normas.
- Previews devem respeitar headers, expiração, cache e auth definidos pelo owner; não embutir token no URL público.

### 4.8 Histórico
- Timeline oficial, evento, timestamp, autor resolvido, resumo e alterações por campo, quando suportado por fonte oficial.
- Avatar oficial apenas para identidade vinculada; fallback textual; nunca inventar usuário.
- Se não houver trilha de auditoria para cadastro de produtos, informar indisponibilidade, não apresentar dados simulados.

## 5. Visualizar e Editar

- **Visualizar** é default, não modifica dados.
- **Editar** só estará funcional para campos com owner, contrato WRITE, validações, autorização e auditoria comprovados. Não reutilizar o ACT de NC como permissão para editar produto.
- Modo de edição: mesmas abas/grupos, inputs apenas em campos editáveis, identificar read-only, validação inline, Save/Cancel, dirty state, saída segura, erros por campo, conflitos de versão, idempotência quando cabível, confirmação proporcional ao risco.
- Edição de estrutura, vínculo fornecedor, revisão/desenho ou publicação técnica é outro workflow: PREPARE/ACT, revisão/aprovação quando necessário; **não** publicar diretamente por mudança simples em formulário.
- Se ainda não houver contrato WRITE de produto, mostrar apenas Visualizar ou Editar desabilitado com explicação. Um protótipo visual não é capability PROVEN.

## 6. EVA — cobertura automática governada das novas capacidades

**Regra de produto:** cada capacidade funcional oficial de Produtos deve ter contrato consumível pelo Portal e registro semântico equivalente na EVA, respeitando seu estágio de prontidão. Não publicar funcionalidade nova no Portal deixando a EVA sem conhecimento do catálogo, **mas** não declarar a ação executável antes de fonte/contrato/AuthZ/teste.

- Superfície MCP existente de seis tools: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`. Não adicionar tool para cada aba.
- Ações semânticas candidatas (nomes ilustrativos, contrato sujeito a G0/G1): `product.search`, `product.detail`, `product.structure` (já há cobertura parcial conforme plano 54), `product.where_used`, `product.suppliers`, `product.drawings`, `product.history`; evolução de `product.update` apenas com autoridade WRITE.
- `get_context` deve reportar ações PROVEN / PLANNED / NOT_IMPLEMENTED com schemas sob demanda; não ampliar AuthZ.
- `read` consulta fatos oficiais; `analyze` só analisa conteúdo recuperado com provenance; `knowledge` apresenta guias versionados existentes; `execute` apenas para alterações autorizadas, com live Core AuthZ, auditoria e postcondition.
- Desenhos: source → percepção/extraction → análise → candidato DRAFT → revisão/aprovação → publicação. EVA nunca vira source of truth do desenho.
- Contratos devem manter owner, consumer, request/response, erros, AuthN/AuthZ, compatibilidade, limites, observabilidade, idempotência e postcondition. Sem integração por DB alheio/cross-context import.
- Integração pode ser progressiva: aba/capacidade sem fonte segue como PLANNED, visível somente de maneira honesta.

## 7. Limites de arquitetura, segurança e ownership

- **Keycloak** identidade/SSO; **Core** app/rota/RBAC; **Portal** host/contexto; **Portal Engenharia** experiência; **Engineering API** contratos próprios de Engenharia; **Domain APIs/TOTVS** fatos e regras de produto; **file server / owner do Cockpit** documentos/desenhos; **EVA** interpretação e execução governada.
- MCP/A2A e prompts nunca concedem autoridade. Live AuthZ no backend, inclusive para reads com restrição; service-to-service somente por contrato técnico apropriado, com usuário preservado quando necessário.
- Domain/Application livres de SDK provider, framework, HTTP e DB; adapters oficiais.
- Não criar espelho de cadastro de produtos, nova verdade concorrente, acesso direto ao banco TOTVS, ou file share pelo frontend.
- Alteração de owner, SoT, bounded context ou autorização: `ARCHITECTURE_DECISION_REQUIRED` antes de implementar.
- Dados de custo, preço, imposto, comercial e fornecedor requerem revisão de escopo e permissão; screenshots TOTVS mostram campos, não autorizam sua exposição.

## 8. Entrega incremental sugerida (não é declaração de implementação)

- **P0 — Contract Inventory:** descobrir rotas oficiais existentes para listagem/detalhe, estrutura, onde-usado, fornecedores, desenho Cockpit, status e edição. Mapear owner, permisos, respostas e gaps.
- **P1 — MVP READ:** entrada Produtos no catálogo; Hero + busca/filtros suportados + tabela; Ficha com Visão geral; Estrutura se fonte atual cobrir; Desenhos PA se contrato reutilizável validado; EVA read/get_context correspondentes.
- **P2 — Abas enriquecidas:** Onde é usado, Fornecedores, Histórico com APIs oficiais quando disponíveis; lazy load e estados de indisponibilidade honestos; sem N+1.
- **P3 — Edição governada:** contratos WRITE por campo/entidade, Core auth, concorrência, auditoria, prévia/aprovação para operações críticas, EVA execute conforme contrato.
- **P4 — Capacidade técnica futura:** novas abas conforme demanda (roteiros, inspeções, qualidade, especificações) após abstraction/contract gate; desenhos candidatos sob owner técnico.

Este plano é de experiência e roadmap, não autorização automática de mudanças de backend/prod.

## 9. Critérios de aceite da especificação/implementação futura

| ID | Critério |
| --- | --- |
| PRD-01 | Menu e títulos Produtos / Catálogo de produtos / Ficha do Produto |
| PRD-02 | Ícone Package e Hero conforme Portal |
| PRD-03 | Busca, filtros, paginação e sorting server-side dentro dos contratos |
| PRD-04 | Colunas essenciais e responsividade sem overflow |
| PRD-05 | Navegação lista → detalhe preservando contexto |
| PRD-06 | Hero compacto, modo Visualizar padrão, Editar governado |
| PRD-07 | Abas na ordem definida com lazy loading |
| PRD-08 | Visão geral agrupa dados reais e ajuda contextual em labels |
| PRD-09 | Estrutura com níveis e quantidade/unidade oficiais |
| PRD-10 | Onde é usado a partir de API reversa oficial |
| PRD-11 | Fornecedores via contrato de vínculos autorizado |
| PRD-12 | Desenhos PA via contrato oficial do Cockpit/file server |
| PRD-13 | Card de desenho na Visão geral quando disponível |
| PRD-14 | Viewer de desenho seguro, revisão/provenance e estados honestos |
| PRD-15 | Histórico via fonte real e timeline oficial, sem simulação |
| PRD-16 | Edição apenas de campos com owner/WRITE/AuthZ/auditoria |
| PRD-17 | Feedback de erros, carregamento, vazio, forbidden e unavailable |
| PRD-18 | Paridade light/dark, desktop/tablet/mobile e acessibilidade |
| PRD-19 | Core AuthZ backend-first; sem exposição indevida de dados sensíveis |
| PRD-20 | EVA catalogada e funcional para cada capacidade realmente PROVEN |
| PRD-21 | Sem N+1, duplicação de fonte ou import entre bounded contexts |
| PRD-22 | Testes contratuais, unitários, integração e browser em SHA final |
| PRD-23 | Screenshots e documentação de evidências por etapa |
| PRD-24 | Deploy/rollback somente após autorização de cada entrega |
| PRD-25 | Não afirmar FULLY_IMPLEMENTED enquanto tabs/edits carecerem de contratos |

## 10. Próximo passo canônico

Executar inventário de código/rotas existentes e das integrações Cockpit/File Server antes de implementar, documentando **PROVEN / TO_INVENTORY / PLANNED / TARGET** por aba. Preservar a especificação acima como baseline de design; mudanças futuras requerem decisão explícita de produto. 
