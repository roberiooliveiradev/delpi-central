/**
 * Textos dos balões de explicação (HelpTooltip / SectionCard.hint / titleHint).
 * Fonte única — ajuda contextual desta entrega (IMP-MFE-HOME), sem CMS.
 */

export const CF_HELP = {
  shell: {
    portal:
      "Portal Controladoria & Finanças: Início com saudação, contexto operacional e acesso às áreas do produto.",
    navHome:
      "Início: saudação, contexto operacional, busca de caminhos e catálogo das áreas do portal.",
  },
  home: {
    overview:
      "Saudação personalizada e destaques do contexto operacional. Indicadores aparecem como indisponíveis quando a origem de dados ainda não está conectada — «—» nunca significa zero confirmado.",
    context:
      "Contexto operacional do seu dia na Controladoria & Finanças. Nesta versão, a Central de Fechamento ainda não está conectada — as seções mostram o estado honesto de cada fonte.",
    events:
      "Eventos e interações do seu dia: tarefas e alertas operacionais. Nesta versão ainda não há fontes conectadas — quando existirem, aparecem aqui sem precisar recarregar.",
    shortcuts:
      "Caminhos por seção do portal. Busque aqui, no botão Buscar da barra superior ou com Ctrl/Cmd+K — o objetivo é chegar à ação em até dois cliques.",
    search:
      "Filtra seções e rotas do catálogo (rótulo e palavras-chave). A URL guarda ?q= para compartilhar o filtro.",
    palette:
      "Busca rápida do portal: botão Buscar na barra superior ou Ctrl/Cmd+K. Mesmo catálogo do Início, em popover ancorado à barra.",
    recents:
      "Últimos caminhos abertos neste portal — guardados só neste navegador, sem dados sensíveis.",
  },
  closing: {
    page:
      "Baixas financeiras: eventos de baixa a pagar e a receber do ERP, com filtros de período, natureza e tipo de movimento. Valores são agrupados por moeda — nunca somados entre moedas — e não representam fechamento contábil oficial.",
    side:
      "Alterne entre baixas a pagar (fornecedores) e baixas a receber (clientes). Os mesmos filtros se aplicam às duas visões.",
    filters:
      "Período é obrigatório. Natureza e tipo de movimento usam os códigos de origem do ERP — ainda sem classificação contábil nesta versão.",
    summary:
      "Resumo exploratório do período: quantidade de eventos, valores por moeda e qualidade dos vínculos. Não é total oficial de fechamento.",
    table:
      "Detalhe dos eventos de baixa. «Filial não identificada» significa que a origem não informa a filial do registro — não é erro nem filial 01/02.",
    linkStatus:
      "Situação do vínculo: indica quando o documento ou a natureza financeira de origem não foi localizado, preservando o evento em vez de escondê-lo.",
    pagination: {
      pageSize: "Quantidade de eventos exibidos por página.",
      previous: "Página anterior.",
      next: "Próxima página.",
      info: "Faixa exibida e total de eventos do filtro atual.",
      jump: "Ir diretamente para uma página.",
      jumpEmpty: "Informe o número da página.",
      jumpInvalid: "Use apenas números.",
      jumpBelowMin: "A página mínima é 1.",
    },
  },
} as const;
