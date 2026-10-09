/** Parser do payload «Processos — Abertura de Chamado» (general-request). */

export type GeneralRequestPayloadView = {
  title: string | null;
  description: string | null;
};

function text(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  const str = String(value).trim();
  return str || null;
}

export function parseGeneralRequestPayload(
  payload: Record<string, unknown> | null | undefined,
): GeneralRequestPayloadView {
  const source = payload && typeof payload === "object" ? payload : {};
  return {
    title: text(source.title),
    description: text(source.description),
  };
}
