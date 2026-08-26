import type { CompareSparklineTone, SeriesSparklineTone } from "@delpi/plugin-ui/index";

/** Em preventiva, golpes acima da média é ruim — inverte o tom padrão up/down. */
export function resolvePreventivaCompareSparklineTone(
  media: number,
  golpesAtuais: number,
): CompareSparklineTone {
  if (!Number.isFinite(media) || !Number.isFinite(golpesAtuais)) return "flat";
  if (golpesAtuais > media) return "down";
  if (golpesAtuais < media) return "up";
  return "flat";
}

export function resolvePreventivaSeriesSparklineTone(status: string): SeriesSparklineTone {
  if (status === "CRÍTICO") return "danger";
  if (status === "ATENÇÃO") return "warning";
  if (status === "OK") return "success";
  return "default";
}
