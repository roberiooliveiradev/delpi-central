/** Textos pt-BR da feature Controle e Cadastro de Produtos — camada de
 * conteúdo local (labels/hints), nunca paths nem contratos. */

export const PRC_STATUS_LABELS: Record<string, string> = {
  submitted: "Enviada",
  in_progress: "Em atendimento",
  needs_information: "Aguardando informações",
  under_review: "Em revisão",
  completed: "Concluída",
  rejected: "Rejeitada",
};

export const PRC_STATUS_VARIANTS: Record<
  string,
  "neutral" | "info" | "success" | "warning" | "danger"
> = {
  submitted: "info",
  in_progress: "info",
  needs_information: "warning",
  under_review: "warning",
  completed: "success",
  rejected: "danger",
};

export const PRC_TYPE_LABELS: Record<string, string> = {
  create: "Criação",
  update: "Alteração",
};

export const PRC_EVENT_LABELS: Record<string, string> = {
  submitted: "Solicitação enviada",
  started: "Atendimento iniciado",
  assigned: "Responsável atribuído",
  draft_changed: "Ficha técnica alterada",
  information_requested: "Informações solicitadas",
  resumed: "Atendimento retomado",
  submitted_for_review: "Encaminhada para revisão",
  rejected: "Solicitação rejeitada",
  completed: "Solicitação concluída",
  verification_attempted: "Verificação oficial executada",
  verify_and_complete: "Verificação oficial e conclusão",
  "flag.created": "Bandeira criada",
  "flag.updated": "Bandeira atualizada",
  "flag.resolved": "Bandeira resolvida",
  "flag.reopened": "Bandeira reaberta",
  "flag.deleted": "Bandeira excluída",
};

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

/** Campos do catálogo v1 → rótulo pt-BR (espelha FIELD_SPECS do
 * backend; path técnico permanece EN). */
export const PRC_FIELD_LABELS: Record<string, string> = {
  officialProductCode: "Código oficial",
  description: "Descrição",
  group: "Grupo",
  productKind: "Tipo",
  unit: "Unidade",
  defaultWarehouse: "Armazém padrão",
  thirdPartyProduct: "Produto de terceiros",
  accountingAccount: "Conta contábil",
  customerReference: "Referência do cliente",
  suppliers: "Fornecedores",
};

export const PRC_SUPPLIER_LABELS: Record<string, string> = {
  supplierCode: "Código",
  store: "Loja",
  supplierName: "Razão social",
  partNumber: "Part Number",
  catalogNumber: "Catálogo",
};

/** Helps funcionais por path da ficha — significado real do campo
 * TOTVS em linguagem de Engenharia (nunca nome de tabela como
 * explicação). Quando presente, prevalece sobre `spec.note`. */
/** Catálogo canônico PRC-REF-018 — labels+helps funcionais.
 * Consumido por CREATE, UPDATE, Ficha técnica e Verificação TOTVS.
 * Nunca exibir B1_/A5_/legado como help ao usuário. */
export const PRC_FIELD_HELP: Record<string, string> = {
  officialProductCode:
    "Código atribuído ao produto no TOTVS. Preserve zeros à esquerda.",
  description:
    "Descrição técnica utilizada para identificar o produto.",
  group:
    "Classificação do produto nos grupos cadastrados no TOTVS.",
  productKind:
    "Classificação do tipo de produto no ERP.",
  unit:
    "Unidade de medida utilizada no cadastro e movimentação.",
  defaultWarehouse:
    "Armazém normalmente associado ao produto.",
  accountingAccount:
    "Conta usada na classificação contábil do produto.",
  thirdPartyProduct:
    "Indica a classificação do produto quanto à propriedade de terceiros, conforme cadastro oficial.",
  customerReference:
    "Código ou referência fornecida pelo cliente para identificar o produto.",
  suppliers:
    "Vínculos do produto com fornecedores oficiais (código, loja e atributos).",
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

const LEGACY_NOTE_RE = /\b(B1_|A5_|legado|legado\s*['"]|cta_contabil)\b/i;

/** Help funcional do path — nunca devolve nota técnica/legado. */
export function prcFieldHelp(
  path: string,
  fallbackNote?: string | null,
): string | undefined {
  const head = path.split(".")[0];
  const fromCatalog = PRC_FIELD_HELP[head] || PRC_FIELD_HELP[path];
  if (fromCatalog) return fromCatalog;
  const note = (fallbackNote || "").trim();
  if (!note || LEGACY_NOTE_RE.test(note)) return undefined;
  return note;
}

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
    "Código de peça informado pelo fornecedor, quando disponível.",
  catalogHint:
    "Referência de catálogo informada pelo fornecedor, quando disponível.",
  reasonOptional:
    "Justificativa opcional (até 250 caracteres) — aparece só quando o campo foi preenchido ou alterado.",
  selectRequired:
    "Escolha um fornecedor na lista de resultados para confirmar o código e a loja.",
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

/** Rótulos funcionais pt-BR dos enums de domínio (códigos vêm do
 * catálogo canônico do backend; descrições são conteúdo de UI). */
export const PRC_ENUM_OPTION_LABELS: Record<
  string,
  Record<string, string>
> = {
  productKind: {
    MP: "Matéria-prima",
    PA: "Produto acabado",
    PI: "Produto intermediário",
  },
  thirdPartyProduct: {
    "1": "Não",
    "2": "Sim",
  },
};

export const PRC_COPY = {
  breadcrumbHome: "Início",
  breadcrumbRoot: "Controle e Cadastro de Produtos",
  listTitle: "Solicitações de produtos",
  listDescription:
    "Fila de cadastros e alterações de matérias-primas sob atendimento da Engenharia.",
  newRequest: "Nova solicitação",
  refresh: "Atualizar",
  clearFilters: "Limpar filtros",
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
  verifyCta: "Verificar e concluir",
  verifyExplain:
    "A Engineering API relê o cadastro oficial no TOTVS e conclui a solicitação somente se todos os campos verificáveis corresponderem. A revisão publicada é imutável.",
  neverVerified: "Nenhuma verificação oficial executada até o momento.",
  noRevisions: "Nenhuma revisão publicada — revisões existem após a conclusão.",
  immutableRevision:
    "Revisões publicadas são imutáveis e servem apenas para consulta.",
} as const;

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function prcShortId(id: string): string {
  return `#${id.slice(0, 8)}`;
}

/** Identidade honesta — nunca exibe GUID bruto como nome de pessoa. */
export function prcPersonLabel(
  subject: string | null | undefined,
  displayName?: string | null,
): string {
  const name = (displayName || "").trim();
  if (name) return name;
  if (!subject) return PRC_COPY.unassigned;
  return UUID_RE.test(subject.trim())
    ? PRC_COPY.assigneeUnknown
    : subject.trim();
}

export function prcRequesterLabel(requester: {
  subject: string;
  displayName?: string | null;
}): string {
  const name = (requester.displayName || "").trim();
  if (name) return name;
  return UUID_RE.test(requester.subject)
    ? PRC_COPY.requesterUnknown
    : requester.subject;
}

export function prcFieldLabel(path: string): string {
  const head = path.split(".")[0];
  const sub = path.split(".").slice(1).join(".");
  const base = PRC_FIELD_LABELS[head] || head;
  return sub ? `${base} · ${PRC_SUPPLIER_LABELS[sub] || sub}` : base;
}

export function prcStatusLabel(status: string): string {
  return PRC_STATUS_LABELS[status] || status;
}
