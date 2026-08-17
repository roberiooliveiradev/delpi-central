import type { NotificationType } from "../data/coreApi";

export type NotificationSeverityTone = NotificationType;

export type NotificationSeverityToneResolved = {
  tone: NotificationSeverityTone;
  labelPt: string;
  /** CSS modifier without leading dashes, e.g. `warning` */
  cssModifier: NotificationSeverityTone;
  /** Short eyebrow for the important attention panel */
  attentionEyebrow: string;
};

const TONE_BY_ALIAS: Record<string, NotificationSeverityTone> = {
  info: "info",
  success: "success",
  warning: "warning",
  error: "error",
  aviso: "info",
  informacao: "info",
  informação: "info",
  atencao: "warning",
  atenção: "warning",
  alerta: "error",
  erro: "error",
  sucesso: "success",
};

const LABEL_PT: Record<NotificationSeverityTone, string> = {
  info: "Aviso",
  success: "Sucesso",
  warning: "Atenção",
  error: "Alerta",
};

const ATTENTION_EYEBROW: Record<NotificationSeverityTone, string> = {
  info: "Aviso importante",
  success: "Sucesso importante",
  warning: "Atenção importante",
  error: "Alerta importante",
};

/** Canonical severity for UI tones (blue / green / yellow / red). */
export function resolveNotificationSeverityTone(
  type: string | null | undefined,
): NotificationSeverityToneResolved {
  const raw = (type || "info").trim().toLowerCase();
  const tone = TONE_BY_ALIAS[raw] ?? "info";
  return {
    tone,
    labelPt: LABEL_PT[tone],
    cssModifier: tone,
    attentionEyebrow: ATTENTION_EYEBROW[tone],
  };
}

export const NOTIFICATION_TYPE_OPTIONS: Array<{
  value: NotificationType;
  label: string;
}> = [
  { value: "info", label: "Aviso (info)" },
  { value: "success", label: "Sucesso (success)" },
  { value: "warning", label: "Atenção (warning)" },
  { value: "error", label: "Alerta (error)" },
];
