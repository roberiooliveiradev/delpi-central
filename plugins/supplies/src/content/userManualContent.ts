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
        "O avatar na TopBar abre o Meu Perfil Minha DELPI (/profile) — foto, cargo e contatos. O nome abre o menu com Preferências do Portal Suprimentos (filial padrão, densidade).",
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
          where: "Início",
          how: "Bloco Atenção e atalhos do catálogo",
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
          how: "Abra a linha; itens, entrega prometida, recebimentos e SC origem. Copie o endereço da ficha; F5 a restaura; voltar retorna à lista. Só pedidos em aberto",
        },
        {
          want: "Abrir solicitações de compras (SC)",
          where: "Solicitações de compras",
          how: "Lista no escopo de CC/unidade; filtros automáticos; clique na SC para a ficha; URL guarda filtros (F5); exportação Excel se tiver permissão",
        },
        {
          want: "Ver o detalhe de uma solicitação",
          where: "Solicitações de compras",
          how: "Abra a SC; cabeçalho e itens no escopo de CC. Copie o endereço da ficha; F5 a restaura; voltar retorna à lista com os filtros",
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
          want: "Ver estoque de segurança (ESTSEG)",
          where: "Estoque de segurança",
          how: "Déficit e cobertura — não é o saldo físico",
        },
        {
          want: "Consultar item / produto",
          where: "Produtos",
          how: "Busca e ficha 360 quando liberada",
        },
        {
          want: "Identificar fornecedor ou solicitante",
          where: "Pedidos de compra",
          how: "Avatar de iniciais na lista, nos cards e na ficha — também em Solicitações de compras. A página própria ainda não existe; o avatar não navega",
        },
        {
          want: "Consultar fornecedor",
          where: "Fornecedores",
          how: "Lista 360 reservada; hoje o avatar identifica o fornecedor nos pedidos",
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
        "Início — saudação com o primeiro nome da sessão, atenção, busca, favoritos e caminhos por capability.",
        "Visão geral — indicadores consolidados do período e das unidades selecionadas; itens operacionais em Solicitações e Operações.",
        "OTD — velocímetros de pontualidade e evolução; abra pelo Início, catálogo Análises ou CTA da Visão geral.",
        "Pedidos de compra — itens com saldo pendente de recebimento no recorte; hero com linhas/valor/atrasadas; Atenção Todos(N)/Atrasados(N) do resumo do servidor; filtros automáticos, Atualizar; Unidade como Santa Catarina / Espírito Santo; clique no PC para a ficha. Distinto do OTD de pontualidade e de Entregas / Atrasos.",
        "Entregas / Atrasos — recebimentos de matéria-prima (MP) já digitados, classificados em Em atraso ou No prazo. Período = data de digitação/entrada. Sem clique no pedido (histórico ≠ PC aberto).",
        "Solicitações de compras — acompanhamento global no período; o hero conta SCs e a faixa Atenção filtra a situação sem ser uma permissão. Clique na SC para a ficha; exportação Excel faz parte do uso normal.",
        "Operações — pedidos, entregas, fornecedores, produtos, estoque e ESTSEG.",
        "Indicadores / Negociações — recorte analítico quando liberado.",
        "Administração — mappings e configurações.",
        "Perfil — avatar na TopBar abre /profile do host; preferências deste Portal ficam no menu do nome (Preferências do Portal).",
        "Ajuda — este manual, FAQ e glossário.",
      ],
    },
    {
      id: "faq",
      title: "Perguntas frequentes",
      faqs: [
        {
          q: "Qual a diferença entre estoque e estoque de segurança?",
          a: "Estoque é o saldo físico/posições. Estoque de segurança (ESTSEG) é a cobertura mínima planejada e o déficit — abra Estoque de segurança, não Estoque.",
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
          q: "Por que a lista de SC vem vazia?",
          a: "Nesta tela o uso normal do Portal acompanha as solicitações das duas unidades. O recorte de centro de custo vale só no módulo próprio de Solicitações, não no Portal Suprimentos.",
        },
        {
          q: "Por que não vejo Exportar CSV?",
          a: "A exportação exige a permissão de exportação além do acesso às solicitações. Ter só a lista não libera o download.",
        },
        {
          q: "Por que o avatar do fornecedor ou do solicitante não abre uma ficha?",
          a: "A identificação visual já segue o padrão do Portal Comercial. As páginas de fornecedor e de pessoa estão reservadas e ainda não existem — o avatar não navega.",
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
          a: "Clique no nome na TopBar → Preferências do Portal. Foto, cargo e contatos: clique no avatar (abre /profile do host). Não existe página /preferences separada.",
        },
        {
          q: "Qual a diferença entre o perfil do Portal e o /profile da Minha DELPI?",
          a: "O avatar abre /profile (identidade global Minha DELPI). O menu do nome inclui Preferências do Portal Suprimentos (units, densidade, filial padrão). A página /users/:id do plugin continua sendo o editor de preferências locais.",
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
