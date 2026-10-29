/**
 * Delega no cliente HTTP canônico do Portal Engenharia
 * (`src/api/httpClient.ts`): mesmo Bearer do host, caller-app
 * "engineering", timeout e classificação de erros — sem segunda fonte
 * de token ou política de resiliência.
 */

import {
  getJson,
  HomeApiError,
  type HomeApiErrorKind,
} from "../../../api/httpClient";

export type LmpApiErrorKind = HomeApiErrorKind;
export { HomeApiError as LmpApiError };

export async function httpGet<T>(
  url: string,
  options: { signal?: AbortSignal } = {},
): Promise<T> {
  return getJson<T>(url, options.signal);
}
