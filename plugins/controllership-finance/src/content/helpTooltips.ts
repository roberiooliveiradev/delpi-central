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
      "Período é obrigatório. A consulta é automática: ao alterar qualquer filtro válido os resultados se atualizam sem botão — campos digitáveis aguardam uma breve pausa na digitação. Natureza e tipo de movimento usam os códigos de origem do ERP — ainda sem classificação contábil nesta versão.",
    summary:
      "Resumo exploratório do período: quantidade de eventos, valores por moeda e qualidade dos vínculos. Não é total oficial de fechamento.",
    table:
      "Detalhe dos eventos de baixa. A contagem junto ao título mostra o universo filtrado, não apenas a página atual. Em «Colunas» você escolhe quais campos exibir, em «Fonte» ajusta o tamanho do texto e a borda direita de cada cabeçalho permite redimensionar a coluna — as preferências ficam gravadas no seu usuário. «Filial não identificada» significa que a origem não informa a filial do registro — não é erro nem filial 01/02.",
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
  stockInventory: {
    page:
      "Estoque histórico — P7: consulta operacional dos saldos de estoque registrados no fechamento de cada mês no ERP. Os resultados ainda não equivalem ao relatório oficial MATR460 — use-os como consulta de apoio ao fechamento, não como documento oficial.",
    filters:
      "Competência é obrigatória e sempre aponta para o último dia do mês. A consulta é automática: ao alterar qualquer filtro válido os resultados se atualizam sem botão — Armazém aguarda uma breve pausa na digitação. Filial é apenas filtro de dados — Matriz (01), Filial 02 ou Todas — sem alterar permissões. Visão restringe os tipos de produto; Armazém usa o código de origem do ERP.",
    indicators:
      "Valor histórico total e quantidade de itens calculados sobre todo o universo do filtro, não apenas a página exibida. Quando o snapshot do mês não existe na origem, o total não é exibido — ausência nunca aparece como zero.",
    status:
      "Disponibilidade da origem: «Disponível» = snapshot encontrado; «Parcial» = alguma filial solicitada não tem snapshot no mês; «Não encontrado» = o ERP não gravou fechamento de estoque para a competência; «Sem itens» = o snapshot existe mas os filtros não retornaram registros. Estados de acesso: «Acesso restrito» = seu usuário não possui a permissão do Portal; «Consulta ainda não habilitada» = a liberação do conjunto de dados está desativada no ambiente; «Integração de dados pendente» = a credencial técnica entre o Portal e a origem ainda aguarda autorização — acione o suporte.",
    summaryType:
      "Totais por tipo de produto (MP, PI, PA e demais) sobre o universo filtrado, com a participação percentual de cada grupo no valor histórico total.",
    summaryWarehouse:
      "Totais por armazém e filial sobre o universo filtrado, com a participação percentual de cada grupo no valor histórico total.",
    table:
      "Detalhamento por produto e armazém no snapshot do mês, com a contagem do universo filtrado junto ao título. Ordenação fixa por filial, armazém e produto. Em «Colunas» você escolhe campos, em «Fonte» ajusta o texto e a borda direita de cada cabeçalho redimensiona a coluna — preferências gravadas no seu usuário. Quando o snapshot não existe para a competência, só o aviso é exibido — a tabela vazia não representaria saldo zero.",
  },
} as const;
