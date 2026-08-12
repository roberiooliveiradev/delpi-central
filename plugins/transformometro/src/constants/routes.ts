export const TRANSFORMOMETRO_ROUTES = {
  home: "/apps/transformometro",
  dashboard: "/apps/transformometro/dashboard",
  processes: "/apps/transformometro/processes",
  /** @deprecated alias — use `processes` */
  processos: "/apps/transformometro/processes",
  meetingMinutes: "/apps/transformometro/meeting-minutes",
  /** @deprecated alias — use `meetingMinutes` */
  atas: "/apps/transformometro/meeting-minutes",
  meetingMinutesPending: "/apps/transformometro/meeting-minutes/pending",
  /** @deprecated alias — use `meetingMinutesPending` */
  atasPending: "/apps/transformometro/meeting-minutes/pending",
  mySignature: "/apps/transformometro/my-signature",
  /** @deprecated alias — use `mySignature` */
  minhaAssinatura: "/apps/transformometro/my-signature",
  settings: "/apps/transformometro/settings",
  /** @deprecated alias — use `settings` */
  configuracoes: "/apps/transformometro/settings",
  settingsUnits: "/apps/transformometro/settings/units",
  /** @deprecated alias — use `settingsUnits` */
  configuracoesUnidades: "/apps/transformometro/settings/units",
  settingsDepartments: "/apps/transformometro/settings/departments",
  /** @deprecated alias — use `settingsDepartments` */
  configuracoesDepartamentos: "/apps/transformometro/settings/departments",
  settingsSharedResources: "/apps/transformometro/settings/shared-resources",
  /** @deprecated alias — use `settingsSharedResources` */
  configuracoesRecursos: "/apps/transformometro/settings/shared-resources",
  /** @deprecated use settingsUnits */
  filiais: "/apps/transformometro/settings/units",
  /** @deprecated use settingsDepartments */
  setores: "/apps/transformometro/settings/departments",
  /** @deprecated use settingsSharedResources */
  recursos: "/apps/transformometro/settings/shared-resources",
  data: "/apps/transformometro/data",
  /** @deprecated alias — use `data` */
  dados: "/apps/transformometro/data",
} as const;

export function buildAtaPath(ataId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.meetingMinutes}/${ataId}`;
}

export function buildAtaEditPath(ataId: string): string {
  return `${buildAtaPath(ataId)}/edit`;
}

export function buildAtaSignPath(ataId: string): string {
  return `${buildAtaPath(ataId)}/sign`;
}

export function buildMeetingMinutePath(minuteId: string): string {
  return buildAtaPath(minuteId);
}

export function buildMeetingMinuteEditPath(minuteId: string): string {
  return buildAtaEditPath(minuteId);
}

export function buildMeetingMinuteSignPath(minuteId: string): string {
  return buildAtaSignPath(minuteId);
}
