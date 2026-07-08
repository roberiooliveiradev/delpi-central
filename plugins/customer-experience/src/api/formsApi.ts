import {
  httpDelete,
  httpDownloadBlob,
  httpGet,
  httpPatchJson,
  httpPost,
  httpPostForm,
  httpPostJson,
  httpPutJson,
  unwrapEnvelope,
  type ApiEnvelope,
} from "./httpClient";
import type {
  BackgroundFit,
  CreateFormInput,
  FormDashboard,
  FormDetail,
  FormPage,
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
    oneQuestionPerPage: input.oneQuestionPerPage ?? false,
  });
  return unwrapEnvelope(response, "Não foi possível criar o formulário.");
}

export async function duplicateForm(id: string): Promise<FormDetail> {
  const response = await httpPost<ApiEnvelope<FormDetail>>(`${FORMS}/${id}/duplicate`);
  return unwrapEnvelope(response, "Não foi possível duplicar o formulário.");
}

export async function updateForm(
  id: string,
  input: {
    title?: string;
    description?: string | null;
    oneQuestionPerPage?: boolean;
    backgroundFit?: BackgroundFit;
  },
): Promise<FormDetail> {
  const response = await httpPatchJson<ApiEnvelope<FormDetail>>(`${FORMS}/${id}`, input);
  return unwrapEnvelope(response, "Não foi possível atualizar o formulário.");
}

export async function setQuestions(
  id: string,
  input: {
    questions: FormQuestion[];
    pages?: FormPage[];
    oneQuestionPerPage?: boolean;
  },
): Promise<FormDetail> {
  const payload = {
    oneQuestionPerPage: input.oneQuestionPerPage,
    pages: (input.pages ?? []).map((p) => ({
      id: p.id,
      title: p.title,
      pointImageFit: p.pointImageFit ?? "scale",
      pointIcon: p.pointIcon ?? null,
    })),
    questions: input.questions.map((q) => ({
      id: q.id,
      type: q.type,
      label: q.label,
      helpText: q.helpText,
      required: q.required,
      options: q.options,
      pageId: q.pageId,
      pageIndex: q.pageIndex ?? undefined,
      pointImageFit: q.pointImageFit ?? "scale",
      pointIcon: q.pointIcon ?? null,
    })),
  };
  const response = await httpPutJson<ApiEnvelope<FormDetail>>(
    `${FORMS}/${id}/questions`,
    payload,
  );
  return unwrapEnvelope(response, "Não foi possível salvar as perguntas.");
}

async function uploadMultipart(url: string, file: File): Promise<FormDetail> {
  const body = new FormData();
  body.append("image", file);
  const response = await httpPostForm<ApiEnvelope<FormDetail>>(url, body);
  return unwrapEnvelope(response, "Não foi possível enviar a imagem.");
}

export async function uploadFormBackground(id: string, file: File): Promise<FormDetail> {
  return uploadMultipart(`${FORMS}/${id}/background-image`, file);
}

export async function removeFormBackground(id: string): Promise<FormDetail> {
  const response = await httpDelete<ApiEnvelope<FormDetail>>(`${FORMS}/${id}/background-image`);
  return unwrapEnvelope(response, "Não foi possível remover a imagem de fundo.");
}

export async function uploadPageBackground(
  formId: string,
  pageId: string,
  file: File,
): Promise<FormDetail> {
  return uploadMultipart(`${FORMS}/${formId}/pages/${pageId}/background-image`, file);
}

export async function uploadPagePointImage(
  formId: string,
  pageId: string,
  file: File,
): Promise<FormDetail> {
  return uploadMultipart(`${FORMS}/${formId}/pages/${pageId}/point-image`, file);
}

export async function uploadQuestionPointImage(
  formId: string,
  questionId: string,
  file: File,
): Promise<FormDetail> {
  return uploadMultipart(`${FORMS}/${formId}/questions/${questionId}/point-image`, file);
}

export async function removePageBackground(
  formId: string,
  pageId: string,
): Promise<FormDetail> {
  const response = await httpDelete<ApiEnvelope<FormDetail>>(
    `${FORMS}/${formId}/pages/${pageId}/background-image`,
  );
  return unwrapEnvelope(response, "Não foi possível remover o fundo da página.");
}

export async function removePagePointImage(
  formId: string,
  pageId: string,
): Promise<FormDetail> {
  const response = await httpDelete<ApiEnvelope<FormDetail>>(
    `${FORMS}/${formId}/pages/${pageId}/point-image`,
  );
  return unwrapEnvelope(response, "Não foi possível remover a imagem ilustrativa da página.");
}

export async function removeQuestionPointImage(
  formId: string,
  questionId: string,
): Promise<FormDetail> {
  const response = await httpDelete<ApiEnvelope<FormDetail>>(
    `${FORMS}/${formId}/questions/${questionId}/point-image`,
  );
  return unwrapEnvelope(response, "Não foi possível remover a imagem ilustrativa da pergunta.");
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
