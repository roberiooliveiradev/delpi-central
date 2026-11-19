# UI-02 — Páginas internas da Pesquisa no Portal Comercial (especificação vigente)

> **Estado:** ESPECIFICAÇÃO VIGENTE, aprovada em 18/11/2026 junto com a maquete. As páginas **já existem em HML**, com o visual anterior. O novo visual segue o [plano de implementação](./UI-02-PLANO-IMPLEMENTACAO.md) e os [pedidos de execução](./UI-02-PROMPTS-DEVIN.md). Nada da Pesquisa vai para PROD sem o gate do [README](./README.md#regra-obrigatória-de-ambientes-e-promoção-decisão-13112026).
>
> **Referência visual:** maquete de seis telas, tema escuro — <https://claude.ai/artifact/7sw5awGxjUydGU7MhzuRUk>.
>
> **Decisões:** [Q24](./BUSINESS-DECISIONS.md#q24--novo-visual-das-páginas-internas-18112026). Este documento substitui o texto anterior, que acumulava decisões datadas de 11 a 13/11/2026. As regras daquele texto que continuam valendo estão incorporadas aqui. O texto integral anterior está no histórico do repositório (commit `ed4ededc6`).
>
> **Autoridades:** TOTVS é a fonte do cadastro de clientes. A `commercial-api` é a autoridade de campanhas, participantes, situação, links, contato do convite, mensagem padrão, permissões e gravação. O MFE `plugins/commercial` apresenta, navega e copia.

## 1. Objetivo, acesso e rotas

**Para que servem as páginas:** o Marketing cria campanhas, inclui clientes do TOTVS, configura uma mensagem padrão por campanha e copia o convite de cada empresa para enviar por conta própria (e-mail, WhatsApp, Teams). As páginas também mostram quem respondeu e quem está pendente. **O Portal não envia mensagens** e não rastreia entrega.

**Quem acessa:** `commercial.marketing` ou `commercial.manage`. Sem essas permissões, a página mostra “Acesso restrito”. A autorização final é sempre da `commercial-api`; esconder um botão não é autorização.

| Tela | Rota no MFE Comercial |
|---|---|
| A — Lista de campanhas | `satisfaction-surveys` |
| B — Detalhe da campanha | `satisfaction-surveys/{campaignId}?tab=participants\|message\|data` |
| C — Detalhe do participante | `satisfaction-surveys/{campaignId}/recipients/{recipientId}` |

**Fora destas páginas:** Resultados (UI-01, UI-05), Respostas por empresa (UI-06) e Detalhe da resposta (UI-07). Os botões “Ver resultados” e “Respostas por empresa” entram junto com essas páginas; até lá não aparecem.

## 2. Princípios visuais

1. **Igual ao restante do Portal Comercial:** trilha, bloco de título (`CommercialPageHero`), quadros (`CommercialSectionCard`), tabela e cards (`CommercialDataTableSection`), avisos flutuantes. Nada de visual próprio da Pesquisa.
2. **Só componentes do PluginUI e wrappers do Comercial.** CSS da página só para layout em `styles/satisfaction.css`. Quando faltar um componente, ele é criado no PluginUI, genérico, depois de passar pela avaliação de nova abstração (ex.: `TokenHighlightField`, P1).
3. **Temas claro e escuro do Portal**, só com tokens. Trocar o tema muda só cores, nunca posição ou espaçamento.
4. **Ações e filtros globais ficam no bloco de título.** Ações de um conteúdo ficam no quadro desse conteúdo.
5. **Linguagem de negócio.** Nada de “escopo parcial”, “etapas A/B”, identificador técnico do questionário ou termos como “placeholder” e “token” na tela.
6. **Sem avisos permanentes que não pedem ação.** Avisos só quando mudam o que a pessoa pode fazer: campanha encerrada, empresa que já respondeu, erro.

## 3. Telas

### 3.1 A — Lista de campanhas

Ordem, de cima para baixo:

1. **Trilha:** “← Portal Comercial / Pesquisa de Satisfação”.
2. **Bloco de título:**
   - etiqueta “MARKETING · PESQUISA DE SATISFAÇÃO” acima do título;
   - título “Configuração das Pesquisas”;
   - descrição “Campanhas, participantes e convites da Pesquisa de Satisfação de Clientes. Os convites são copiados e enviados por você — o Portal não dispara mensagens.”;
   - à direita: “Atualizado em dd/mm/aaaa, hh:mm”, Atualizar e **Nova campanha** (principal).
   - No corpo do bloco, os filtros: **Ano** (Todos + anos), **Situação** (Todas, Agendada, Aberta, Encerrada) e **Pesquisar campanha** (marcador “Nome da campanha”). Os filtros se aplicam sozinhos; “Limpar filtros” aparece quando há filtro ativo.
3. **Quadro “Campanhas”:**
   - barra da tabela no padrão de Clientes: Tabela/Cards, Itens por página (20), Fonte, Colunas e total de registros;
   - **Tabela:** colunas Campanha / período (nome em destaque e período abaixo), Situação (selo), Participantes, Respostas e Taxa de resposta. **Todos os cabeçalhos ordenam.** Números alinhados à direita. A linha inteira abre a campanha;
   - **Cards:** barra “Ordenar por” (campo e sentido) no padrão de `CustomersTable.tsx`. Em cada card: nome da campanha como título, selo de situação, “PERÍODO” com o período e os três números (Participantes, Respostas, Taxa de resposta). O card inteiro abre a campanha;
   - paginação “Página X de Y · N registro(s)”.
4. **Diálogo Nova campanha** (sem mudança de fluxo):
   - campos Nome, Início e Término (data e hora), com a nota “Questionário oficial fixo de 15 perguntas”;
   - Cancelar / Criar campanha;
   - só depois da confirmação da API o diálogo fecha e a campanha criada abre.

**Taxa de resposta:** valor `response_rate` da API, com no máximo uma casa decimal (“60%”, “66,7%”, “100%”), como já é hoje; “—” quando a API não informa. A maquete mostra “60,0%” só como exemplo e não muda essa regra.

### 3.2 B — Detalhe da campanha

**Topo, comum às três abas:**

1. **Trilha:** “← Portal Comercial / Pesquisa de Satisfação / {nome da campanha}”.
2. **Bloco de título:**
   - etiqueta “MARKETING · PESQUISA DE SATISFAÇÃO”, nome da campanha como título e “Janela de resposta: {início} → {término}”;
   - à direita: “Atualizado em…”, selo de situação e Atualizar;
   - **números** no corpo do bloco (`highlights`): PARTICIPANTES, RESPONDIDAS, PENDENTES e TAXA DE RESPOSTA, vindos da API. “Pendente” significa sem resposta registrada, não “não enviado”.
3. **Abas:** Participantes, Mensagem padrão e Dados da campanha (`CommercialUnderlineNav`).
   - A aba aberta fica no endereço (`?tab=`). Sem valor ou com valor inválido, abre Participantes.
   - Trocar de aba cria uma entrada no histórico, para o “voltar” do navegador funcionar.
   - Trocar de aba não grava nada e não apaga a busca ou a seleção em andamento.

**Aba Participantes:**

1. **Quadro recolhível “Adicionar clientes”:**
   - Fechado: “Buscar no cadastro TOTVS e incluir empresas nesta campanha.” e o botão **Adicionar clientes**.
   - Aberto: busca no TOTVS por código ou nome, seleção de várias empresas (mantida entre buscas), Adicionar à pesquisa e Cancelar.
   - O resultado vem por avisos flutuantes (incluídas, já existentes, falhas por empresa) e a lista se atualiza. Não há painel de contadores.
   - Campanha encerrada: o quadro mostra “Campanha encerrada não recebe novos participantes.” e não permite incluir.
2. **Um único quadro “Participantes”**, com tudo dentro:
   - filtros Situação (Todas, Pendente, Respondida) e Pesquisar participante (“Empresa, código/loja ou contato”);
   - barra da tabela;
   - tabela e cards com **exatamente três colunas**:
     - **Empresa:** avatar, nome em destaque e “Código/loja 000232/01” abaixo, com os zeros à esquerda preservados;
     - **Contato:** nome em cima e e-mail embaixo. Sem contato, “Sem contato” em tom secundário;
     - **Situação:** selo Respondida (verde) ou Pendente (amarelo).
   - Todos os cabeçalhos ordenam. A linha ou o card inteiro abre o participante; **não há coluna Ação nem botões na linha**.
   - paginação.

**Aba Mensagem padrão:**

1. **Quadro “Mensagem padrão da campanha”**, com a descrição “Uma única mensagem por campanha. Cada empresa recebe o próprio nome e o link exclusivo ao abrir o participante.”
   - **Assunto do e-mail** e **Mensagem do convite**, os dois com `TokenHighlightField`. `{nome_empresa}` e `{link_pesquisa}` aparecem destacados enquanto se digita.
   - Legenda: “Campos destacados são preenchidos para cada empresa: {nome_empresa} e {link_pesquisa}.”
   - Botões **Inserir nome da empresa** e **Inserir link da pesquisa**: inserem o marcador na posição do cursor (pelo `inputRef`, sem `document.getElementById`).
   - Avisos dentro do quadro, só quando necessários: falta de `{nome_empresa}` ou `{link_pesquisa}`; marcador não permitido (“Use apenas {nome_empresa} e {link_pesquisa}.”); “Alterações não salvas.”; conflito de edição com “Recarregar campanha”.
   - **Rodapé do quadro**, alinhado à direita: Reverter alterações e **Salvar mensagem**. Salvar só depois da confirmação da API, com aviso flutuante “Mensagem padrão salva.”
2. **Quadro “Prévia”**, com a descrição “Como a mensagem chega à empresa, com nome e link de exemplo. O convite real de cada empresa fica no detalhe do participante.”
   - Alternância **Correio eletrônico | Mensageiro**.
     - **Correio eletrônico:** “Assunto:” e a mensagem em HTML seguro, gerado a partir do texto, com `RichTextEditor` em modo de prévia.
     - **Mensageiro:** texto simples com quebras de linha, sem assunto.
   - Empresa e link de exemplo (“Empresa Exemplo”, link `.invalid` que não funciona).
   - **Sem botão de copiar.** A prévia é só para ver.

**Aba Dados da campanha:**

- Quadro “Dados da campanha”, com **Editar dados** no cabeçalho do quadro.
- Grade de leitura:
  - Nome, Janela de resposta e Situação (selo);
  - **Questionário:** “Questionário oficial”;
  - **Versão do questionário:** “Versão de 11/11/2026”, tirando a data do sufixo `@AAAA-MM-DD` de `questionnaire_version`. Sem sufixo válido, mostrar só “Questionário oficial”, sem linha de versão. O identificador técnico nunca aparece;
  - Criada em e Atualizada em.
- Aviso informativo: “As datas não podem ser alteradas depois que alguma empresa responder.”
- **Editar dados** abre o diálogo da campanha (mesmo do 3.1). A API valida e recusa o que não pode mudar.

### 3.3 C — Detalhe do participante

1. **Trilha:** “← Portal Comercial / Pesquisa de Satisfação / {campanha} / {empresa} · {código/loja}”.
2. **Bloco de título:**
   - avatar grande, etiqueta “PARTICIPANTE DA PESQUISA”, nome da empresa como título e “Código/loja {x} · Campanha {nome}”;
   - à direita: “Atualizado em…”, selo Pendente ou Respondida e Atualizar.
3. **Aviso, só quando respondida:** “Esta empresa já respondeu à pesquisa.” A resposta individual não aparece aqui (UI-07).
4. **Quadro “Contato do convite”:**
   - Nome do contato e E-mail do contato (“Não informado” quando vazio), com **Editar contato** no cabeçalho do quadro;
   - o diálogo tem empresa e código/loja só para leitura e os dois campos opcionais. Cancelar não grava; Salvar só depois da confirmação da API. Não altera o TOTVS nem o link.
5. **Quadro “Convite personalizado”:**
   - descrição “Mensagem padrão da campanha com o nome e o link exclusivos desta empresa. Copie e envie por conta própria.”;
   - alternância Correio eletrônico | Mensageiro; assunto (só no correio); mensagem com o nome e o link reais desta empresa; linha “Link exclusivo:” com o link;
   - botões **Copiar mensagem** (principal, no formato da alternância), Copiar assunto e Copiar link;
   - a cópia só é confirmada quando o navegador aceita. Se o navegador recusar, aparece a área “Cópia manual” com o texto selecionável;
   - se a mensagem não puder ser montada: “A mensagem padrão ainda não pôde ser resolvida para esta empresa. Volte à campanha e configure a mensagem padrão.”

## 4. Regras funcionais preservadas

| Regra | Origem |
|---|---|
| Configuração por campanha. A lista de participantes é acumulativa, e incluir mais tarde não muda respostas, links nem o prazo | Decisões de 11/11/2026 |
| Inclusão em lote com resultado parcial: incluídas, já existentes e falhas por empresa | 11/11 e 13/11/2026 |
| Campanha encerrada não recebe inclusão; a API recusa | 11/11/2026 |
| Só dois campos dinâmicos: `{nome_empresa}` e `{link_pesquisa}`. Uma mensagem por campanha, sem links de participante dentro dela | 11/11/2026 |
| HTML da prévia e da cópia gerado de forma segura a partir de texto, sem executar HTML escrito pelo usuário | 13/11/2026 |
| Sem envio, sem “Enviado/Entregue”, sem abrir aplicativo externo | Contrato da primeira entrega |
| Participante é página própria; só Editar contato é diálogo | 13/11/2026 |
| Situação da campanha vem da API (Agendada, Aberta, Encerrada); não existe ativar ou desativar | 11/11/2026 |

## 5. Estados

Cada tela tem estados distintos para carregando, vazio, vazio por filtro, erro com “Atualizar” e acesso restrito, usando `CommercialLoadingCard`, `CommercialEmptyState` e `CommercialStateBanner`. O conteúdo de cada estado é o já existente em `content/satisfactionSurveysContent.ts`, exceto as mudanças da §6.

“Atualizado em” mostra a hora da última leitura feita com sucesso, e “· Atualizando…” enquanto recarrega. É o mesmo comportamento de Clientes.

## 6. Mudanças de texto

| Chave hoje | Mudança |
|---|---|
| `list.partialScope` | **Remover** (lista e campanha) |
| — (novo) `list.eyebrow`, `recipient.eyebrow` | “MARKETING · PESQUISA DE SATISFAÇÃO” e “PARTICIPANTE DA PESQUISA” |
| — (novo) `updatedAt(data)` | “Atualizado em {dd/mm/aaaa, hh:mm}” |
| — (novo) `list.cardPeriod`, `list.sortBy` | “Período” e “Ordenar por” |
| `detail.metricParticipants` | “Participantes” |
| — (novo) `detail.metricResponseRate` | “Taxa de resposta” |
| `message.intro` | “Uma única mensagem por campanha. Cada empresa recebe o próprio nome e o link exclusivo ao abrir o participante.” |
| — (novo) `message.tokenLegend` | “Campos destacados são preenchidos para cada empresa:” |
| `message.unknownTokens` | “Campos não permitidos: … Use apenas {nome_empresa} e {link_pesquisa}.” (sem “Placeholders”) |
| `message.previewSampleNote` | “Como a mensagem chega à empresa, com nome e link de exemplo. O convite real de cada empresa fica no detalhe do participante.” |
| `message.copyPreview`, `message.copiedPreview` | **Remover** |
| `data.fieldQuestionnaireValue` | “Questionário oficial” |
| — (novo) `data.versionFrom(data)` | “Versão de {dd/mm/aaaa}” |
| `data.editHint` | “As datas não podem ser alteradas depois que alguma empresa responder.” |
| `recipient.heroDescription` | “Código/loja {x} · Campanha {nome}” |
| `recipient.responded` | “Esta empresa já respondeu à pesquisa.” |

## 7. Layout, temas e acessibilidade

- **Larguras:** computador 1280 px ou mais; tablet 768 px; celular 360 px. Tabela no computador e cards no celular, igual a Clientes.
- **Números do bloco de título:** a grade compacta do `CommercialPageHero` (`density="compact"`, que já existe no kit) põe os quatro numa linha no computador e dois por linha até 768 px, inclusive no celular. Ajustado em 19/11/2026: a grade compacta substitui o “empilhados no celular” de 12/11, porque dois por linha cabem em 360 px e evitam mudar o kit.
- **Filtros** no bloco de título em grade que se ajusta sozinha. No celular, um por linha.
- **Temas:** conferir claro e escuro em todas as telas. Selos, avisos, destaque de marcadores e números só com tokens.
- **Acessibilidade:**
  - trilha como navegação;
  - abas com `role="tab"` e seleção anunciada;
  - linha e card clicáveis também por teclado (Enter);
  - camada de destaque oculta ao leitor de tela;
  - foco visível;
  - zoom de 200% sem cortar ações;
  - “Atualizado em” com `aria-live="polite"`.

## 8. Componentes por tela

| Tela | Componentes |
|---|---|
| A | `CommercialPagePath`, `CommercialPageHero`, `CommercialSelectField`, `CommercialTextField`, `CommercialClearFiltersButton`, `CommercialActionButton`, `CommercialDataTableSection`, `CommercialDataCardsSortBar`, `CommercialInteractiveDataCard`, `SatisfactionStatusBadge`, `CampaignFormDialog` |
| B | `CommercialPagePath`, `CommercialPageHero` (`highlights`), `CommercialUnderlineNav`, `CommercialSectionCard`, `CommercialDataTableSection`, `CustomerAvatar`, `CommercialStatusBadge`, `TokenHighlightField` (via fábrica do Comercial), `RichTextEditor` (prévia), `CommercialStateBanner` |
| C | `CommercialPagePath`, `CommercialPageHero`, `CustomerAvatar`, `CommercialSectionCard`, `InvitePreview`, `CommercialActionButton`, `RecipientContactDialog`, `CommercialStateBanner` |

## 9. Critérios de aceite

1. As seis telas da maquete reproduzidas no tema escuro, e com a mesma composição no claro.
2. Os ajustes 1–16 da [§4 do plano](./UI-02-PLANO-IMPLEMENTACAO.md#4-catálogo-de-mudanças-o-que-muda-em-cada-tela) cobertos por teste ou por captura de tela.
3. Os fluxos de criar campanha, incluir clientes, editar contato, salvar e reverter mensagem, copiar convite e cópia manual com o mesmo comportamento de antes, com os testes existentes verdes.
4. Aba no endereço: atualizar a página e usar o “voltar” do navegador funcionam.
5. Nenhum CSS de componente novo fora do PluginUI e nenhuma cor literal nova na página.
6. Homologação em HML com o aceite do solicitante; nada em PROD.
