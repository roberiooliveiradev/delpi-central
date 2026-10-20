export const SUPPLIERS_CONTENT = {
  eyebrow: "Operações",
  title: "Fornecedores",
  description:
    "Cadastro central de fornecedores (SA2, empresa 01) com busca, ficha cadastral e edição governada.",
  titleHint:
    "Cada fornecedor é identificado por código + loja (8 dígitos). CNPJ/CPF não é chave única e dados pessoais chegam mascarados do backend.",

  searchLabel: "Buscar fornecedor",
  searchPlaceholder: "Código, loja, razão social, fantasia ou documento",
  searchHint:
    "A busca cobre código, loja, razão social, nome fantasia e documento (CNPJ/CPF). A lista é paginada no servidor.",
  stateLabel: "UF",
  stateHint: "Filtra pelo estado (UF) do endereço cadastrado no Protheus.",
  blockedLabel: "Situação",
  blockedHint:
    "Fornecedor bloqueado (MSBLQL=1) não deve receber novos pedidos sem validação de Compras.",
  blockedEmptyOption: "Todas",
  blockedActive: "Ativos",
  blockedBlocked: "Bloqueados",
  clearFilters: "Limpar filtros",

  newSupplierAction: "Novo fornecedor",
  newSupplierHint:
    "Cadastro de fornecedor. O envio só é liberado quando a escrita no ERP estiver homologada neste ambiente.",
  refreshAction: "Atualizar",

  listTitle: "Cadastro de fornecedores",
  listHint:
    "Ordenado por código + loja. Clique na linha para abrir a ficha cadastral.",
  loading: "Carregando fornecedores",
  emptyTitle: "Nenhum fornecedor encontrado",
  emptyMessage: "Ajuste a busca ou os filtros para encontrar o cadastro desejado.",
  error:
    "Não foi possível carregar a lista de fornecedores. Tente novamente ou fale com o suporte.",
  errorForbidden:
    "Você não tem permissão operacional de Suprimentos para consultar fornecedores.",
  retry: "Tentar novamente",

  detailTitle: "Ficha do fornecedor",
  detailLoading: "Carregando ficha do fornecedor",
  detailNotFoundTitle: "Fornecedor não encontrado",
  detailNotFoundMessage:
    "O código e a loja informados não correspondem a um fornecedor ativo na base da empresa 01.",
  backToList: "Fornecedores",

  sectionIdentification: "Identificação",
  sectionAddress: "Endereço",
  sectionContact: "Contato",
  sectionFiscal: "Fiscal",
  sectionPurchasing: "Compras",

  editAction: "Editar cadastro",
  editHint:
    "Edite os campos cadastrais necessários — código, loja e CNPJ/CPF são protegidos e não podem ser alterados. Antes de gravar, revise as diferenças; nenhuma gravação ocorre sem confirmação.",
  readonlyFieldHint:
    "Somente leitura — alteração deste campo ainda não foi homologada no contrato do ERP.",
  protectedFieldHint:
    "Campo protegido — documento fiscal e identidade do fornecedor não são alteráveis nesta operação.",
  cancelAction: "Cancelar",
  reviewAction: "Revisar alterações",
  reviewTitle: "Revisar antes de gravar",
  confirmAction: "Confirmar envio",
  noChangesMessage: "Nenhum campo editável foi alterado.",
  unsavedChangesWarning:
    "Você tem alterações não gravadas. Ao sair desta tela elas serão descartadas.",

  writeDisabledTitle: "Escrita não homologada neste ambiente",
  writeDisabledMessage:
    "O cadastro/alteração de fornecedores está bloqueado por gate operacional. Nenhum dado foi enviado ao ERP.",
  outcomeAcknowledgedTitle: "Envio aceito pelo ERP — aguardando confirmação",
  outcomeAcknowledgedMessage:
    "O ERP recebeu a requisição, mas isso não garante gravação. Recarregue a ficha para confirmar a persistência.",
  outcomePersistenceTitle: "Alteração confirmada no ERP",
  outcomePersistenceMessage:
    "A gravação foi confirmada por nova consulta ao cadastro.",
  outcomeRejectedTitle: "Operação rejeitada",
  outcomeRejectedMessage:
    "O ERP ou a validação rejeitou o envio. Revise os dados e tente novamente.",
  outcomeIndeterminateTitle: "Resultado indeterminado",
  outcomeIndeterminateMessage:
    "A resposta do ERP não chegou a tempo. Antes de repetir o envio, recarregue a ficha para evitar gravação duplicada.",

  createTitle: "Novo fornecedor",
  createDescription:
    "Cadastro inicial de fornecedor com todos os campos do contrato de integração. " +
    "O envio só é liberado quando a escrita no ERP estiver homologada neste ambiente.",
  createSubmit: "Revisar e enviar",
  createBack: "Voltar para a lista",
  fieldEmptyOption: "Não informado",
  openCreatedDetail: "Abrir ficha do fornecedor criado",
  verifyAction: "Conferir gravação no ERP",
  verifyNotReflectedMessage:
    "A consulta ao ERP ainda não reflete as alterações enviadas. Aguarde e confira novamente antes de reenviar.",
} as const;

export function supplierFieldMaxLengthHint(max: number): string {
  return `Até ${max} caracteres, conforme o contrato de integração com o ERP.`;
}

export function mapSuppliersFetchError(message: string, code?: string): string {
  // "forbidden" is only the BFF's own supplies.access denial; upstream
  // denials surface typed codes (e.g. S2S_SCOPE_DENIED) or
  // "upstream_forbidden" and must not claim a missing user permission.
  if (code !== undefined) {
    return code === "forbidden"
      ? SUPPLIERS_CONTENT.errorForbidden
      : SUPPLIERS_CONTENT.error;
  }
  const normalized = message.toLowerCase();
  if (normalized.includes("forbidden") || normalized.includes("não autorizado")) {
    return SUPPLIERS_CONTENT.errorForbidden;
  }
  return SUPPLIERS_CONTENT.error;
}
