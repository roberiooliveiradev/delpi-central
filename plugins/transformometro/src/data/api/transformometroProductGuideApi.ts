import {
  TRANSFORMOMETRO_API_BASE,
  buildAuthHeaders,
} from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";

/** Help view served by GET /transformometro/product-guides — public
 * fields only; internal refs (capability/contract/source) stay backend. */
export type ProductGuideHelpTopic = {
  id: string;
  title: string;
  summary: string;
  purpose?: string;
  use_when?: string[];
  do_not_use_when?: string[];
  how_to_use?: string[];
  quality_rules?: string[];
  common_mistakes?: string[];
  related_topics?: string[];
};

export type ProductGuideHelpResponse = {
  schema: string;
  registry_version: string;
  topics: ProductGuideHelpTopic[];
};

export async function fetchProductGuideHelp(
  getAccessToken?: () => string | undefined,
): Promise<ProductGuideHelpResponse> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/product-guides?view=help`,
    { headers: buildAuthHeaders(getAccessToken) },
  );
  return parseApiEnvelope<ProductGuideHelpResponse>(response);
}
