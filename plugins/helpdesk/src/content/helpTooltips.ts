export const helpTooltips = {
  list:
    "Aqui ficam os chamados de TI no seu nome, em tabela que preenche a tela e rola por dentro. Aberto, atualizado, resolvido e fechado mostram dia e hora. Acima da grade, o recorte ativo e a ordenação aparecem em chips; o botão de atualizar pede de novo ao helpdesk. Use Colunas para mostrar ou esconder campos — a preferência fica neste navegador. Clique no cabeçalho para ordenar (resolvido e fechado inclusive) ou abra a ordenação em níveis (até três). O número e o título são o endereço do chamado: Ctrl, Shift, Alt ou o clique do meio abrem em outra aba. O mais (+) abre chamado; as setas mudam de página; o seletor define 10, 20 ou 50 por página; o X limpa o recorte. Chamado de outra pessoa e da lixeira não aparecem.",
  filters:
    "A busca e os filtros pedem o recorte ao helpdesk. A busca acha no título ou no texto da abertura. O selo de estado usa o número do status (novo, em atendimento, pendente, aguardando aprovação, solucionado, fechado), não o texto. Pendentes e aguardando aprovação têm recorte próprio; Abertos continua incluindo os que esperam aprovação. Aberto de/até filtra pela data de abertura; atualizado de/até, pela última mudança. O construtor de filtros monta várias regras com E (AND) e grava o recorte na URL — o F5 mantém o mesmo critério. Grupos com OU, exportação, seleção em massa e mapa ficam no console do helpdesk. A ordenação também: o clique na coluna não reordena só esta página. Recorte vazio significa que nenhum chamado bate com o filtro, não que você não tenha chamados.",
  link:
    "Na primeira vez, a Minha DELPI entra no helpdesk com o mesmo login. Se o usuário ainda não existir lá, o helpdesk cria a conta. Depois disso, os chamados passam a aparecer aqui.",
  create:
    "À esquerda ficam título e descrição; à direita, categoria, urgência e observadores opcionais. A descrição aceita formatação (negrito, listas, links, título, tabela) — o mesmo editor da resposta. O que você digitar fica guardado neste navegador se atualizar a página (F5); some depois do envio. Não dá para colar imagem nem anexar arquivo na abertura. Observadores: números de usuário do helpdesk, separados por vírgula — o BFF só envia o papel observador, sem escolher solicitante nem entidade. O envio fica no rodapé da classificação. A categoria é a lista visível para o seu usuário. A seta no canto superior volta à lista com o mesmo recorte (busca, filtros e página). O chamado fica no seu usuário e na entidade padrão do helpdesk.",

  createUi: {
    back: "Volta para a lista de Meus chamados com o mesmo recorte que você tinha (busca, filtros e página), sem gravar este formulário.",
    title: "Assunto curto do chamado. Obrigatório.",
    description:
      "Detalhe o problema com formatação se quiser. Obrigatório. O texto fica guardado se você atualizar a página (F5). Não dá para colar imagem nem anexar arquivo na abertura — a barra do editor já traz ajuda em cada ícone.",
    category: "Categoria visível para o seu usuário no helpdesk. Obrigatória.",
    urgency: "Urgência do chamado no helpdesk. Obrigatória.",
    observers:
      "Opcional. Números de usuário do helpdesk, separados por vírgula. Só papel observador — sem escolher solicitante nem entidade.",
    send: "Grava o chamado no helpdesk no seu nome e abre a conversa.",
  },
  detailUi: {
    back: "Volta para a lista de Meus chamados com o mesmo recorte que você tinha (busca, filtros e página).",
  },
  detail:
    "A conversa preenche a tela e rola. No cartão aparecem aberto, atualizado, resolvido e fechado em dia e hora; TTO/TTR e o observador só se o helpdesk trouxer. A resposta fica no rodapé no mesmo editor rico da abertura, enquanto o chamado aceitar acompanhamento — chamado fechado some o Responder. O texto da resposta sobrevive ao F5 neste navegador até você enviar. Aprovar solução, reabrir e pesquisa de satisfação ficam no console do helpdesk: a API nova ainda não entrega esses passos ao solicitante. A formatação do helpdesk aparece na bolha; menções gravadas no helpdesk (chip com id de usuário) também. Imagens do fio abrem em prévia ao clicar. Não dá para colar imagem nem enviar arquivo novo por aqui, nem mencionar alguém com @ neste editor — isso fica no console até a API listar quem pode ser mencionado. A foto da Minha DELPI aparece só nas mensagens que o helpdesk reconhece como suas, pelo usuário ou pelo e-mail, não pelo nome. Nas outras, as iniciais de quem escreveu. A seta no canto superior volta à lista com o mesmo recorte (busca, filtros e página); o ícone de enviar grava a resposta. Arquivos ligados ao chamado ficam abaixo da abertura.",

  /** Controles da lista — um texto curto por superfície. */
  listUi: {
    refreshPage: "Pede de novo a lista ao helpdesk com o mesmo recorte da URL.",
    openTicket: "Abre o formulário para registrar um chamado novo no seu nome.",
    clearFilters: "Remove busca, status, urgência, categoria e datas; mantém a ordenação e o tamanho da página.",
    search: "Busca no título ou no texto da abertura do chamado. Aguarda um instante antes de pedir ao helpdesk.",
    status:
      "Recorta pelo número do status no helpdesk: abertos (inclui aprovação), em atendimento, pendentes, aguardando aprovação, solucionados ou fechados.",
    urgency: "Filtra pela urgência cadastrada no helpdesk. Todas mostra qualquer urgência.",
    category: "Filtra pela categoria visível para o seu usuário. Todas mostra qualquer categoria.",
    updatedFrom: "Só chamados cuja última atualização é neste dia ou depois.",
    updatedTo: "Só chamados cuja última atualização é neste dia ou antes.",
    createdFrom: "Só chamados abertos neste dia ou depois.",
    createdTo: "Só chamados abertos neste dia ou antes.",
    pageSize: "Quantos chamados o helpdesk devolve por página: 10, 20 ou 50.",
    sortChip: "Mostra a ordenação ativa. Até três níveis; o primeiro é o que a grade destaca.",
    filterChip: "Indica um critério do recorte que está na URL e sobrevive ao F5.",
    filterBuilderToggle: "Abre ou fecha o construtor de regras com E (AND). O recorte aplicado vai para a URL.",
    sortBuilderToggle: "Abre ou fecha a ordenação em níveis (até três campos).",
    columns: "Mostra ou esconde colunas da grade. A preferência fica neste navegador.",
    refreshList: "Atualiza só a grade com o recorte atual, sem limpar filtros.",
    prevPage: "Volta para a página anterior do recorte.",
    nextPage: "Avança para a próxima página quando o helpdesk indica que há mais.",
    pageNumber: "Página atual da lista. O helpdesk não informa o total de páginas.",
  },

  filterBuilder: {
    panel:
      "Monte regras com E (AND). Ao aplicar, o recorte vai para a URL e o F5 mantém o critério. Grupos com OU ficam no console do helpdesk por enquanto.",
    field: "Escolha o campo do filtro entre os que o helpdesk já aceita nesta lista.",
    operator: "Operação da regra: contém, é, de ou até — conforme o campo.",
    value: "Valor da regra. Vazio não entra no recorte ao aplicar.",
    removeRule: "Remove esta regra do construtor. Só altera a lista depois de Aplicar.",
    addRule: "Inclui outra regra E no construtor.",
    clear: "Apaga todas as regras do construtor sem mudar a URL até você aplicar ou limpar pelos filtros de cima.",
    apply: "Grava as regras na URL e pede a lista ao helpdesk.",
  },

  sortBuilder: {
    panel: "Defina até três níveis de ordenação. O primeiro é o que a grade destaca no cabeçalho.",
    field: "Campo usado neste nível de ordenação.",
    direction: "Ascendente (A→Z / antigo→novo) ou descendente.",
    removeLevel: "Remove este nível. Precisa restar pelo menos um.",
    addLevel: "Inclui outro nível de ordenação (no máximo três).",
    apply: "Grava a ordenação na URL e pede a lista ao helpdesk.",
  },

  columns: {
    id: "Número do chamado no helpdesk.",
    title: "Título informado na abertura.",
    status: "Estado atual com o rótulo do helpdesk; o recorte usa o número do status.",
    category: "Categoria do chamado.",
    urgency: "Urgência cadastrada.",
    assigned: "Técnico atribuído, quando o helpdesk informar.",
    created_at: "Data e hora de abertura.",
    updated_at: "Data e hora da última alteração.",
    solved_at: "Data e hora da solução, quando existir.",
    closed_at: "Data e hora do fechamento, quando existir. Ordena pelo instante de fechamento no helpdesk.",
    requester: "Nome do solicitante (rótulo). O helpdesk não identifica pessoa pelo nome.",
  },
} as const;
