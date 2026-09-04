/** Textos de Ajuda in-app — domínio my-requests (fonte canônica no MFE). */

export const MY_REQUESTS_HELP_TOOLTIPS = {
  shell: {
    nav: "Navegue entre Minhas (suas solicitações), Fila (itens a processar) e Nova (criar).",
  },
  mine: {
    section:
      "Lista as solicitações que você criou. Use a busca (número, código, nome ou descrição), filtros de tipo/status/filial e a paginação. Abra o número para ver detalhe, timeline e ações permitidas.",
  },
  workQueue: {
    section:
      "Fila operacional das solicitações elegíveis ao seu perfil. Busque por número/código/nome/descrição e filtre por tipo, status e filial; a API decide o escopo de processamento.",
  },
  new: {
    section:
      "Escolha o tipo: emissão de NF abre o wizard; matéria-prima abre o formulário schema-driven; outros tipos usam o fluxo genérico. Deep link: /new?type=invoice-issuance. O app legado invoice-issuance permanece em dual-run com banner de depreciação.",
    type: "Tipo cadastrado no Request Engine (workflow declarativo).",
    branch: "Filial TOTVS do escopo da solicitação (01 = SC, 02 = ES).",
  },
  invoiceWizard: {
    section:
      "Wizard specialized de emissão de NF: destinatário, tipo, itens, frete, adicionais e conferência. Lookups e create vão só para requests-api.",
    partySearch:
      "Busque destinatário (cliente/fornecedor) via lookup TOTVS proxied pela requests-api.",
    steps: "Seis etapas alinhadas ao fluxo legado de emissão, sem state machine no frontend.",
  },
  rawMaterialForm: {
    section:
      "Formulário schema-driven de criação de matéria-prima: campos vêm do form_schema do RequestType. Create só via requests-api.",
    fields: "Descrição e unidade são obrigatórios; observações são opcionais.",
  },
  detail: {
    section:
      "Detalhe da solicitação. Status e botões de ação vêm da API (`allowed_actions`) — o MFE não calcula a máquina de estados.",
    actions:
      "Cada botão corresponde a uma transição liberada pelo WorkflowEngine. Devolver e cancelar pedem o motivo em um diálogo (não use prompt do navegador).",
    invoicePayload:
      "Resumo do payload de emissão de NF (destinatário, tipo, itens) quando o type_code é invoice-issuance.",
  },
  timeline: {
    section:
      "Eventos auditáveis (criação, transição, upload, comentário). Complementa o histórico de status.",
  },
  comments: {
    section: "Thread de comentários da solicitação. Visível a quem pode ver o detalhe.",
  },
  attachments: {
    section:
      "Anexos do solicitante. Arraste ou selecione arquivos (PDF/imagem) para enviar; baixe pelos links da lista. Distintos dos artefatos de processamento.",
  },
  artifacts: {
    section:
      "Artefatos gerados no processamento (ex.: PDF da NF). Quem tem process ou manage pode enviar via arrastar/selecionar e escolher o tipo (genérico ou PDF da NF); solicitantes só baixam.",
  },
} as const;

export type MyRequestsHelpKey = keyof typeof MY_REQUESTS_HELP_TOOLTIPS;
