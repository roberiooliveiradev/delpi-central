import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import {
  commercialApiUrl,
  httpDelete,
  httpGet,
  httpPatch,
  httpPost,
} from "./httpClient";

export type AccountContactChannel =
  | "phone"
  | "mobile"
  | "email"
  | "whatsapp"
  | "other";

export type TotvsAccountContact = {
  full_name: string | null;
  phone: string | null;
  email: string | null;
  source: "totvs";
  read_only: true;
};

export type AccountContact = {
  id: string;
  customer_code: string;
  customer_store: string;
  full_name: string;
  role_title: string | null;
  channel: AccountContactChannel;
  email: string | null;
  phone_e164: string | null;
  is_whatsapp: boolean;
  is_primary: boolean;
  source: string;
  created_at: string;
  updated_at: string;
};

export type AccountContactsBundle = {
  totvs_contact: TotvsAccountContact | null;
  items: AccountContact[];
};

export type AccountContactInput = {
  full_name: string;
  role_title?: string | null;
  channel: AccountContactChannel;
  email?: string | null;
  phone_e164?: string | null;
  is_whatsapp: boolean;
  is_primary: boolean;
  source?: string;
};

function accountContactsPath(customerCode: string, customerStore: string): string {
  return commercialApiUrl(
    `/customers/${encodeURIComponent(customerCode)}/${encodeURIComponent(customerStore)}/contacts`,
  );
}

export async function getAccountContactsBundle(
  customerCode: string,
  customerStore: string,
  signal?: AbortSignal,
): Promise<AccountContactsBundle> {
  const response = await httpGet<ApiSuccessResponse<AccountContactsBundle>>(
    `${accountContactsPath(customerCode, customerStore)}-bundle`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar contatos.");
}

export async function createAccountContact(
  customerCode: string,
  customerStore: string,
  input: AccountContactInput,
): Promise<AccountContact> {
  const response = await httpPost<ApiSuccessResponse<AccountContact>>(
    accountContactsPath(customerCode, customerStore),
    input,
  );
  return unwrapEnvelope(response, "Erro ao criar contato.");
}

export async function updateAccountContact(
  customerCode: string,
  customerStore: string,
  contactId: string,
  input: AccountContactInput,
): Promise<AccountContact> {
  const response = await httpPatch<ApiSuccessResponse<AccountContact>>(
    `${accountContactsPath(customerCode, customerStore)}/${encodeURIComponent(contactId)}`,
    input,
  );
  return unwrapEnvelope(response, "Erro ao atualizar contato.");
}

export async function deleteAccountContact(
  customerCode: string,
  customerStore: string,
  contactId: string,
): Promise<void> {
  await httpDelete<ApiSuccessResponse<{ deleted: boolean; id: string }>>(
    `${accountContactsPath(customerCode, customerStore)}/${encodeURIComponent(contactId)}`,
  );
}
