import { httpPost } from "./httpClient";
import type {
  DisplayFormatPreviewRequest,
  DisplayFormatPreviewResponse,
} from "@delpi/plugin-ui/index";

type Envelope<T> = {
  success?: boolean;
  data?: T;
  message?: string;
};

/**
 * Batch format catalog + previews — server authority (FORMAT-001).
 * One request for all options; never format locally for picker previews.
 */
export async function fetchDisplayFormatPreviews(
  request: DisplayFormatPreviewRequest,
): Promise<DisplayFormatPreviewResponse> {
  const envelope = await httpPost<Envelope<DisplayFormatPreviewResponse>>(
    "/apps/tv-dashboard-api/data/display-format/previews",
    {
      value: request.value,
      semanticType: request.semanticType ?? null,
      locale: request.locale ?? "pt-BR",
      timezone: request.timezone ?? null,
      valueSource: request.valueSource ?? "authoritative",
      customPattern: request.customPattern ?? null,
      selectedSpec: request.selectedSpec ?? null,
    },
  );
  if (!envelope?.data || !Array.isArray(envelope.data.options)) {
    throw new Error(envelope?.message || "Resposta de formato inválida.");
  }
  return envelope.data;
}
