/** Labels e helpers de anexos CAPEX — alinhados ao backend 2B.3. */

import { MAX_DOCUMENT_BYTES, validateClientUpload } from "./documentUpload";

export const CAPEX_ATTACHMENT_TYPE_OPTIONS = [
  { value: "quotation", label: "Orçamento" },
  { value: "commercial_proposal", label: "Proposta comercial" },
  { value: "technical_specification", label: "Especificação técnica" },
  { value: "image", label: "Imagem" },
  { value: "justification", label: "Justificativa" },
  { value: "other", label: "Outro documento" },
] as const;

export type CapexAttachmentUploadUiState =
  | "ready"
  | "uploading"
  | "processing"
  | "done"
  | "error";

export function attachmentTypeLabel(value?: string | null): string {
  if (!value) return "—";
  return CAPEX_ATTACHMENT_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function newAttachmentIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `att-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function uploadStatusLabel(state: CapexAttachmentUploadUiState): string {
  switch (state) {
    case "ready":
      return "Pronto para enviar";
    case "uploading":
      return "Enviando";
    case "processing":
      return "Processando";
    case "done":
      return "Concluído";
    case "error":
      return "Erro no envio";
    default:
      return "";
  }
}

export function formatAttachmentDate(value?: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("pt-BR");
}

/** Mensagens amigáveis a partir dos códigos estáveis do backend. */
export function mapCapexAttachmentError(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err ?? "");
  const lower = raw.toLowerCase();

  if (lower.includes("budget_capex_attachment_mime_invalid")) {
    return "O tipo MIME do arquivo não é permitido. Envie um formato aceito (PDF, Office, imagem etc.).";
  }
  if (lower.includes("budget_capex_attachment_extension_invalid")) {
    return "A extensão do arquivo não é permitida.";
  }
  if (lower.includes("budget_capex_attachment_too_large")) {
    return "O arquivo excede o limite de 25 MB.";
  }
  if (lower.includes("budget_capex_attachment_type_invalid")) {
    return "Selecione um tipo de anexo válido.";
  }
  if (lower.includes("budget_capex_investment_archived")) {
    return "Este investimento está arquivado. Não é possível adicionar anexos.";
  }
  if (lower.includes("budget_capex_attachment_archived")) {
    return "Este anexo já foi arquivado.";
  }
  if (
    lower.includes("budget_capex_attachment_not_found") ||
    lower.includes("budget_capex_investment_not_found")
  ) {
    return "Anexo ou investimento não encontrado, ou você não tem acesso a este centro de custo.";
  }
  if (lower.includes("budget_capex_attachment_forbidden")) {
    return "Acesso negado aos anexos CAPEX.";
  }
  if (lower.includes("budget_guidance_acknowledgement_required")) {
    return "Confirme a leitura das orientações vigentes antes de gerenciar anexos.";
  }
  if (lower.includes("budget_responsibility") || lower.includes("cost_center_forbidden")) {
    return "Você não possui responsabilidade válida neste centro de custo.";
  }
  if (err && typeof err === "object" && "status" in err) {
    const status = Number((err as { status?: number }).status);
    if (status === 401) return "Sessão expirada. Faça login novamente.";
    if (status === 403) return "Acesso negado a este recurso.";
    if (status === 404) return "Recurso não encontrado.";
    if (status === 0) return "Falha de rede. Verifique a conexão e tente novamente.";
  }
  if (lower.includes("network") || lower.includes("falha de rede")) {
    return "Falha de rede. Verifique a conexão e tente novamente.";
  }
  const cleaned = raw.replace(/^\[[^\]]+]\s*/, "").trim();
  return cleaned || "Não foi possível concluir a operação com o anexo.";
}

export type AttachmentFormValidation =
  | { ok: true }
  | { ok: false; message: string };

export function validateAttachmentUploadForm(input: {
  file: File | null;
  displayName: string;
  attachmentType: string;
}): AttachmentFormValidation {
  if (!input.file) {
    return { ok: false, message: "Selecione um arquivo." };
  }
  if (!input.displayName.trim()) {
    return { ok: false, message: "Informe o nome de exibição." };
  }
  if (!input.attachmentType.trim()) {
    return { ok: false, message: "Selecione o tipo de anexo." };
  }
  const fileCheck = validateClientUpload(input.file);
  if (!fileCheck.ok) {
    return fileCheck;
  }
  if (input.file.size > MAX_DOCUMENT_BYTES) {
    return { ok: false, message: "Arquivo excede o limite de 25 MB." };
  }
  return { ok: true };
}

export function triggerBrowserDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename || "anexo";
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
