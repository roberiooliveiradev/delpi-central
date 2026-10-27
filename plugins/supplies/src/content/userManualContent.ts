import { GLOSSARY_CONTENT } from "./glossaryContent";

/**
 * Conteúdo PT-BR do Manual do usuário (página /help) — Portal Suprimentos E4.
 * Espelho markdown completo fica para E16.
 */
export type UserManualLinkRow = {
  want: string;
  where: string;
  how: string;
};

export type UserManualFaq = {
  q: string;
  a: string;
};

export type UserManualSection = {
  id: string;
  title: string;
  intro?: string;
  bullets?: readonly string[];
  links?: readonly UserManualLinkRow[];
  faqs?: readonly UserManualFaq[];
  glossary?: readonly { term: string; meaning: string }[];
};

export const USER_MANUAL_CONTENT = {
  pageTitle: "Manual do usuário",
  pageSubtitle:
    "O que é o Portal Suprimentos, onde ir, dúvidas frequentes e glossário mínimo.",
  backHome: "Voltar ao Início",
  tocTitle: "Nesta página",
  tocAriaLabel: "Índice do manual",
  conceptsTitle: "Conceitos que não misture",
  concepts: [
    {
      term: "Portal vs apps antigos",
      meaning:
        "O Portal reúne as jornadas. Cockpit, SC e estoque de segurança legados continuam no launcher até o cutover.",
    },
    {
      term: "Início vs Visão geral",
      meaning:
        "Início é ação e descoberta. Visão geral é o painel de KPIs do período — só aparece com acesso analítico.",
    },
    {
      term: "Filial no escopo",
      meaning:
        "Dados TOTVS das duas unidades operacionais. A filial na tela é filtro. Sem uso normal do Portal o módulo não abre.",
    },
    {
      term: "Perfil do Portal vs perfil Minha DELPI",
      meaning:
        "O avatar na TopBar abre o perfil do Portal Suprimentos (`/users/:id`). O nome abre o menu com Meu perfil Minha DELPI (`/profile`) e Preferências do Portal.",
    },
  ],
  scopeNote:
    "Sem permissão (403): você não tem uso normal deste módulo. Aliases antigos não abrem o app.",
  sections: [
    {
      id: "want",
      title: "Quero… → vá em…",
      intro: "Use esta tabela como mapa. Atalhos também estão no Início (favoritos, recentes e busca).",
      links: [
        {
          want: "Ver o que precisa de atenção",
          where: "Visão geral e listas operacionais",
          how: "KPIs do período na Visão geral; pendências reais nas faixas Atenção das listas (pedidos atrasados, situações de SC) e em Minhas tarefas",
        },
        {
          want: "Ver indicadores do período",
          where: "Visão geral",
          how: "Filtros Hoje/Esta semana/Este mês… e Unidade (MultiSelect SC/ES); KPIs com Meta parcial ≠ Meta mês quando o SI distingue; Nota IDD do SI",
        },
        {
          want: "Ver OTD com velocímetro",
          where: "OTD",
          how: "Velocímetros por unidade e série no tempo; mesmos filtros da Visão geral. Diferente de Entregas / Atrasos (recebimentos MP no período)",
        },
        {
          want: "Compartilhar o mesmo recorte da Visão geral",
          where: "Visão geral",
          how: "A URL guarda unidade(s), datas e preset — copie o link com o filtro ativo",
        },
        {
          want: "Acompanhar entregas atrasadas",
          where: "Entregas / Atrasos",
          how: "Recebimentos MP por pontualidade; filtre Unidade, período de digitação e Em atraso/No prazo. A URL guarda o recorte (F5). Sem clique no pedido",
        },
        {
          want: "Abrir pedidos de compra (PC)",
          where: "Pedidos de compra",
          how: "Lista linhas abertas; filtros aplicam sozinhos; clique na linha para a ficha. A URL da lista guarda filtros (F5)",
        },
        {
          want: "Ver o detalhe de um pedido",
          where: "Pedidos de compra",
          how: "Abra a linha; cabeçalho com filial, fornecedor, comprador, itens em aberto e atraso; por item: quantidades, preços, recebimentos (NF, série, datas, valor) e SC origem — clique na SC para abrir a ficha dela. Copie o endereço da ficha; F5 a restaura; voltar retorna à lista. Só pedidos em aberto",
        },
        {
          want: "Abrir solicitações de compras (SC)",
          where: "Solicitações de compras",
          how: "Lista no escopo de CC/unidade; filtros automáticos; clique na SC para a ficha; URL guarda filtros (F5); exportação Excel se tiver permissão",
        },
        {
          want: "Ver o detalhe de uma solicitação",
          where: "Solicitações de compras",
          how: "Abra a SC; cabeçalho com identificação, solicitante, centros de custo, aprovação e indicadores (itens visíveis, pedidos vinculados, atraso) — tudo no escopo de CC. Cada item mostra unidade, quantidades, necessidade, aprovação, fornecedor sugerido e conta contábil; depois vêm pedidos vinculados (clique no PC para a ficha dele), recebimentos e o acompanhamento com previsões marcadas. Copie o endereço da ficha; F5 a restaura; voltar retorna à lista com os filtros",
        },
        {
          want: "Alterar unidade padrão ou densidade das tabelas",
          where: "Perfil (avatar na TopBar)",
          how: "Só no próprio perfil; administradores podem ler outros usuários, sem editar prefs",
        },
        {
          want: "Fixar atalhos que uso sempre",
          where: "Favoritos (estrela na TopBar ou nos caminhos)",
          how: "Clique na estrela de um caminho no Início; abra a lista pelo botão Favoritos ao lado da busca",
        },
        {
          want: "Ver estoque de segurança",
          where: "Estoque de segurança",
          how: "Indicadores, déficit por unidade de medida e lista classificada; clique na linha para abrir a página de detalhe do material — na visão Todas as Filiais, escolha a filial antes",
        },
        {
          want: "Consultar o estoque físico",
          where: "Estoque",
          how: "Filtre Unidade e Armazém; consulte saldo físico, UM, custo e valor da posição. A URL preserva o recorte (F5). Inclui saldos positivos, zerados e negativos",
        },
        {
          want: "Consultar item / produto",
          where: "Produtos",
          how: "Busca e ficha 360 quando liberada",
        },
        {
          want: "Identificar fornecedor ou solicitante",
          where: "Pedidos de compra",
          how: "Avatar na lista, nos cards e na ficha — também em Solicitações de compras. Clique no avatar ou no nome do fornecedor para abrir a ficha cadastral (E14); clique no avatar ou no nome do solicitante para abrir o perfil do usuário no Portal — quando a pessoa tem vínculo com a Minha DELPI e você tem acesso",
        },
        {
          want: "Consultar fornecedor",
          where: "Fornecedores",
          how: "Busca por código, loja, razão social, fantasia ou documento; clique na linha para abrir a ficha cadastral",
        },
        {
          want: "Comparar cadastro com fonte externa",
          where: "Fornecedores → ficha → Enriquecimento cadastral",
          how: "«Consultar dados externos» compara a ficha com dados públicos do CNPJ (BrasilAPI — só sugestão). Aceite ou rejeite por campo, use seleção em lote e «Preparar atualização» gera apenas um rascunho — nada é gravado no Protheus",
        },
        {
          want: "Verificar a integração REST de fornecedores",
          where: "Fornecedores (perfil de administração)",
          how: "O widget «Integração Protheus», no canto inferior direito, mostra configuração, conectividade, autenticação e consulta REST em tempo real, além das liberações de inclusão e alteração. Expanda para os detalhes, recolha ou feche pelo «×» — reabra pelo botão flutuante. A verificação é somente leitura — nada é gravado no ERP",
        },
        {
          want: "Acompanhar pedidos em aberto",
          where: "Pedidos de compra",
          how: "Saldo pendente de recebimento; para pontualidade de recebimentos já digitados use Entregas / Atrasos",
        },
        {
          want: "Fila pessoal",
          where: "Minhas tarefas",
          how: "Acompanhamentos atribuídos a você",
        },
        {
          want: "Administrar escopos",
          where: "Administração",
          how: "Só com permissão de administrar o Portal",
        },
      ],
    },
    {
      id: "screens",
      title: "Mapa das áreas",
      bullets: [
        "Início — saudação com o primeiro nome da sessão, busca, favoritos, últimos acessos e caminhos por capability. O Início abre rápido: pendências operacionais ficam nas faixas Atenção das próprias listas e na Visão geral.",
        "Visão geral — indicadores consolidados do período e das unidades selecionadas; itens operacionais em Solicitações e Operações.",
        "OTD — velocímetros de pontualidade e evolução; abra pelo Início, catálogo Análises ou CTA da Visão geral.",
        "Pedidos de compra — itens com saldo pendente de recebimento no recorte; hero com linhas/valor/atrasadas; Atenção Todos(N)/Atrasados(N) do resumo do servidor; filtros automáticos, Atualizar; Unidade como Santa Catarina / Espírito Santo; clique no PC para a ficha. Distinto do OTD de pontualidade e de Entregas / Atrasos.",
        "Entregas / Atrasos — recebimentos de matéria-prima (MP) já digitados, classificados em Em atraso ou No prazo. Período = data de digitação/entrada. Sem clique no pedido (histórico ≠ PC aberto).",
        "Estoque — posição física atual por produto, unidade e armazém, incluindo saldos positivos, zerados e negativos. Não calcula saldo disponível e não é estoque de segurança.",
        "Estoque de segurança — materiais com estoque de segurança parametrizado no ERP: indicadores do recorte, déficit por unidade de medida e lista ordenável com os quatro status. Clique na linha para a página de detalhe do material (saldos, cobertura, pedidos/SCs/empenhos em aberto, projeção, consumo e fornecedores); na visão Todas as Filiais, o Portal pede a escolha de Santa Catarina ou Espírito Santo. Distinto de Estoque (posição física) e de Produtos (ficha cadastral).",
        "Inteligência de mercado — cotações históricas de metais e câmbio de fontes autorizadas (World Bank Pink Sheet e Banco Central PTAX), com USD nativo e conversão BRL pela média PTAX do mês. Mostra fonte, licença e estados de dados (parcial, desatualizado, sem dados) — nunca inventa valores.",
        "Solicitações de compras — acompanhamento global no período; o hero conta SCs e a faixa Atenção filtra a situação sem ser uma permissão. Clique na SC para a ficha; exportação Excel faz parte do uso normal.",
        "Operações — agrupamento do Início que reúne pedidos, entregas, fornecedores, produtos, estoque físico e estoque de segurança. Na barra de navegação, «Pedidos de compra» abre diretamente a lista de pedidos.",
        "Indicadores / Negociações — recorte analítico quando liberado.",
        "Administração — mappings e configurações.",
        "Perfil — avatar na TopBar abre o perfil deste Portal; Meu perfil Minha DELPI e Preferências ficam no menu do nome.",
        "Ajuda — este manual, FAQ e glossário.",
      ],
    },
    {
      id: "safety-stock",
      title: "Estoque de segurança",
      intro:
        "A página Estoque de segurança mostra os materiais com estoque de segurança parametrizado no ERP e quanto falta para atingir esse nível. Classificação, saldos, déficit e projeção são calculados pelo servidor — o Portal apenas exibe.",
      bullets: [
        "Objetivo — responder «quais materiais estão abaixo do nível de segurança e quanto falta comprar», por filial e por recorte de filtros.",
        "Filial — selecione Santa Catarina, Espírito Santo ou Todas. «Todas» é uma única consulta consolidada, não a soma de duas buscas. Filial é filtro de dados, não permissão.",
        "Filtros — situação, grupo de produto, unidade de medida, busca por código/descrição e os as opções «Incluir materiais bloqueados» e «Incluir materiais sem estoque de segurança». Aplicam automaticamente e ficam na URL (F5 restaura o mesmo recorte).",
        "Indicadores — o topo mostra totais do recorte: materiais, com/sem estoque de segurança e quantos estão abaixo, no nível ou acima. Quando um dado está indisponível aparece «—», nunca zero falso.",
        "Os quatro status — Sem estoque de segurança (sem estoque de segurança definido), Abaixo (saldo disponível menor que o estoque de segurança), No nível e Acima. O rótulo sempre acompanha a cor.",
        "Indicadores clicáveis — os seis cartões do cabeçalho filtram a lista com um clique. «Materiais» mostra tudo; «Com estoque de segurança» mostra os que têm parâmetro definido (abaixo, no nível ou acima); os outros equivalem ao filtro Status — mudar um altera o outro. Filial, grupo, UM, busca e ordenação são preservados.",
        "Déficit por unidade de medida — quanto falta comprar para repor o estoque de segurança, agrupado por UM. Só compare quantidades da mesma unidade.",
        "Ordenação e paginação — clique no título da coluna para ordenar (nove campos disponíveis); a ordenação vale para o recorte inteiro, não só a página atual, e fica na URL.",
        "Detalhe do material — clique na linha ou em «Ver detalhes» para abrir a página própria da ficha do item naquela filial: identificação, saldos por armazém, cobertura do déficit, pedidos de compra, solicitações e empenhos em aberto, projeção de estoque, consumo mensal/anual e fornecedores vinculados. Na visão Todas as Filiais, escolha Santa Catarina ou Espírito Santo antes de abrir. O link «Estoque de Segurança» no topo volta à lista com os mesmos filtros.",
        "Cobertura — quanto do déficit já está coberto por pedidos de compra elegíveis; «Falta comprar» é o restante calculado pelo servidor.",
        "Projeção — extrato cronológico do saldo: posição inicial, entradas de pedidos e saídas de empenhos. Ruptura é o primeiro saldo projetado negativo.",
        "Fornecedores vinculados — fornecedores do material com dados da última compra; a identidade é código + loja do fornecedor.",
        "Atualizar — o botão Atualizar recarrega filtros, resumo e lista mantendo o recorte; o horário exibido é da última consulta bem-sucedida.",
        "Sem resultados — a lista vazia é um resultado legítimo do recorte: ajuste os filtros ou use Limpar. Não confunda com erro.",
        "Erros e acesso — falhas aparecem como aviso explícito com opção de tentar novamente; uma seção pode falhar sem derrubar as demais. Sem uso normal do módulo a página não abre (403) — peça o acesso ao administrador.",
      ],
    },
    {
      id: "market-intelligence",
      title: "Inteligência de mercado",
      intro:
        "A página Inteligência de mercado reúne indicadores históricos usados nas análises de compra, em três perspectivas exclusivas. Os dados vêm de fontes externas autorizadas, ingeridos pelo serviço de dados externos da plataforma — a página nunca consulta a internet diretamente.",
      bullets: [
        "Perspectivas — o topo alterna entre Metais (seis instrumentos do catálogo), Câmbio (PTAX do Banco Central) e Indicadores (IPP do IBGE e importações Comex Stat por NCM homologada). Só uma perspectiva é exibida por vez e a troca não recarrega a página.",
        "Metais — cartões de Cobre, Alumínio, Zinco, Níquel, Chumbo e Estanho, cada um com ícone, unidade e base da cotação (fechamento COMEX/LME, spot ou média mensal). A seleção é múltipla e prepara o histórico e a comparação, mas nunca libera cotações: um metal sem fonte homologada mostra «Fonte pendente» e nenhum valor — e, quando selecionado, é nomeado em um aviso com o motivo.",
        "Unidades — cada card, tabela e legenda mostra a unidade nativa legível (US$/t, US$/lb, R$/US$, Índice ou %); séries com unidades diferentes nunca são somadas nem comparadas — o gráfico de metais agrupa as séries por unidade.",
        "Indicadores — IPP do IBGE para Metalurgia (número-índice dez/2018=100 ou variação mensal — índice, não cotação) e importações Comex Stat por NCM homologada (valor FOB, peso e valor médio em US$/t — referência de custo, não cotação internacional). Sem NCM homologada, a perspectiva mostra a configuração pendente, os próximos passos e a prévia dos indicadores que serão exibidos.",
        "Comex configurável — dentro de Indicadores, a aba Comex oferece duas origens: «Produtos DELPI» pesquisa itens reais do cadastro (matéria-prima, intermediário ou acabado) e mostra a NCM fiscal de cada um; «Consultar NCM» aceita o código de 8 dígitos diretamente — pontos, espaços e vários códigos de uma vez são normalizados. Somente NCMs aprovadas entram na análise; pendentes podem ser solicitadas na própria tela e aguardam decisão de quem governa a classificação fiscal. Selecionar vários produtos que usam a mesma NCM nunca duplica o valor de importação.",
        "Visualizações salvas — é possível salvar a análise Comex como uma visualização pessoal (produtos, NCMs, período, granularidade e modo) e reabri-la depois; cada usuário vê, edita e exclui apenas as suas.",
        "Câmbio — PTAX de fechamento (venda ou compra). Dias úteis sem boletim permanecem ausentes; se a fonte estiver indisponível, um aviso explica a falha e cartões compactos mostram a última tentativa de coleta, a última observação persistida e a cobertura do período — sem inventar taxas.",
        "Frequência — Dia, Semana, Mês e Ano ficam visíveis; opções sem suporte da série ativa aparecem desabilitadas com o motivo (ex.: IPP é mensal).",
        "Indicadores do período — a faixa de KPIs mostra somente métricas válidas para a seleção ativa: última referência, média do período, menor e maior valor (ou menor e maior variação nas séries de percentual), variação e cobertura; valores ausentes aparecem como «—» com motivo.",
        "Filtros — metais selecionados, indicador/série, tipo de boletim, granularidade e período ficam na URL: F5, voltar/avançar e compartilhamento restauram a mesma visão.",
        "Gráfico, tabela e comparação — um único painel alterna os modos, com exportação correspondente aos filtros ativos. A comparação só habilita com ao menos duas séries autorizadas e unidade compatível.",
        "Lacunas — competências sem publicação oficial aparecem listadas como ausências legítimas; nunca como zero nem interpoladas.",
        "Estados — dados parciais, desatualizados, fonte indisponível ou coleta pendente são sinalizados por aviso compacto; limite de requisições e erros aparecem com opção de tentar novamente.",
        "Atualizar — recarrega catálogo, indicadores e série mantendo a perspectiva e os filtros atuais.",
      ],
    },
    {
      id: "faq",
      title: "Perguntas frequentes",
      faqs: [
        {
          q: "Qual a diferença entre estoque e estoque de segurança?",
          a: "Estoque é o saldo físico/posições. Estoque de segurança é a cobertura mínima planejada e o déficit — abra Estoque de segurança, não Estoque.",
        },
        {
          q: "O que vejo no detalhe de um material no Estoque de segurança?",
          a: "Clique na linha da lista: abre uma página com identificação, saldos por armazém, cobertura do déficit, pedidos de compra, solicitações e empenhos em aberto, projeção de estoque, consumo mensal/anual e fornecedores vinculados. O detalhe vale para a filial da linha — o mesmo código pode ter situações diferentes em cada filial. Na visão Todas as Filiais, você escolhe a filial (Santa Catarina ou Espírito Santo) antes de abrir.",
        },
        {
          q: "Como compartilho o detalhe de um material?",
          a: "O detalhe tem endereço próprio na URL (filial + código do material). Copie o link com a página aberta; F5 reabre o mesmo material e «Estoque de Segurança» no topo retorna à lista com os filtros.",
        },
        {
          q: "Para que servem os cartões de indicadores no Estoque de segurança?",
          a: "Além de mostrar as contagens do recorte, cada cartão filtra a lista com um clique: «Abaixo», «No estoque», «Acima» ou «Sem estoque de segurança» equivalem ao filtro Status; «Com estoque de segurança» mostra os materiais com o parâmetro definido; «Materiais» volta a listar tudo. O cartão ativo fica destacado.",
        },
        {
          q: "O que é a projeção de estoque no detalhe?",
          a: "Um extrato cronológico calculado pelo servidor: saldo inicial, entradas previstas de pedidos elegíveis e saídas de empenhos. Ruptura marca o primeiro saldo projetado abaixo de zero — o Portal não recalcula esses valores.",
        },
        {
          q: "Por que a lista de Estoque de segurança veio vazia?",
          a: "Vazio é um resultado legítimo do recorte — nenhum material atendeu aos filtros. Ajuste status, grupo, UM ou a busca, ou use Limpar. Se houvesse falha técnica, a tela mostraria um aviso de erro, não uma lista vazia.",
        },
        {
          q: "O que faço quando uma parte da página falha?",
          a: "Cada bloco é independente: se o resumo falhar, a lista continua (e vice-versa); no detalhe, os fornecedores podem falhar sem derrubar a ficha. Use Atualizar ou tente novamente — seus filtros são preservados. Indicadores indisponíveis aparecem como «—», nunca como zero.",
        },
        {
          q: "Saldo físico é o mesmo que saldo disponível?",
          a: "Não. Estoque mostra a posição física atual registrada no ERP. A página não calcula disponibilidade descontando reservas, empenhos ou outras regras.",
        },
        {
          q: "OTD é a mesma coisa que Entregas / Atrasos?",
          a: "Não. OTD (Visão geral / página OTD) é indicador analítico de pontualidade. Entregas / Atrasos lista recebimentos históricos de MP e a pontualidade de cada linha no período de digitação. Pedidos de compra lista PCs ainda em aberto — outro universo.",
        },
        {
          q: "Qual a diferença entre Entregas / Atrasos e Pedidos de compra?",
          a: "Entregas / Atrasos mostra linhas de recebimento já digitadas (MP) e se chegaram Em atraso ou No prazo. Pedidos de compra mostra saldo em aberto (SC7) — inclusive sem recebimento. Não clique no pedido em Entregas: a ficha de PC só cobre o universo aberto.",
        },
        {
          q: "O período em Entregas / Atrasos filtra qual data?",
          a: "A data de digitação/entrada do recebimento. Não é a data prometida nem a emissão do pedido.",
        },
        {
          q: "Qual a diferença entre Visão geral e a página OTD?",
          a: "A Visão geral é o placar de KPIs do período (com série OTD). A página OTD mostra velocímetros por unidade (Santa Catarina / Espírito Santo) e a evolução no tempo. Ambas usam o mesmo filtro de Unidade e período.",
        },
        {
          q: "Os indicadores do Sheets são os mesmos do Portal?",
          a: "Não automaticamente. O Portal usa indicadores homologados nas fichas e na Visão geral; planilhas externas podem divergir até a paridade.",
        },
        {
          q: "Onde vejo o significado de cada KPI da Visão geral?",
          a: "Nas fichas de indicadores e na Visão geral. Cada card mostra se o valor é intervalo, snapshot ou estado atual — não misture com o Início. O IDD Suprimentos e a nota do card vêm do Strategic Indicators. A meta do período acompanha o recorte; a meta mês é só referência cadastrada.",
        },
        {
          q: "De onde vêm as cotações da Inteligência de mercado?",
          a: "De fontes externas autorizadas com licença aberta: metais do World Bank Pink Sheet (média mensal em USD/t) e câmbio do Banco Central (PTAX, boletim diário). Fonte, licença e última ingestão ficam visíveis na página. A página nunca consulta a internet — os dados vêm do serviço interno de dados de mercado.",
        },
        {
          q: "Por que não consigo analisar a NCM de um produto no Comex?",
          a: "A NCM exibida vem do cadastro do ERP e só entra na análise depois de homologada no fluxo de governança (revisão fiscal → aprovação). Produto sem NCM, com NCM inválida ou ainda candidata aparece sinalizado; use «Solicitar homologação» na aba Comex e acompanhe o estado. Ninguém aprova a própria solicitação sem o perfil de gestão.",
        },
        {
          q: "Por que um mês aparece vazio ou «Sem câmbio»?",
          a: "Metais do Pink Sheet são publicados com defasagem (o mês corrente ainda não saiu) e meses antigos sem PTAX não podem ser convertidos. O Portal mostra o ponto vazio e o aviso de dados parciais — nunca inventa um valor nem exibe zero.",
        },
        {
          q: "Como o valor em BRL é calculado?",
          a: "Cotação mensal em USD × média das PTAX de venda (fechamento) do mesmo mês — método versionado pela API. O tipo de PTAX (venda/compra) pode ser trocado no filtro quando aplicável.",
        },
        {
          q: "Por que um instrumento não aparece ou mostra «indisponível»?",
          a: "Uma fonte só é exibida quando seus direitos de uso cobrem a exibição. Enquanto uma revisão de licença estiver pendente, o instrumento não fica selecionável e a página mostra um aviso neutro — nunca um valor antigo ou estimado.",
        },
        {
          q: "Por que a lista de SC vem vazia?",
          a: "Nesta tela o uso normal do Portal acompanha as solicitações das duas unidades. O recorte de centro de custo vale só no módulo próprio de Solicitações, não no Portal Suprimentos.",
        },
        {
          q: "Por que não vejo Exportar CSV?",
          a: "A exportação exige a permissão de exportação além do acesso às solicitações. Ter só a lista não libera o download.",
        },
        {
          q: "O avatar do solicitante abre uma ficha?",
          a: "Sim, quando o solicitante está vinculado a um usuário da Minha DELPI e você tem permissão para ver o perfil — o clique abre a ficha do usuário no Portal, com as solicitações de compra relacionadas na mesma tabela da listagem (colunas, ordenação e paginação; «Ver todas» abre a lista já filtrada). Sem vínculo ou sem acesso, o avatar fica apenas informativo. O avatar e o nome do fornecedor abrem a ficha cadastral (E14) nas listas e fichas de pedidos e entregas; também dá para chegar lá pela lista Fornecedores (clique na linha).",
        },
        {
          q: "De onde vem o nome do solicitante?",
          a: "Quando o usuário TOTVS da solicitação tem vínculo ativo com um cadastro da Minha DELPI, o Portal mostra o nome oficial da plataforma — com a foto real do usuário quando ele tem foto cadastrada. Sem vínculo, mostra o nome ou código que veio do ERP — nunca uma correspondência inventada por semelhança de nome.",
        },
        {
          q: "Posso filtrar por solicitante ou centro de custo?",
          a: "Sim. «Solicitante» lista as pessoas do recorte autorizado com o nome oficial da Minha DELPI quando há vínculo (o filtro é pelo usuário real do ERP, não por texto). «Centro de custo» lista código e descrição dentro do seu escopo. Ambos aceitam múltipla seleção e ficam na URL — dá para compartilhar o filtro.",
        },
        {
          q: "Como cadastro um novo fornecedor?",
          a: "Na lista Fornecedores, «Novo fornecedor» oferece três inícios no mesmo formulário: consultar por CNPJ (o campo pontua o documento automaticamente, busca dados públicos e mostra sugestões com fonte e horário de Brasília — você confirma campo a campo, nada é aplicado sozinho), buscar por razão social (em homologação — indisponível até o provedor ser aprovado) ou preencher manualmente. O formulário se organiza em seções — identificação, endereço, contato, fiscal/tributário e compras/relacionamentos — e cada uma mostra sua finalidade logo abaixo do título; cada campo tem ajuda contextual com a referência no ERP. A consulta também avisa se já existe cadastro com aquele CNPJ. Campos marcados com * são obrigatórios e, ao concluir, o Portal valida tudo antes de enviar: se faltar algo, um resumo lista os campos pendentes e cada campo mostra o que corrigir — nada sai do Portal e o que você já preencheu é mantido. Se o ERP recusar o cadastro, o aviso mostra o motivo sanitizado; quando o resultado não puder ser confirmado, acompanhe a operação antes de tentar novamente — não há reenvio automático. A gravação no ERP segue bloqueada até homologação — o Portal avisa e nada é enviado sem a revisão final.",
        },
        {
          q: "Por que alguns campos do cadastro aparecem somente leitura na edição?",
          a: "A edição libera apenas os campos cuja gravação foi homologada no ERP — endereço, contato, fiscal/tributário e compras/relacionamentos já podem ser alterados, incluindo Regime SIMP e a loja do cliente vinculado. Permanecem protegidos os campos de identidade (código, loja e CNPJ) e o código do cliente vinculado, que o ERP não permite alterar em uma edição — apenas a loja desse cliente pode ser trocada.",
        },
        {
          q: "O que significa «Este CNPJ já possui cadastro no Protheus»?",
          a: "Existe um ou mais cadastros com esse documento — o que é informativo, não um erro. O Portal lista todos os registros encontrados, com código e loja, e pagina quando há muitos. «Conferir cadastro» abre a ficha do registro em uma nova aba: você confere dados e divergências sem perder o formulário, e pode continuar o novo cadastro normalmente se desejar.",
        },
        {
          q: "O que significa «verificação de duplicidade não concluída»?",
          a: "A consulta ao cadastro interno falhou ou não retornou resultado conclusivo — não é confirmação de que o fornecedor não existe. Você pode continuar o preenchimento e conferir a ficha existente depois.",
        },
        {
          q: "Como altero o cadastro de um fornecedor?",
          a: "Na ficha do fornecedor, Editar cadastro abre o formulário com os campos homologados organizados nas mesmas seções do cadastro — altere um ou vários. Antes de gravar, revise o antes/depois na revisão; cancelar não persiste nada e somente os campos modificados são enviados. O envio depende de homologação de escrita no ERP: se estiver bloqueado, o Portal avisa e nada é enviado; se a resposta demorar, recarregue a ficha antes de repetir para evitar duplicidade.",
        },
        {
          q: "Como abro e compartilho o detalhe de um pedido de compra?",
          a: "Na lista Pedidos de compra, clique na linha. Copie o endereço da ficha para compartilhar; atualizar (F5) reabre o mesmo pedido. Voltar retorna à lista. Só pedidos em aberto aparecem — encerrados e residual não.",
        },
        {
          q: "Como abro e compartilho o detalhe de uma SC?",
          a: "Na lista Solicitações de compras, clique na SC, na linha ou no card. A ficha tem endereço próprio; F5 a restaura. Voltar retorna à lista com os filtros. Links antigos com ?request=unidade:número redirecionam para a ficha.",
        },
        {
          q: "Como compartilho o recorte da lista de SC?",
          a: "A URL da lista guarda unidade, período (date_from/date_to), uma ou mais situações (overall_stage repetido), produto e ordenação (sort_by/sort_dir). Sem branch na URL significa Todas as unidades liberadas. Os atalhos de período (iguais à Visão geral) preenchem as datas; editar datas vira Personalizado. O padrão é Este mês. F5 restaura o mesmo estado e deriva o atalho das datas. A faixa Atenção grava os mesmos overall_stage e volta para a página 1.",
        },
        {
          q: "Como compartilho o recorte de Entregas / Atrasos?",
          a: "A URL guarda branch (omitido = Todas), status, start_date, end_date, page, page_size, sort_by e sort_dir. F5 restaura o mesmo recorte. O período é a digitação do recebimento.",
        },
        {
          q: "Como ordeno a lista de SC ou pedidos em Cards?",
          a: "No modo Cards use «Ordenar por» e Crescente/Decrescente — a mesma ordenação da tabela, guardada na URL. Em Solicitações, a situação ordena o recorte inteiro antes da página; acima de cerca de 10 mil SCs, pode pedir um período ou unidade menores.",
        },
        {
          q: "Por que um card da Visão geral aparece indisponível?",
          a: "Uma fonte auxiliar falhou. Os demais indicadores continuam utilizáveis; atualize o período/unidade ou tente de novo.",
        },
        {
          q: "O que mostra o gráfico OTD na Visão geral?",
          a: "A evolução do OTD de pedidos de compra no mesmo filtro de Unidade e período dos KPIs, com granularidade e exportação. Os velocímetros ficam na página OTD. Se a série falhar, o restante da página continua utilizável.",
        },
        {
          q: "Como filtro Unidade e período na Visão geral?",
          a: "Use o preset (Hoje, Esta semana, Este mês, trimestre, ano…) ou as datas De/Até e o MultiSelect Unidade (Santa Catarina / Espírito Santo). Vazio ou ambas = consolidado. O link da página guarda o recorte para compartilhar (F5/voltar).",
        },
        {
          q: "Por que Meta parcial e Meta mês podem ser diferentes?",
          a: "Para indicadores de fluxo (OTD, CPV…), a Meta do período pode ser pró-rata ou acumulada e diferir da Meta mês cadastrada. Para Valor do estoque (snapshot), a meta é o nível/teto cadastrado — não há pró-rata diária nem soma de meses; Meta do período e Meta mês coincidem no consolidado. A Nota IDD é o score do SI. SC pendentes e materiais críticos não têm meta SI.",
        },
        {
          q: "Por que recebi 403?",
          a: "Falta o uso normal do módulo. Peça esse acesso ao administrador. A filial da tela é filtro, não permissão.",
        },
        {
          q: "Onde altero a filial padrão ou a densidade das tabelas?",
          a: "Clique no nome na TopBar → Preferências do Portal (ou no avatar, que abre o perfil deste Portal). Foto, cargo e contatos: menu do nome → Meu perfil Minha DELPI (/profile). Não existe página /preferences separada.",
        },
        {
          q: "Qual a diferença entre o perfil do Portal e o /profile da Minha DELPI?",
          a: "O avatar abre o perfil do Portal Suprimentos (`/users/:id` — preferências locais). O menu do nome inclui Meu perfil Minha DELPI (`/profile` — identidade global) e Preferências do Portal.",
        },
        {
          q: "Alterei a foto no Meu Perfil e o Suprimentos não mudou?",
          a: "A TopBar e o perfil do Portal recarregam da Core ao salvar no Meu Perfil (mesmo navegador). Se ainda estiver antiga, atualize a página do Portal Suprimentos.",
        },
        {
          q: "Ainda vejo os apps antigos no launcher",
          a: "É esperado na coexistência. O Portal é o hub novo; os legados só saem após cutover homologado.",
        },
      ],
    },
    {
      id: "glossary",
      title: "Glossário mínimo",
      intro: "Termos usados nas telas e nos balões de ajuda.",
      glossary: GLOSSARY_CONTENT,
    },
  ] satisfies readonly UserManualSection[],
} as const;
