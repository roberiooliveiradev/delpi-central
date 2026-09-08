/** Textos de Ajuda in-app — linguagem de usuário (fonte canônica no MFE). */

export const MY_REQUESTS_HELP_TOOLTIPS = {
  shell: {
    nav: "Use o menu superior para ir às suas solicitações, à fila de atendimento, criar uma nova ou (se autorizado) ver os tipos cadastrados.",
  },
  mine: {
    section:
      "Aqui ficam as solicitações que você abriu. Filtre por tipo, status ou filial e clique no número para acompanhar o andamento e as ações disponíveis.",
  },
  workQueue: {
    section:
      "Lista o que está na sua fila para atender. Filtre o que precisa e abra a solicitação para iniciar, devolver, concluir ou registrar a emissão.",
  },
  new: {
    section:
      "Escolha um card para abrir o formulário do tipo desejado. A filial, quando necessária, aparece dentro do formulário. Você também pode abrir um tipo direto pelo link com ?type=.",
    type: "Tipo de solicitação disponível para o seu perfil.",
    branch:
      "Informe a filial do pedido (01 = Santa Catarina, 02 = Espírito Santo). Alguns tipos exigem filial; outros não pedem.",
  },
  invoiceWizard: {
    section:
      "Passo a passo para pedir emissão de nota fiscal: destinatário, tipo, itens, frete, dados extras e conferência antes de enviar.",
    partySearch:
      "Busque o cliente ou fornecedor por código, nome ou CNPJ. Selecione o resultado correto na lista.",
    steps:
      "Avance pelas etapas. Na conferência, confira o checklist antes de enviar a solicitação.",
    stepsById: {
      recipient: "Selecione o destinatário (cliente ou fornecedor) da nota.",
      invoiceType: "Informe o tipo da nota fiscal. Se for «Outros», descreva o motivo.",
      items: "Inclua os produtos com quantidade e preço.",
      freight: "Escolha CIF ou FOB e, se quiser, a transportadora.",
      extras: "Informe peso, volumes e observações úteis ao atendimento.",
      review: "Confira o checklist e envie quando tudo estiver marcado.",
    },
  },
  rawMaterialForm: {
    section:
      "Preencha os campos do formulário de matéria-prima e envie. A filial aparece quando o tipo exige.",
    fields: "Descrição e unidade são obrigatórios; observações são opcionais.",
  },
  detail: {
    section:
      "Resumo da solicitação: tipo, status, filial e solicitante. As ações possíveis aparecem como botões conforme o andamento atual.",
    actions:
      "Use os botões para avançar o atendimento. Devolver e cancelar pedem um motivo antes de confirmar.",
    invoicePayload:
      "Resumo dos dados da emissão (destinatário, tipo de NF, frete e itens) quando a solicitação é de nota fiscal.",
  },
  timeline: {
    section:
      "Histórico do que aconteceu nesta solicitação: criação, mudanças de etapa, comentários e envios de arquivo.",
  },
  comments: {
    section: "Converse sobre a solicitação com quem acompanha o atendimento.",
  },
  attachments: {
    section:
      "Anexe PDFs ou imagens que ajudem a entender o pedido. Quem acompanha a solicitação pode baixar os arquivos.",
  },
  artifacts: {
    section:
      "Arquivos gerados no atendimento (por exemplo, PDF da nota). Quem atende pode enviar; quem só solicitou normalmente só baixa.",
  },
  admin: {
    section:
      "Consulta dos tipos de solicitação (nome, ativo e se pedem filial). É só leitura — alterações de fluxo ficam com a administração do sistema.",
  },
} as const;

export type MyRequestsHelpKey = keyof typeof MY_REQUESTS_HELP_TOOLTIPS;
