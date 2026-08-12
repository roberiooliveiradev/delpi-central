/**
 * Textos do wizard de transferência em massa (E6.5).
 */
export const PORTFOLIO_BULK_TRANSFER_CONTENT = {
  title: "Transferir clientes em massa",
  description:
    "Escolha a carteira de origem, os clientes, o destino e confirme com um motivo.",
  stepSource: "Origem",
  stepCustomers: "Clientes",
  stepTarget: "Destino",
  stepConfirm: "Confirmar",
  sourceLabel: "Carteira de origem",
  sourceEmpty: "Selecione a carteira de origem",
  sourceHint: "Carteira de onde os clientes saem.",
  customersLabel: "Clientes",
  customersHint: "Selecione um ou mais clientes da carteira de origem.",
  customersEmpty: "Esta carteira não tem clientes para transferir.",
  targetLabel: "Carteira de destino",
  targetEmpty: "Selecione a carteira de destino",
  targetHint: "Carteira ativa que recebe os clientes.",
  reasonLabel: "Motivo",
  reasonHint: "Motivo obrigatório da transferência (fica no histórico).",
  reasonPlaceholder: "Ex.: Reorganização de carteira regional",
  confirmSummary: "Resumo",
  confirmFrom: "De",
  confirmTo: "Para",
  confirmCount: "Clientes selecionados",
  back: "Voltar",
  next: "Continuar",
  cancel: "Cancelar",
  submit: "Transferir",
  submitting: "Transferindo…",
  successAll: "Transferência concluída: {count} cliente(s) movido(s).",
  successPartial:
    "Transferência parcial: {ok} ok, {failed} falha(s). Revise o histórico da carteira.",
  openWizard: "Transferência em massa",
  openWizardHint: "Wizard para mover vários clientes entre carteiras com auditoria.",
} as const;
