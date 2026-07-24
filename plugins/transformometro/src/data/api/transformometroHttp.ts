import { describeHttpError } from "../../utils/apiErrorMessage";

export type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
  detail?: unknown;
};

function detailFromBody(body: { message?: string; detail?: unknown }): string {
  if (typeof body.message === "string" && body.message.trim()) {
    return body.message.trim();
  }
  if (typeof body.detail === "string" && body.detail.trim()) {
    return body.detail.trim();
  }
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((item: { msg?: string; loc?: unknown[] }) => {
        const loc = Array.isArray(item.loc) ? item.loc.join(".") : "";
        return loc ? `${loc}: ${item.msg ?? ""}` : (item.msg ?? "");
      })
      .filter(Boolean)
      .join("; ");
  }
  return "";
}

/**
 * Lê envelope JSON da API Transformômetro.
 * Respostas HTML (ex.: 429 do Nginx) viram mensagem amigável — nunca "Unexpected token '<'".
 */
export async function parseApiEnvelope<T>(response: Response): Promise<T> {
  let body: ApiEnvelope<T>;
  try {
    body = (await response.json()) as ApiEnvelope<T>;
  } catch {
    if (response.ok) {
      throw new Error("Resposta inválida da API.");
    }
    throw new Error(describeHttpError(response.status));
  }

  if (!response.ok || !body.success) {
    throw new Error(describeHttpError(response.status, detailFromBody(body)));
  }
  return body.data;
}
