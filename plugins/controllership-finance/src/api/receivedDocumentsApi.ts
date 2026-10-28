/** Cliente da BFF — projeção documental do destinatário externo (DRE-019).
 *
 * Contrato: `GET|POST /closing/received-documents*` — superfície restrita
 * da capability `controllership-finance.access.dre` (RW03 — única; a
 * legada `closing-documents.read` foi descontinuada). O MFE
 * nunca consulta Core nem rotas internas nesta experiência: a BFF
 * revalida capability + vínculo RECIPIENT + pacote SUBMITTED + membership
 * do recurso por request (existência fora do conjunto liberado é 404).
 *
 * Mensagens do destinatário são sempre `SHARED`; solicitações de ajuste
 * seguem OPEN → ANSWERED → CONFIRMED — responder não encerra, concluir
 * é ato do requerente. Retry reutiliza a mesma `idempotency_key` — o
 * backend deduplica (`deduplicated`), divergente é 409.
 */
import {
  cfApiUrl,
  httpGet,
  httpGetBlob,
  httpPost,
} from "./httpClient";

type Envelope<T> = { success: boolean; data?: T | null };

export type ReceivedDelivery = {
  period: string;
  recipient_area: string;
  version_no: number;
  submitted_at: string | null;
  document_count: number;
};

export type ReceivedDocument = {
  document_id: string;
  item_key: string | null;
  item_name: string | null;
  recipient_area: string | null;
  title: string | null;
  link_kind: string | null;
  original_name: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  version_no: number;
  released_at: string | null;
};

export type ReceivedDocumentVersion = {
  version_no: number;
  state: string;
  original_name: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  created_at: string | null;
};

export type ReceivedAdjustmentRequest = {
  request_id: string;
  document_id: string;
  version_no: number | null;
  state: "OPEN" | "ANSWERED" | "CONFIRMED" | string;
  body: string;
  requester_subject: string;
  requester_name: string | null;
  answer_body: string | null;
  answered_name: string | null;
  answered_at: string | null;
  confirmed_at: string | null;
  created_at: string | null;
  deduplicated?: boolean;
};

export type ReceivedDeliveryDetail = {
  period: string;
  deliveries: {
    recipient_area: string;
    version_no: number;
    submitted_at: string | null;
  }[];
  documents: ReceivedDocument[];
  requests: ReceivedAdjustmentRequest[];
};

export type ReceivedDocumentDetail = {
  document: ReceivedDocument;
  versions: ReceivedDocumentVersion[];
};

export type ReceivedMessage = {
  message_id: string;
  document_id: string;
  competence_id: string;
  version_no: number | null;
  audience: string;
  body: string;
  author_subject: string;
  author_name: string | null;
  created_at: string | null;
  mine?: boolean;
  deduplicated?: boolean;
};

export type ReceivedMessageListResult = {
  messages: ReceivedMessage[];
  total: number;
  limit: number;
  offset: number;
};

function base(period?: string): string {
  return period
    ? `/closing/received-documents/${period}`
    : "/closing/received-documents";
}

/** «Fechamentos recebidos» — entregas correntes do ator. */
export async function listReceivedDeliveries(options?: {
  signal?: AbortSignal;
}): Promise<ReceivedDelivery[]> {
  const envelope = await httpGet<
    Envelope<{ deliveries: ReceivedDelivery[] }>
  >(cfApiUrl(base()), options);
  return envelope?.data?.deliveries ?? [];
}

/** Entrega da competência: envios vigentes + documentos liberados +
 * solicitações do próprio ator. */
export async function getReceivedDelivery(
  period: string,
  options?: { signal?: AbortSignal },
): Promise<ReceivedDeliveryDetail> {
  const envelope = await httpGet<Envelope<ReceivedDeliveryDetail>>(
    cfApiUrl(base(period)),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Entrega não encontrada.");
  }
  return envelope.data;
}

/** Detalhe do documento liberado + versões autorizadas. */
export async function getReceivedDocument(
  period: string,
  documentId: string,
  options?: { signal?: AbortSignal },
): Promise<ReceivedDocumentDetail> {
  const envelope = await httpGet<Envelope<ReceivedDocumentDetail>>(
    cfApiUrl(`${base(period)}/documents/${documentId}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Documento não encontrado.");
  }
  return envelope.data;
}

/** Download autenticado de versão liberada — bytes só após a
 * autorização de membership no conjunto liberado. */
export async function downloadReceivedDocumentVersion(
  period: string,
  documentId: string,
  versionNo: number,
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  return httpGetBlob(
    cfApiUrl(
      `${base(period)}/documents/${documentId}` +
        `/versions/${versionNo}/content`,
    ),
    options,
  );
}

/** Persiste o blob com o nome original do servidor (mesmo helper do
 * contrato interno). */
export { saveDocumentBlob } from "./documentsApi";

/** Conversa compartilhada do documento liberado — somente SHARED. */
export async function listReceivedDocumentMessages(
  period: string,
  documentId: string,
  query: { limit?: number; offset?: number } = {},
  options?: { signal?: AbortSignal },
): Promise<ReceivedMessageListResult> {
  const search = new URLSearchParams();
  if (query.limit !== undefined) search.set("limit", String(query.limit));
  if (query.offset !== undefined)
    search.set("offset", String(query.offset));
  const qs = search.toString();
  const envelope = await httpGet<Envelope<ReceivedMessageListResult>>(
    cfApiUrl(
      `${base(period)}/documents/${documentId}/messages` +
        `${qs ? `?${qs}` : ""}`,
    ),
    options,
  );
  return (
    envelope?.data ?? { messages: [], total: 0, limit: 100, offset: 0 }
  );
}

/** Mensagem do destinatário — sempre SHARED; o servidor define autor,
 * data e contexto da versão liberada. */
export async function postReceivedDocumentMessage(
  period: string,
  documentId: string,
  input: { body: string; idempotencyKey: string },
  options?: { signal?: AbortSignal },
): Promise<ReceivedMessage> {
  const envelope = await httpPost<Envelope<ReceivedMessage>>(
    cfApiUrl(`${base(period)}/documents/${documentId}/messages`),
    { body: input.body, idempotency_key: input.idempotencyKey },
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia ao enviar a mensagem.");
  }
  return envelope.data;
}

/** Solicitações do próprio ator no documento liberado. */
export async function listReceivedAdjustmentRequests(
  period: string,
  documentId: string,
  options?: { signal?: AbortSignal },
): Promise<ReceivedAdjustmentRequest[]> {
  const envelope = await httpGet<
    Envelope<{ requests: ReceivedAdjustmentRequest[] }>
  >(
    cfApiUrl(
      `${base(period)}/documents/${documentId}/adjustment-requests`,
    ),
    options,
  );
  return envelope?.data?.requests ?? [];
}

/** Solicitação de esclarecimento/revisão — autor, data e versão
 * contextual vêm do servidor; replay idempotente deduplica. */
export async function createReceivedAdjustmentRequest(
  period: string,
  documentId: string,
  input: { body: string; idempotencyKey: string },
  options?: { signal?: AbortSignal },
): Promise<ReceivedAdjustmentRequest> {
  const envelope = await httpPost<Envelope<ReceivedAdjustmentRequest>>(
    cfApiUrl(
      `${base(period)}/documents/${documentId}/adjustment-requests`,
    ),
    { body: input.body, idempotency_key: input.idempotencyKey },
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia ao registrar a solicitação.");
  }
  return envelope.data;
}

/** Conclusão pelo requerente — ANSWERED → CONFIRMED. */
export async function confirmReceivedAdjustmentRequest(
  period: string,
  documentId: string,
  requestId: string,
  options?: { signal?: AbortSignal },
): Promise<ReceivedAdjustmentRequest> {
  const envelope = await httpPost<Envelope<ReceivedAdjustmentRequest>>(
    cfApiUrl(
      `${base(period)}/documents/${documentId}` +
        `/adjustment-requests/${requestId}/confirm`,
    ),
    {},
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia ao concluir a solicitação.");
  }
  return envelope.data;
}
