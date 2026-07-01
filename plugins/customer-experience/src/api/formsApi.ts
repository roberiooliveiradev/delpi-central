import {
  httpDelete,
  httpDownloadBlob,
  httpGet,
  httpPatchJson,
  httpPost,
  httpPostJson,
  httpPutJson,
  unwrapEnvelope,
  type ApiEnvelope,
} from "./httpClient";
import type {
  CreateFormInput,
  FormDashboard,
  FormDetail,
  FormQuestion,
  FormResponseList,
  FormSummary,
} from "../types";

const API_BASE = "/apps/customer-experience-api";
const FORMS = `${API_BASE}/forms`;

export async function listForms(): Promise<FormSummary[]> {
  const response = await httpGet<ApiEnvelope<{ items: FormSummary[] }>>(FORMS);
  return unwrapEnvelope(response, "Não foi possível listar os formulários.").items;
}

export async function getForm(id: string): Promise<FormDetail> {
  const response = await httpGet<ApiEnvelope<FormDetail>>(`${FORMS}/${id}`);
  return unwrapEnvelope(response, "Não foi possível carregar o formulário.");
}

export async function createForm(input: CreateFormInput): Promise<FormDetail> {
  const response = await httpPostJson<ApiEnvelope<FormDetail>>(FORMS, {
    title: input.title,
    description: input.description ?? null,
  });
  return unwrapEnvelope(response, "Não foi possível criar o formulário.");
}

export async function updateForm(
  id: string,
  input: { title?: string; description?: string | null },
): Promise<FormDetail> {
  const response = await httpPatchJson<ApiEnvelope<FormDetail>>(`${FORMS}/${id}`, input);
  return unwrapEnvelope(response, "Não foi possível atualizar o formulário.");
}

export async function setQuestions(
  id: string,
  questions: FormQuestion[],
): Promise<FormDetail> {
  const payload = {
    questions: questions.map((q) => ({
      id: q.id,
      type: q.type,
      label: q.label,
      helpText: q.helpText,
      required: q.required,
      options: q.options,
    })),
  };
  const response = await httpPutJson<ApiEnvelope<FormDetail>>(
    `${FORMS}/${id}/questions`,
    payload,
  );
  return unwrapEnvelope(response, "Não foi possível salvar as perguntas.");
}

export async function activateForm(id: string): Promise<FormDetail> {
  const response = await httpPost<ApiEnvelope<FormDetail>>(`${FORMS}/${id}/activate`);
  return unwrapEnvelope(response, "Não foi possível publicar o formulário.");
}

export async function deactivateForm(id: string): Promise<FormDetail> {
  const response = await httpPost<ApiEnvelope<FormDetail>>(`${FORMS}/${id}/deactivate`);
  return unwrapEnvelope(response, "Não foi possível despublicar o formulário.");
}

export async function deleteForm(id: string): Promise<void> {
  const response = await httpDelete<ApiEnvelope<null>>(`${FORMS}/${id}`);
  unwrapEnvelope(response, "Não foi possível excluir o formulário.");
}

export async function downloadFormQr(id: string): Promise<Blob> {
  return httpDownloadBlob(`${FORMS}/${id}/qr`);
}

export async function getDashboard(id: string): Promise<FormDashboard> {
  const response = await httpGet<ApiEnvelope<FormDashboard>>(`${FORMS}/${id}/dashboard`);
  return unwrapEnvelope(response, "Não foi possível carregar o dashboard.");
}

export async function listResponses(
  id: string,
  params: { limit?: number; offset?: number } = {},
): Promise<FormResponseList> {
  const query = new URLSearchParams();
  if (params.limit != null) query.set("limit", String(params.limit));
  if (params.offset != null) query.set("offset", String(params.offset));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await httpGet<ApiEnvelope<FormResponseList>>(
    `${FORMS}/${id}/responses${suffix}`,
  );
  return unwrapEnvelope(response, "Não foi possível carregar as respostas.");
}
