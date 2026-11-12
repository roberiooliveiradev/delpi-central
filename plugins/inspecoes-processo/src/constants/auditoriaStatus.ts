export const AUDITORIA_STATUS_ALL = "all" as const;
export const AUDITORIA_STATUS_NAO_INSPECIONOU = "nao_inspecionou" as const;
export const AUDITORIA_STATUS_INSPECIONOU = "inspecionou" as const;
export const AUDITORIA_STATUS_ABAIXO_MINIMO = "abaixo_minimo" as const;
export const AUDITORIA_STATUS_MINIMO_ATINGIDO = "minimo_atingido" as const;
export const AUDITORIA_STATUS_SEM_CADASTRO = "sem_cadastro" as const;

export type AuditoriaInspecaoStatus =
  | typeof AUDITORIA_STATUS_ALL
  | typeof AUDITORIA_STATUS_NAO_INSPECIONOU
  | typeof AUDITORIA_STATUS_INSPECIONOU
  | typeof AUDITORIA_STATUS_ABAIXO_MINIMO
  | typeof AUDITORIA_STATUS_MINIMO_ATINGIDO
  | typeof AUDITORIA_STATUS_SEM_CADASTRO;

/** Default da tela: exibe OP+operação com menos de duas inspeções. */
export const AUDITORIA_DEFAULT_STATUS: AuditoriaInspecaoStatus =
  AUDITORIA_STATUS_ABAIXO_MINIMO;

export const AUDITORIA_STATUS_OPTIONS: ReadonlyArray<{
  value: AuditoriaInspecaoStatus;
  label: string;
}> = [
  { value: AUDITORIA_STATUS_ALL, label: "Todos" },
  { value: AUDITORIA_STATUS_ABAIXO_MINIMO, label: "Abaixo de 2 inspeções" },
  { value: AUDITORIA_STATUS_MINIMO_ATINGIDO, label: "Mínimo atingido (2+)" },
  { value: AUDITORIA_STATUS_NAO_INSPECIONOU, label: "Não inspecionou (0)" },
  { value: AUDITORIA_STATUS_INSPECIONOU, label: "Inspecionou (1+)" },
  {
    value: AUDITORIA_STATUS_SEM_CADASTRO,
    label: "Não possui inspeção cadastrada",
  },
];
