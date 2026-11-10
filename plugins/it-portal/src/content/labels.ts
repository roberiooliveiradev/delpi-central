/** Textos PT-BR do Portal de TI — valores técnicos vêm da API em inglês. */
import type {
  ActionPriority,
  ActionStatus,
  AdministrativeStatus,
  Criticality,
  Environment,
  ServerType,
} from "../api/itPortalApi";

type Option<T extends string> = { value: T; label: string };

export const UNIT_LABELS: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

export const ENVIRONMENT_LABELS: Record<Environment, string> = {
  production: "Produção",
  staging: "Homologação",
  development: "Desenvolvimento",
};

export const SERVER_TYPE_LABELS: Record<ServerType, string> = {
  physical: "Físico",
  virtual: "Virtual",
  cloud: "Nuvem",
};

export const CRITICALITY_LABELS: Record<Criticality, string> = {
  low: "Baixa",
  medium: "Média",
  high: "Alta",
  critical: "Crítica",
};

export const ADMINISTRATIVE_STATUS_LABELS: Record<AdministrativeStatus, string> = {
  planned: "Planejado",
  in_operation: "Em operação",
  maintenance: "Em manutenção",
  decommissioning: "Em desativação",
};

export const ACTION_PRIORITY_LABELS: Record<ActionPriority, string> = {
  low: "Baixa",
  medium: "Média",
  high: "Alta",
  urgent: "Urgente",
};

export const ACTION_STATUS_LABELS: Record<ActionStatus, string> = {
  pending: "Pendente",
  in_progress: "Em andamento",
  done: "Concluído",
  cancelled: "Cancelado",
};

function toOptions<T extends string>(labels: Record<T, string>): Option<T>[] {
  return (Object.keys(labels) as T[]).map((value) => ({ value, label: labels[value] }));
}

export const UNIT_OPTIONS = toOptions(UNIT_LABELS as Record<"01" | "02", string>);
export const ENVIRONMENT_OPTIONS = toOptions(ENVIRONMENT_LABELS);
export const SERVER_TYPE_OPTIONS = toOptions(SERVER_TYPE_LABELS);
export const CRITICALITY_OPTIONS = toOptions(CRITICALITY_LABELS);
export const ADMINISTRATIVE_STATUS_OPTIONS = toOptions(ADMINISTRATIVE_STATUS_LABELS);
export const ACTION_PRIORITY_OPTIONS = toOptions(ACTION_PRIORITY_LABELS);
export const ACTION_STATUS_OPTIONS = toOptions(ACTION_STATUS_LABELS);

export const SERVER_FIELD_LABELS: Record<string, string> = {
  name: "Nome",
  hostname: "Hostname",
  ip_address: "Endereço IP",
  unit_code: "Unidade",
  location: "Localização",
  environment: "Ambiente",
  server_type: "Tipo",
  purpose: "Finalidade",
  operating_system: "Sistema operacional",
  criticality: "Criticidade",
  administrative_status: "Situação administrativa",
  responsible: "Responsável",
  description: "Descrição",
};

export const ACTION_FIELD_LABELS: Record<string, string> = {
  title: "Título",
  description: "Descrição",
  responsible: "Responsável",
  priority: "Prioridade",
  due_date: "Prazo",
  status: "Status",
};

export const HISTORY_EVENT_LABELS: Record<string, string> = {
  server_created: "Servidor cadastrado",
  server_updated: "Cadastro atualizado",
  server_archived: "Servidor arquivado",
  server_restored: "Servidor restaurado",
  note_added: "Nota adicionada",
  action_plan_created: "Plano de ação criado",
  action_plan_updated: "Plano de ação editado",
  action_plan_status_changed: "Status do plano alterado",
};

export const SHELL_CONTENT = {
  navAriaLabel: "Navegação do Portal de TI",
  menuLabel: "Menu do Portal de TI",
  collapseLabel: "Recolher menu",
  expandLabel: "Expandir menu",
  nav: {
    home: "Início",
    servers: "Servidores",
    action_plans: "Planos de ação",
    help: "Ajuda",
  },
  navHints: {
    home: "Visão geral do inventário e das ações que pedem atenção.",
    servers: "Inventário de servidores da infraestrutura.",
    action_plans: "Planos de ação de todos os servidores.",
    help: "Como usar o Portal de TI.",
  },
  search: {
    label: "Buscar",
    shortcut: "Ctrl K",
    ariaLabel: "Buscar áreas do Portal de TI",
    title: "Buscar áreas do Portal de TI (Ctrl+K)",
    paletteTitle: "Ir para",
    placeholder: "Digite o nome de uma área…",
    empty: "Nenhuma área encontrada.",
    group: "Portal de TI",
  },
  userFallback: "Usuário",
  errorBoundary: {
    title: "Não foi possível carregar esta área",
    message: "Tente recarregar a página.",
    retry: "Recarregar",
  },
} as const;

export const STATE_CONTENT = {
  forbiddenTitle: "Acesso restrito",
  forbiddenPortal:
    "Você não tem acesso ao Portal de TI. Solicite a permissão à administração da Minha DELPI.",
  forbiddenArea: "Você não tem permissão para visualizar esta área.",
  unavailableTitle: "Serviço indisponível",
  errorTitle: "Não foi possível carregar",
  sessionTitle: "Sessão expirada",
  notFoundTitle: "Não encontrado",
  retry: "Tentar novamente",
  loading: "Carregando…",
} as const;

export const NOTICE_CONTENT = {
  stackAriaLabel: "Avisos do Portal de TI",
  dismissAriaLabel: "Fechar aviso",
  successTitle: "Tudo certo",
  errorTitle: "Não foi possível concluir",
} as const;

export const SECRET_WARNING =
  "Não registre senhas, tokens, chaves ou credenciais. Use o cofre corporativo e cite apenas onde a credencial está guardada.";
