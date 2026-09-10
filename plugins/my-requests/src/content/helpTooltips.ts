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
      "Escolha a filial com os botões SC (Santa Catarina) ou ES (Espírito Santo). Alguns tipos exigem filial; outros não pedem.",
  },
  invoiceWizard: {
    section:
      "Passo a passo para pedir emissão de nota fiscal: destinatário, tipo, itens, frete, dados extras e conferência antes de enviar.",
    progress:
      "O percentual sobe na ordem das etapas: só conta o que já foi concluído em sequência. Etapas futuras ficam bloqueadas até a anterior estar pronta; as concluídas podem ser reabertas. Em telas menores, use «Ver etapas» para navegar.",
    recipient: "Informe quem receberá a nota fiscal: cliente ou fornecedor.",
    invoiceType:
      "Escolha o tipo da nota. Se for «Outros», descreva o motivo em poucas palavras.",
    items:
      "Inclua os produtos da nota. Busque o item, ajuste quantidade e preço, e remova o que não precisar.",
    freight:
      "CIF: a empresa cuida do frete. FOB: o destinatário assume o frete. A transportadora é opcional.",
    extras:
      "Informe peso e volumes. A observação é opcional e ajuda quem vai emitir a nota.",
    review:
      "Revise cada seção antes de enviar. Use Alterar para corrigir e voltar à conferência.",
    partySearch:
      "Digite ao menos 2 caracteres: a busca ocorre automaticamente. Selecione o destinatário no resultado; o chip com avatar confirma a escolha (apenas um). O CNPJ/CPF aparece ao lado do código/loja.",
    productSearch:
      "Digite ao menos 2 caracteres para buscar. Selecione um ou mais produtos (chips) e use Adicionar selecionados para incluí-los na nota.",
    carrierSearch:
      "Digite ao menos 2 caracteres para buscar a transportadora (opcional). O chip com avatar confirma a escolha; remova-o se não precisar.",
    partyType:
      "Cliente ou fornecedor conforme o cadastro no ERP. A troca limpa o destinatário selecionado.",
    itemQuantity: "Quantidade do item na nota. Use valor maior que zero.",
    itemUnitPrice:
      "Preço unitário em reais. Pode ficar zero se o valor for definido depois na emissão.",
    weightKg: "Peso bruto total da carga em quilogramas.",
    volumeCount: "Número de volumes (caixas, pallets, etc.) da remessa.",
    observation:
      "Texto livre opcional para quem for emitir a nota (instruções, referências, observações).",
  },
  rawMaterialForm: {
    section:
      "Preencha os campos do formulário de matéria-prima e envie. A filial aparece quando o tipo exige.",
    fields: "Descrição e unidade são obrigatórios; observações são opcionais.",
  },
  detail: {
    section:
      "Resumo da solicitação: tipo, status, filial e solicitante. As ações possíveis aparecem conforme o andamento atual.",
    actions:
      "Use os botões para avançar o atendimento. Devolver e cancelar pedem um motivo antes de confirmar.",
    invoicePayload:
      "Resumo dos dados da emissão (destinatário, tipo de NF, frete e itens) quando a solicitação é de nota fiscal.",
    type: "Qual formulário e fluxo esta solicitação segue.",
    status: "Mostra em que etapa sua solicitação está neste momento.",
    branch: "Unidade da empresa relacionada a esta solicitação.",
    requester: "Quem abriu esta solicitação.",
    createdAt: "Data e hora em que a solicitação foi registrada.",
    progress:
      "Acompanhe as etapas do atendimento e o percentual de andamento. Se estiver aguardando correção, isso aparece em destaque.",
    party: "Cliente ou fornecedor que receberá a nota fiscal.",
    invoiceType: "Tipo da nota escolhido no pedido de emissão.",
    freight: "Quem assume o frete (CIF ou FOB) e dados relacionados.",
    items: "Quantidade de produtos incluídos na emissão.",
  },
  timeline: {
    section:
      "Histórico do que aconteceu nesta solicitação: criação, mudanças de etapa, comentários e envios de arquivo.",
  },
  comments: {
    section: "Converse sobre a solicitação com quem acompanha o atendimento.",
    newComment: "Escreva uma mensagem para quem acompanha ou atende esta solicitação.",
  },
  attachments: {
    section:
      "Arquivos que ajudam a explicar ou complementar o pedido. Quem acompanha a solicitação pode baixar os documentos.",
    upload: "Envie PDF ou imagem para complementar a solicitação.",
  },
  artifacts: {
    section:
      "Arquivos produzidos durante o atendimento, como a nota fiscal ou outro comprovante. Quem atende envia; quem só solicitou normalmente só baixa.",
    kind: "Classifique o documento gerado no atendimento (por exemplo, nota fiscal em PDF).",
    upload: "Envie o documento resultante do atendimento.",
  },
  admin: {
    section:
      "Consulta dos tipos de solicitação (nome, ativo e se pedem filial). É só leitura — alterações de fluxo ficam com a administração do sistema.",
  },
} as const;

export type MyRequestsHelpKey = keyof typeof MY_REQUESTS_HELP_TOOLTIPS;
