/** Textos de Ajuda in-app — domínio my-requests (fonte canônica no MFE). */

export const MY_REQUESTS_HELP_TOOLTIPS = {
  shell: {
    nav: "Navegue entre Minhas (suas solicitações), Fila (itens a processar) e Nova (criar).",
  },
  mine: {
    section:
      "Lista as solicitações que você criou. Abra o número para ver detalhe, timeline e ações permitidas.",
  },
  workQueue: {
    section:
      "Fila operacional das solicitações elegíveis ao seu perfil de processar/gerenciar. A API decide o escopo.",
  },
  new: {
    section:
      "Cria uma solicitação genérica escolhendo tipo e filial. Wizards especializados (ex.: NF) entram em etapas futuras.",
    type: "Tipo cadastrado no Request Engine (workflow declarativo).",
    branch: "Filial TOTVS do escopo da solicitação (01 = SC, 02 = ES).",
  },
  detail: {
    section:
      "Detalhe da solicitação. Status e botões de ação vêm da API (`allowed_actions`) — o MFE não calcula a máquina de estados.",
    actions:
      "Cada botão corresponde a uma transição liberada pelo WorkflowEngine para o seu perfil e status atual.",
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
      "Anexos enviados pelo solicitante (PDF/imagens etc.). Distintos dos artefatos de processamento.",
  },
  artifacts: {
    section:
      "Artefatos gerados no processamento (evidências do atendente). Upload restrito a process/manage.",
  },
} as const;

export type MyRequestsHelpKey = keyof typeof MY_REQUESTS_HELP_TOOLTIPS;
