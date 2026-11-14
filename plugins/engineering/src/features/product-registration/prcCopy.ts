/** Textos pt-BR da feature Controle e Cadastro de Produtos — camada de
 * conteúdo local (labels/hints), nunca paths nem contratos. */

import {
  PRC_EVENT_LABELS,
  PRC_ENUM_OPTION_LABELS,
  PRC_FIELD_HELP,
  PRC_FIELD_LABELS,
  PRC_STATUS_LABELS,
  PRC_STATUS_VARIANTS,
  PRC_SUPPLIER_LABELS,
  PRC_TYPE_LABELS,
  prcFieldHelp,
  prcPersonLabel,
  prcRequesterLabel,
  prcStatusLabel,
} from "@delpi/plugin-ui/index";

export const PRC_RESULT_LABELS: Record<string, string> = {
  matched: "Correspondente",
  mismatched: "Divergente",
  unverifiable: "Não verificável",
  not_found: "Não encontrado",
  forbidden: "Sem permissão na fonte",
  unavailable: "Fonte indisponível",
  timeout: "Tempo esgotado",
  contract_error: "Erro de contrato oficial",
};

export const PRC_RESULT_VARIANTS: Record<
  string,
  "neutral" | "info" | "success" | "warning" | "danger"
> = {
  matched: "success",
  mismatched: "danger",
  unverifiable: "warning",
  not_found: "danger",
  forbidden: "danger",
  unavailable: "warning",
  timeout: "warning",
  contract_error: "danger",
};

/** Helps das ações de bandeira — no próprio label (sem ícone ?). */
export const PRC_FLAG_ACTION_HELP = {
  add: "Registra um acompanhamento para este campo, sem alterar seu valor.",
  edit: "Permite modificar o título ou a descrição do acompanhamento.",
  resolve:
    "Encerra este acompanhamento, mantendo seu histórico. Não aprova nem altera o dado do produto.",
  reopen: "Retorna o acompanhamento ao estado aberto para nova análise.",
  remove:
    "Retira a bandeira da visualização e preserva os eventos de auditoria.",
  save: "Grava as alterações feitas neste acompanhamento.",
  close: "Fecha o painel sem gravar alterações pendentes.",
  legend:
    "Azul adiciona acompanhamento; vermelha indica aberto; verde indica resolvido. A cor não aprova o cadastro no TOTVS.",
} as const;

/** Textos da busca assistida SA2 (código / razão social / fantasia). */
export const PRC_SUPPLIER_HELP = {
  placeholder: "Buscar por código, razão social ou nome fantasia",
  search:
    "Use a lupa da linha para abrir a busca no cadastro TOTVS; selecione a razão social e a loja oficiais.",
  codeHint:
    "Código oficial do fornecedor no cadastro TOTVS.",
  storeHint:
    "Unidade cadastral (loja) do fornecedor no TOTVS.",
  legalNameHint:
    "Razão social oficial do fornecedor no TOTVS.",
  tradeNameHint:
    "Nome fantasia do fornecedor, quando disponível no cadastro oficial.",
  partNumberHint:
    "Código de peça do produto no catálogo do fornecedor — obrigatório para vincular.",
  catalogHint:
    "Referência de catálogo informada pelo fornecedor, quando disponível.",
  reasonOptional:
    "Justificativa opcional (até 250 caracteres) — aparece só quando o campo foi preenchido ou alterado.",
  selectRequired:
    "Escolha um fornecedor na lista de resultados para confirmar o código e a loja.",
  partNumberRequired:
    "Part Number é obrigatório para vincular o fornecedor.",
  duplicate:
    "Este fornecedor e esta loja já foram adicionados à solicitação.",
  duplicateExisting:
    "Este fornecedor já está vinculado ao produto. Para alterar o Part Number ou Catálogo, edite a linha existente.",
  discardDraftOnly:
    "Descartar remove somente esta linha candidata — o vínculo oficial permanece intacto.",
} as const;

/** Mensagens de validação acionáveis da ficha (sem jargão técnico). */
export const PRC_VALIDATION = {
  selectOptionRequired: "Selecione uma opção para continuar.",
  catalogUnavailable:
    "Não foi possível consultar as opções oficiais no TOTVS. Tente novamente.",
} as const;

export const PRC_COPY = {
  breadcrumbHome: "Início",
  breadcrumbRoot: "Controle e Cadastro de Produtos",
  listTitle: "Solicitações de produtos",
  listDescription:
    "Fila de cadastros e alterações de matérias-primas sob atendimento da Engenharia.",
  newRequest: "Nova solicitação",
  refresh: "Atualizar",
  remoteUpdatePending:
    "Esta solicitação foi atualizada em outra sessão. Suas edições estão preservadas; os dados serão recarregados ao concluir.",
  clearFilters: "Limpar filtros",
  pendingViewLabel: "Pendências de atendimento",
  pendingViewDescription:
    "Exibindo somente solicitações que aguardam tratamento da Engenharia.",
  pendingViewClear: "Ver todas as solicitações",
  emptyQueue: "Nenhuma solicitação no escopo atual.",
  emptyFiltered: "Nenhum resultado para os filtros aplicados.",
  awaitingCode: "Aguardando cadastro",
  unassigned: "Não atribuído",
  assigneeUnknown: "Responsável não identificado",
  requesterUnknown: "Solicitante não identificado",
  openRequest: "Abrir solicitação",
  forbidden:
    "Você não possui permissão para acessar o Controle e Cadastro de Produtos.",
  detailBreadcrumb: "Solicitações",
  intakeNote:
    "Enviar a solicitação registra o pedido para atendimento da Engenharia — não cadastra nem altera o produto no TOTVS.",
  verifyCta: "Concluir atendimento",
  verifyExplain:
    "Ao concluir, a Engineering API valida a ficha, consulta o TOTVS em tempo real e só publica a revisão se todos os campos verificáveis corresponderem.",
  neverVerified: "Nenhuma verificação oficial executada até o momento.",
  verifyingNow: "Conferindo dados técnicos e consultando o cadastro oficial…",
  conclusionBlocked:
    "Conclusão bloqueada. A solicitação permanece Em atendimento.",
  officialUnavailable:
    "Não foi possível confirmar os dados oficiais no TOTVS. Nenhuma conclusão foi realizada.",
  noRevisions: "Nenhuma revisão publicada — revisões existem após a conclusão.",
  immutableRevision:
    "Revisões publicadas são imutáveis e servem apenas para consulta.",
} as const;

/** Intercâmbio de informações analista ↔ solicitante (PRC-REF-019).
 * Ajuda no próprio texto/hint — sem ícone de interrogação. */
export const PRC_INFO_COPY = {
  requestTitle: "Solicitar informações",
  requestIntro:
    "Registre uma ou mais perguntas ao solicitante. Cada pergunta pode apontar para um campo da ficha, um vínculo de fornecedor ou ser um esclarecimento geral.",
  recipient: "Destinatário",
  recipientHint:
    "O solicitante do caso recebe as perguntas e responde pela própria solicitação.",
  recipientUnknown: "Solicitante não identificado",
  questionsTitle: "Perguntas",
  addQuestion: "Adicionar pergunta",
  removeQuestion: "Remover pergunta",
  targetType: "Tipo de alvo",
  targetField: "Campo da ficha",
  targetFieldPlaceholder: "Selecione o campo",
  supplierPick: "Fornecedor da ficha",
  supplierPickPlaceholder: "Preencher a partir da ficha (opcional)",
  supplierSearch: "Pesquisar fornecedor",
  supplierSearchPlaceholder:
    "Digite código, razão social ou nome fantasia…",
  supplierSearchEmpty: "Nenhum fornecedor oficial encontrado para o termo.",
  supplierSearchUnavailable:
    "Pesquisa oficial indisponível — tente novamente. Não é permitido informar código/loja manualmente.",
  supplierCode: "Código do fornecedor",
  supplierStore: "Loja",
  supplierAttribute: "Atributo",
  questionText: "Pergunta",
  questionTextHint: "Seja objetivo: o solicitante responderá em texto livre.",
  message: "Mensagem complementar (opcional)",
  messageHint:
    "Contexto adicional exibido ao solicitante junto com as perguntas.",
  submitRequest: "Solicitar informações",
  cancel: "Cancelar",

  panelTitle: "Esclarecimentos com o solicitante",
  panelLoading: "Carregando esclarecimentos…",
  panelEmpty: "Nenhuma rodada de esclarecimento registrada.",
  noActiveRound: "Nenhuma rodada de esclarecimento em aberto.",
  panelLoadError: "Não foi possível carregar os esclarecimentos.",
  refresh: "Atualizar esclarecimentos",
  roundLabel: "Rodada",
  requestedBy: "Solicitado por",
  roundMessage: "Mensagem do analista",
  yourAnswer: "Sua resposta",
  answerLabel: "Resposta",
  noAnswerYet: "Sem resposta registrada.",
  requesterIntro:
    "Preencha as respostas e envie à Engenharia.",
  requesterWaitingReview:
    "Respostas enviadas. A Engenharia está analisando os esclarecimentos.",
  requesterWaitingOther:
    "As perguntas foram encaminhadas. Aguardando respostas para prosseguir.",
  saveDraft: "Salvar rascunho",
  submitAnswers: "Enviar respostas",
  draftSaved: "Rascunho salvo.",
  answersSubmitted: "Respostas enviadas. Aguardando análise.",
  reviewIntro:
    "Avalie cada resposta: aceite o esclarecimento ou solicite complemento.",
  acceptQuestion: "Aceitar esclarecimento",
  requestFollowUp: "Solicitar complemento",
  followUpQuestion: "Nova pergunta de complemento",
  followUpSubmit: "Enviar complemento",
  followUpCancel: "Cancelar complemento",
  followUpSent: "A Engenharia solicitou informações complementares.",
  questionAccepted: "Esclarecimento aceito.",
  resolvedReady: "Todas as perguntas desta rodada foram avaliadas.",
  resolvedSummary: "Esclarecimentos aceitos.",
  resume: "Retomar atendimento",
  resumeReadyHint:
    "Os esclarecimentos foram avaliados. O atendimento pode ser retomado no cabeçalho da solicitação.",
  resumeBlocked:
    "Aguardando informações do solicitante. O atendimento poderá ser retomado após a análise dos esclarecimentos.",
  resumeBlockedReview:
    "Há respostas aguardando avaliação. Aceite os esclarecimentos ou registre a dispensa antes de retomar.",
  resumeConflict:
    "Este atendimento ainda possui esclarecimentos pendentes. Aguarde as respostas e conclua a análise antes de retomar.",
  resumeSuccess: "Atendimento retomado com sucesso.",
  history: "Histórico de esclarecimentos",
} as const;

export const PRC_INFO_QUESTION_STATUS_LABELS: Record<string, string> = {
  pending: "Aguardando resposta",
  drafted: "Rascunho",
  submitted: "Respondida",
  accepted: "Aceita",
  follow_up_requested: "Complemento solicitado",
};

export const PRC_INFO_QUESTION_STATUS_VARIANTS: Record<
  string,
  "neutral" | "info" | "success" | "warning" | "danger"
> = {
  pending: "warning",
  drafted: "neutral",
  submitted: "info",
  accepted: "success",
  follow_up_requested: "warning",
};

export const PRC_INFO_ROUND_STATUS_LABELS: Record<string, string> = {
  awaiting_requester: "Aguardando solicitante",
  awaiting_review: "Aguardando análise",
  resolved: "Resolvida",
};


export function prcShortId(id: string): string {
  return `#${id.slice(0, 8)}`;
}



export function prcFieldLabel(path: string): string {
  const head = path.split(".")[0];
  const sub = path.split(".").slice(1).join(".");
  const base = PRC_FIELD_LABELS[head] || head;
  return sub ? `${base} · ${PRC_SUPPLIER_LABELS[sub] || sub}` : base;
}


/* UI-FIX-03/07 — implementações migraram para `@delpi/plugin-ui`
 * (fonte única compartilhada com Minhas Solicitações). */
/* UI-FIX-03/07 — implementações migraram para `@delpi/plugin-ui`
 * (fonte única compartilhada com Minhas Solicitações). Re-export via
 * `export {}` local — `export {} from` ao remote federado gera export
 * duplicado no transform do Rollup MF. */
export {
  PRC_EVENT_LABELS,
  PRC_ENUM_OPTION_LABELS,
  PRC_FIELD_HELP,
  PRC_FIELD_LABELS,
  PRC_STATUS_LABELS,
  PRC_STATUS_VARIANTS,
  PRC_SUPPLIER_LABELS,
  PRC_TYPE_LABELS,
  prcFieldHelp,
  prcPersonLabel,
  prcRequesterLabel,
  prcStatusLabel,
};

/** Rótulos de apresentação para a origem técnica da solicitação.
 * O contrato persiste `detail.source` (ex.: `my-requests`); a UI
 * nunca expõe o código bruto — desconhecido cai no fallback. */
export const PRC_SOURCE_LABELS: Record<string, string> = {
  "my-requests": "Canal corporativo (My Requests)",
  my_requests: "Canal corporativo (My Requests)",
  engineering: "Portal Engenharia",
  "engineering-api": "Portal Engenharia",
};

export function prcSourceLabel(source: string | null | undefined): string {
  if (!source) return "—";
  return PRC_SOURCE_LABELS[source] ?? "Canal integrado";
}
