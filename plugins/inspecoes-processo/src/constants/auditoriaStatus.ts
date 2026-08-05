export const AUDITORIA_STATUS_ALL = "all" as const;
export const AUDITORIA_STATUS_NAO_INSPECIONOU = "nao_inspecionou" as const;
export const AUDITORIA_STATUS_INSPECIONOU = "inspecionou" as const;
export const AUDITORIA_STATUS_SEM_CADASTRO = "sem_cadastro" as const;

export type AuditoriaInspecaoStatus =
  | typeof AUDITORIA_STATUS_ALL
  | typeof AUDITORIA_STATUS_NAO_INSPECIONOU
  | typeof AUDITORIA_STATUS_INSPECIONOU
  | typeof AUDITORIA_STATUS_SEM_CADASTRO;

/** Default da tela: foca nas pendências reais do operador. */
export const AUDITORIA_DEFAULT_STATUS: AuditoriaInspecaoStatus =
  AUDITORIA_STATUS_NAO_INSPECIONOU;

export const AUDITORIA_STATUS_OPTIONS: ReadonlyArray<{
  value: AuditoriaInspecaoStatus;
  label: string;
}> = [
  { value: AUDITORIA_STATUS_ALL, label: "Todos" },
  { value: AUDITORIA_STATUS_NAO_INSPECIONOU, label: "Não inspecionou" },
  { value: AUDITORIA_STATUS_INSPECIONOU, label: "Inspecionou" },
  {
    value: AUDITORIA_STATUS_SEM_CADASTRO,
    label: "Não possui inspeção cadastrada",
  },
];
