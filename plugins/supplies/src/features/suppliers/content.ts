export const SUPPLIERS_CONTENT = {
  eyebrow: "Operações",
  title: "Fornecedores",
  description:
    "Cadastro central de fornecedores (SA2, empresa 01) com busca, ficha cadastral e edição governada.",
  titleHint:
    "Cada fornecedor é identificado por código + loja (8 dígitos). CNPJ/CPF não é chave única e dados pessoais chegam mascarados (proteção LGPD).",

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

  sectionIdentificationDescription:
    "Reúne os dados que identificam o fornecedor, como documento fiscal, tipo de pessoa, razão social e nome fantasia.",
  sectionAddressDescription:
    "Informe a localização cadastral do fornecedor, incluindo logradouro, número, bairro, município, estado e país. Você pode consultar o CEP para obter sugestões de endereço.",
  sectionContactDescription:
    "Registre os canais de comunicação e as pessoas de referência do fornecedor, utilizados para contato comercial, esclarecimentos e atualização de informações.",
  sectionFiscalDescription:
    "Reúne informações fiscais e tributárias utilizadas no enquadramento cadastral do fornecedor, incluindo inscrições, regimes, retenções e códigos de classificação.",
  sectionPurchasingDescription:
    "Defina as condições comerciais e financeiras e os relacionamentos utilizados nas operações com o fornecedor, como pagamento, transportadora e outras referências cadastrais.",

  editAction: "Editar cadastro",
  editHint:
    "Atualize as informações cadastrais necessárias. Código, loja e documento fiscal são protegidos. Antes de concluir, revise os campos alterados. A gravação depende da disponibilidade e das autorizações do ambiente.",
  readonlyFieldHint:
    "Somente leitura — a alteração deste campo ainda não foi liberada no ERP.",
  protectedFieldHint:
    "Campo protegido — documento fiscal e identidade do fornecedor não são alteráveis nesta operação.",
  cancelAction: "Cancelar",
  reviewAction: "Revisar alterações",
  reviewBackAction: "Voltar para edição",
  editModeTitle: "Editando fornecedor",
  reviewTitle: "Revisar alterações",
  reviewEditDescription:
    "Confira as alterações antes de salvar. Somente campos modificados são listados.",
  confirmAction: "Confirmar e salvar",
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
    "Preencha as informações cadastrais do fornecedor. Você pode consultar dados públicos pelo CNPJ ou informar os dados manualmente. Confira as informações e revise o cadastro antes de concluir. O envio ao Protheus estará disponível quando autorizado.",
  requiredFieldsLegend: "* Campos obrigatórios",
  validationSummaryTitle: "Não foi possível concluir o cadastro.",
  validationSummaryLead: "Preencha os campos obrigatórios:",
  validationSummaryLeadMixed: "Corrija os campos indicados:",
  validationAuthMessage:
    "Não foi possível autenticar na integração com o Protheus.",
  validationGoToField: "Ir para o campo",
  validationSectionErrorOne: "1 pendência",
  validationSectionErrorMany: "{count} pendências",
  createSubmit: "Revisar dados",
  createReviewTitle: "Revisar dados do fornecedor",
  createReviewDescription:
    "Confira os dados que serão enviados ao ERP para inclusão.",
  createConfirmAction: "Confirmar inclusão",
  createBack: "Voltar para a lista",
  fieldEmptyOption: "Não informado",
  fieldNotProvided: "Não informado",
  fieldUnavailable: "Indisponível na consulta",
  catalogComboPlaceholder: "Selecione…",
  catalogSearchPlaceholder: "Buscar por código ou descrição…",
  catalogSearchAriaLabel: "Buscar opções",
  catalogLoading: "Carregando opções…",
  catalogEmpty: "Nenhuma opção encontrada.",
  catalogError: "Catálogo indisponível no momento.",
  catalogMoreHint: "Resultados limitados — refine a busca.",

  // Consulta de CEP (F5-UX-R4) — proposta assistida, nunca automática.
  postalLookupButton: "Buscar endereço",
  postalLookupLoading: "Consultando CEP…",
  postalInvalid: "Informe os 8 dígitos do CEP para consultar.",
  postalNotFound: "CEP não encontrado — preencha o endereço manualmente.",
  postalError:
    "Consulta de CEP indisponível no momento — preencha manualmente.",
  postalFoundTitle: "Endereço encontrado",
  postalApply: "Aplicar endereço",
  postalDiscard: "Descartar",
  postalMunicipalityMatched: "Município conciliado com o cadastro Protheus.",
  postalMunicipalityUnmatched:
    "Município não localizado no catálogo Protheus — selecione manualmente após aplicar.",
  postalMunicipalityMultiple:
    "Mais de um município corresponde — escolha o correto antes de aplicar.",
  postalFieldAddress: "Endereço",
  postalFieldDistrict: "Bairro",
  postalFieldCity: "Cidade",
  postalFieldState: "UF",
  openCreatedDetail: "Abrir ficha do fornecedor criado",
  statusCardTitle: "Integração Protheus",
  statusCardHint:
    "Diagnóstico técnico da integração REST de fornecedores. A verificação é somente leitura e nunca cadastra ou altera fornecedores no ERP.",
  statusCheckAction: "Verificar integração",
  statusCheckAgainAction: "Verificar novamente",
  statusChecking: "Verificando…",
  statusExpandAction: "Detalhes",
  statusCollapseAction: "Recolher",
  statusCloseAction: "Fechar diagnóstico",
  statusReopenTooltip: "Abrir diagnóstico da integração Protheus",
  statusCheckFailed:
    "Não foi possível executar o diagnóstico agora. Tente novamente.",
  statusCheckedAtLabel: "Verificado em",
  statusNeverChecked: "Verificação ainda não executada",
  statusEnvironmentLabel: "Ambiente",
  statusEnvironmentProduction: "Produção",
  statusEnvironmentHomologation: "Homologação",
  statusEnvironmentUnknown: "Desconhecido",
  statusRowConfiguration: "Configuração REST",
  statusRowConnectivity: "Conectividade",
  statusRowAuthentication: "Autenticação técnica",
  statusRowSuppliersRead: "Consulta de fornecedores",
  statusRowCreateGate: "Inclusão (POST)",
  statusRowUpdateGate: "Alteração (PUT)",
  statusRowWriteGuard: "Proteção de destino",
  statusRowWriteValidation: "Gravação efetiva",
  statusStateOk: "Correta",
  statusStateAccessible: "Acessível",
  statusStateValid: "Válida",
  statusStateFunctional: "Funcional",
  statusStateEnabled: "Habilitada",
  statusStateDisabled: "Desabilitada",
  statusStateVerified: "Válida",
  statusStateMismatch: "Divergente",
  statusStateUnverified: "Não verificada",
  statusStateFailed: "Falhou",
  statusStateUnavailable: "Indisponível",
  statusStatePending: "Pendente",
  statusStateNotTested: "Não testada",
  statusOverallReady: "Pronta para tentativa operacional",
  statusOverallPending: "Dependência externa pendente",
  statusOverallUnavailable: "Integração indisponível",
  statusWriteNotProvenNote:
    "Gravação não comprovada: nenhum POST/PUT foi executado nesta verificação.",
  statusSqlIndependentNote:
    "A listagem desta página usa consulta SQL independente da REST.",
  verifyAction: "Conferir gravação no ERP",
  verifyNotReflectedMessage:
    "A consulta ao ERP ainda não reflete as alterações enviadas. Aguarde e confira novamente antes de reenviar.",
} as const;

/** Descrições funcionais das seções — fonte única inclusão/edição (S10). */
export const supplierSectionDescriptions = {
  identification: SUPPLIERS_CONTENT.sectionIdentificationDescription,
  address: SUPPLIERS_CONTENT.sectionAddressDescription,
  contact: SUPPLIERS_CONTENT.sectionContactDescription,
  fiscal: SUPPLIERS_CONTENT.sectionFiscalDescription,
  purchasing: SUPPLIERS_CONTENT.sectionPurchasingDescription,
} as const;


export function supplierPendingChangesLabel(count: number): string {
  return count === 1
    ? "1 alteração pendente"
    : `${count} alterações pendentes`;
}

export function supplierFieldMaxLengthHint(max: number): string {
  return `Máximo de ${max} caracteres.`;
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
