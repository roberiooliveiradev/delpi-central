export const TV_DASHBOARD_HELP_TOOLTIPS = {
  ribbon: {
    slides:
      "Navegue e gerencie as telas da apresentação. Use as setas para alternar sem sair do editor.",
    newSlide: "Adiciona uma nova tela ao final da playlist. Você escolhe o tipo na sequência.",
    prevSlide: "Volta para a tela anterior na ordem de exibição.",
    nextSlide: "Avança para a próxima tela na ordem de exibição.",
    currentSlide: "Ações sobre a tela selecionada no filmstrip ou no palco.",
    pause: "Desativa a tela na exibição da TV sem removê-la da playlist.",
    activate: "Reativa uma tela pausada para voltar a aparecer na rotação.",
    duplicate: "Cria uma cópia idêntica da tela atual, logo após ela na lista.",
    delete: "Remove a tela da playlist. Esta ação não pode ser desfeita.",
    insert:
      "Adiciona elementos ao slide personalizado: textos, mídias e formas. Clique no palco para selecionar e editar.",
    background:
      "Define a cor ou imagem de fundo do slide personalizado. A imagem cobre toda a área do palco.",
    font: "Formata o texto selecionado: família, tamanho, estilo, realce e cor.",
    paragraph:
      "Alinhamento horizontal e vertical, justificação, entrelinhas e espaçamento entre caracteres.",
    shape: "Ajusta preenchimento e contorno da forma selecionada.",
    organize:
      "Controla camadas e mídia do elemento selecionado: ordem (frente/fundo), troca de arquivo ou remoção.",
    insertHeading: "Caixa de título em destaque para comunicados e chamadas principais.",
    insertText: "Bloco de texto livre para mensagens e legendas.",
    insertImage: "Imagem posicionável no slide; envie o arquivo após inserir.",
    insertVideo: "Vídeo em loop no slide; envie o arquivo após inserir.",
    insertShape: "Formas geométricas com preenchimento e contorno configuráveis.",
  },
  tabs: {
    element:
      "Propriedades do elemento selecionado no slide personalizado: conteúdo, link, posição, rotação e fundo.",
    slide:
      "Configurações da tela atual: título exibido no filmstrip, tempo na rotação e filtros operacionais (quando aplicável).",
    playlist:
      "Parâmetros globais da apresentação: resolução da TV, transição entre telas, duração padrão e link público.",
  },
  ribbonTabs: {
    home: "Gerencie slides da apresentação: adicionar telas, navegar e pausar ou duplicar a tela atual.",
    insert: "Insira elementos no slide personalizado: títulos, textos, imagens, vídeos e formas.",
    format: "Formate o slide e o elemento selecionado: fundo, fonte, forma, camadas e mídia.",
  },
  fields: {
    slideTitle: "Nome curto para identificar a tela no filmstrip e nos relatórios internos.",
    slideDuration:
      "Tempo em segundos que a tela permanece visível antes de passar para a próxima. Mínimo 5 s.",
    slideUrl: "Endereço HTTPS exibido em tela cheia nesta slide (página externa ou dashboard embutido).",
    slideBranch: "Filtra os dados operacionais desta tela para uma filial. Vazio = consolidado.",
    slidePeriod: "Janela de dias usada nas consultas de KPIs e indicadores desta tela.",
    viewport:
      "Resolução de referência para o layout. Escolha o perfil mais próximo do monitor da TV.",
    transition: "Efeito visual ao trocar de tela na exibição (fade, deslizar ou corte direto).",
    slideTransition:
      "Substitui a transição padrão da programação só nesta tela. Deixe em «Herdar» para usar o padrão.",
    defaultDuration:
      "Duração aplicada a novas telas e às que não tiverem tempo individual definido.",
    refreshInterval:
      "Intervalo para atualizar dados ao vivo (KPIs, estoque etc.) sem recarregar a página inteira.",
    publicUrl:
      "Link para abrir a apresentação em tela cheia no navegador da TV ou em um player dedicado.",
  },
  element: {
    panel:
      "Clique em um elemento no palco ou arraste para reposicionar. Use as alças para redimensionar.",
    content: "Texto exibido no elemento. Títulos usam fonte maior na TV.",
    link: "URL aberta ao toque/clique na TV, quando o player suportar interação.",
    shapeText: "Texto opcional renderizado dentro da forma.",
    strokeWidth: "Espessura da borda da forma, em pixels.",
    position:
      "Posição e tamanho em percentual do palco (0–100). Útil para alinhamento preciso entre elementos.",
    rotation: "Gira o elemento em graus (−180 a 180) em torno do centro do quadro.",
    layerUp: "Move o elemento uma camada acima, sobrepondo os demais.",
    layerDown: "Envia o elemento uma camada abaixo, atrás dos demais.",
    remove: "Remove o elemento selecionado do slide.",
    entranceAnimation:
      "Efeito de entrada na TV quando o slide aparece (fade ou deslizar). Não anima no palco do editor.",
    entranceDelay: "Atraso em milissegundos antes do elemento entrar na tela.",
    entranceDuration: "Duração da animação de entrada em milissegundos.",
    uploadMedia: "Substitui a imagem ou vídeo do elemento pelo arquivo enviado.",
    backgroundColor: "Cor sólida de fundo do slide personalizado.",
    uploadBackground: "Imagem de fundo em tela cheia. Substitui a cor quando definida.",
  },
} as const;
