import type { CompareSparklineTone } from "@delpi/plugin-ui/index";

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
