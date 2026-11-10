/** Textos PT-BR do Portal de TI — valores técnicos vêm da API em inglês. */
import type {
  ActionPriority,
  ActionStatus,
  AdministrativeStatus,
  Criticality,
  DbmsEngine,
  Environment,
  HostingRuntime,
  ServerType,
  ServiceKind,
  ServiceType,
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

export const SERVICE_KIND_LABELS: Record<ServiceKind, string> = {
  business_application: "Aplicação de negócio",
  platform_service: "Serviço de plataforma",
};

export const SERVICE_KIND_HINT =
  "Aplicação de negócio é o que o usuário final usa (ex.: um portal). Serviço de plataforma é infraestrutura de apoio (ex.: proxy, cache, identidade). Um container não é, por si só, uma aplicação.";

export const SERVICE_TYPE_LABELS: Record<ServiceType, string> = {
  web_application: "Aplicação web",
  api: "API",
  identity_access: "Identidade e acesso",
  reverse_proxy: "Proxy reverso / gateway",
  cache: "Cache",
  messaging: "Mensageria",
  file_storage: "Armazenamento de arquivos",
  scheduler: "Agendador / jobs",
  monitoring: "Monitoramento",
  erp: "ERP",
  other: "Outro",
};

export const HOSTING_RUNTIME_LABELS: Record<HostingRuntime, string> = {
  container: "Container",
  native_process: "Processo nativo",
  os_service: "Serviço do sistema operacional",
  virtual_machine: "Máquina virtual dedicada",
  other: "Outro",
};

export const DBMS_LABELS: Record<DbmsEngine, string> = {
  postgresql: "PostgreSQL",
  sql_server: "SQL Server",
  mysql: "MySQL",
  mariadb: "MariaDB",
  oracle: "Oracle",
  mongodb: "MongoDB",
  sqlite: "SQLite",
  other: "Outro",
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
export const SERVICE_KIND_OPTIONS = toOptions(SERVICE_KIND_LABELS);
export const SERVICE_TYPE_OPTIONS = toOptions(SERVICE_TYPE_LABELS);
export const HOSTING_RUNTIME_OPTIONS = toOptions(HOSTING_RUNTIME_LABELS);
export const DBMS_OPTIONS = toOptions(DBMS_LABELS);

export const ARCHIVED_OPTIONS = [
  { value: "active", label: "Ativos" },
  { value: "archived", label: "Arquivados" },
  { value: "all", label: "Todos" },
];

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

export const SERVICE_FIELD_LABELS: Record<string, string> = {
  name: "Nome",
  description: "Descrição",
  service_kind: "Natureza",
  service_type: "Tipo de serviço",
  technology: "Tecnologia / runtime",
  environment: "Ambiente",
  unit_code: "Unidade",
  port: "Porta",
  criticality: "Criticidade",
  responsible: "Responsável",
  administrative_status: "Situação administrativa",
};

export const DATABASE_FIELD_LABELS: Record<string, string> = {
  name: "Nome da instância",
  dbms: "SGBD",
  version: "Versão",
  server_id: "Servidor hospedeiro",
  port: "Porta",
  environment: "Ambiente",
  purpose: "Finalidade",
  criticality: "Criticidade",
  responsible: "Responsável",
  administrative_status: "Situação administrativa",
  technical_notes: "Observações técnicas",
};

export const LINK_FIELD_LABELS: Record<string, string> = {
  service_id: "Serviço",
  server_id: "Servidor",
  database_instance_id: "Instância de banco",
  runtime: "Forma de execução",
  instance_name: "Nome da instância em execução",
  notes: "Observações",
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
  service_created: "Serviço cadastrado",
  service_updated: "Serviço atualizado",
  service_archived: "Serviço arquivado",
  service_restored: "Serviço restaurado",
  service_hosting_created: "Serviço vinculado ao servidor",
  service_hosting_removed: "Vínculo serviço–servidor removido",
  database_instance_created: "Instância de banco cadastrada",
  database_instance_updated: "Instância de banco atualizada",
  database_instance_archived: "Instância de banco arquivada",
  database_instance_restored: "Instância de banco restaurada",
  database_consumer_created: "Serviço vinculado ao banco",
  database_consumer_removed: "Vínculo serviço–banco removido",
};

export const SHELL_CONTENT = {
  navAriaLabel: "Navegação do Portal de TI",
  menuLabel: "Menu do Portal de TI",
  collapseLabel: "Recolher menu",
  expandLabel: "Expandir menu",
  nav: {
    home: "Início",
    servers: "Servidores",
    services: "Serviços",
    databases: "Bancos de dados",
    action_plans: "Planos de ação",
    help: "Ajuda",
  },
  navHints: {
    home: "Visão geral do inventário e das ações que pedem atenção.",
    servers: "Inventário de servidores da infraestrutura.",
    services: "Aplicações e serviços de plataforma e onde estão hospedados.",
    databases: "Instâncias de bancos de dados e serviços que as utilizam.",
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
