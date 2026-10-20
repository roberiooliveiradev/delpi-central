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
} as const;
