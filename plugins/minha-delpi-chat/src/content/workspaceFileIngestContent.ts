import attachmentsContent from "./attachments_content.json";

export type WorkspaceFileDropzoneContentVariant =
  | "session"
  | "workspace"
  | "agent"
  | "project"
  | "context";

type ReadingStatusKey = keyof typeof attachmentsContent.preview.readingStatus;

export type WorkspaceFileStatusTone = "default" | "pending" | "success" | "error";

export type WorkspaceFileIconTone = "brand" | "pdf" | "image" | "pending" | "error";

const READING_STATUS = attachmentsContent.preview.readingStatus;
const INGEST_UI = attachmentsContent.ingestUi;

function normalizeStatus(status?: string | null): string {
  return String(status || "").trim().toLowerCase();
}

function readingStatusFromKey(key: ReadingStatusKey | "default"): string {
  return READING_STATUS[key] || READING_STATUS.default;
}

export function workspaceFileReadingStatusLabel(
  status?: string | null,
  parsed?: boolean,
): string {
  const normalized = normalizeStatus(status);

  if (parsed || normalized === "indexed") {
    return readingStatusFromKey("indexed");
  }

  if (normalized === "indexing") {
    return readingStatusFromKey("indexing");
  }

  if (normalized === "uploading" || normalized === "uploaded") {
    return readingStatusFromKey("uploading");
  }

  if (normalized === "unsupported") {
    return readingStatusFromKey("unsupported");
  }

  if (normalized === "index_failed" || normalized === "failed") {
    return readingStatusFromKey("index_failed");
  }

  if (normalized === "queued") {
    return readingStatusFromKey("default");
  }

  if (normalized in READING_STATUS) {
    return readingStatusFromKey(normalized as ReadingStatusKey);
  }

  return readingStatusFromKey("default");
}

export function workspaceFileKindLabel(filename: string): string {
  const normalized = String(filename || "").trim().toLowerCase();
  const extension = normalized.includes(".") ? normalized.split(".").pop() : "";

  if (!extension) {
    return INGEST_UI.project.fileKindLabel;
  }

  if (extension === "pdf") {
    return "PDF";
  }

  if (extension === "md" || extension === "markdown") {
    return "MD";
  }

  if (extension === "docx") {
    return "DOCX";
  }

  if (extension === "xlsx") {
    return "XLSX";
  }

  if (extension === "csv") {
    return "CSV";
  }

  if (extension === "txt") {
    return "TXT";
  }

  if (extension === "json") {
    return "JSON";
  }

  return extension.toUpperCase();
}

export function workspaceFileIconToneForAttachment(
  filename: string,
  previewKind: "image" | "file",
  statusTone: WorkspaceFileStatusTone,
): WorkspaceFileIconTone {
  if (statusTone === "error") {
    return "error";
  }

  if (statusTone === "pending") {
    return "pending";
  }

  if (previewKind === "image") {
    return "image";
  }

  if (workspaceFileKindLabel(filename) === "PDF") {
    return "pdf";
  }

  return "brand";
}

export function workspaceFileReadingStatusTone(
  status?: string | null,
  parsed?: boolean,
): WorkspaceFileStatusTone {
  const normalized = normalizeStatus(status);

  if (parsed || normalized === "indexed") {
    return "success";
  }

  if (
    normalized === "indexing" ||
    normalized === "uploading" ||
    normalized === "uploaded" ||
    normalized === "queued"
  ) {
    return "pending";
  }

  if (normalized === "unsupported" || normalized === "index_failed" || normalized === "failed") {
    return "error";
  }

  return "default";
}

export function workspaceFileDropzoneContent(
  variant: WorkspaceFileDropzoneContentVariant = "workspace",
) {
  const hintByVariant = {
    session: INGEST_UI.dropzone.hintSession,
    workspace: INGEST_UI.dropzone.hintWorkspace,
    agent: INGEST_UI.dropzone.hintAgent,
    project: INGEST_UI.dropzone.hintProject,
    context: INGEST_UI.dropzone.hintContext,
  } as const;

  return {
    title: INGEST_UI.dropzone.title,
    hint: hintByVariant[variant],
    actionAdd: INGEST_UI.dropzone.actionAdd,
    actionSelect: INGEST_UI.dropzone.actionSelect,
  };
}

export function workspaceFileComposerAttachmentsHeader(count: number): string {
  return INGEST_UI.composer.attachmentsHeader.replace("{count}", String(count));
}

export function workspaceFileMessageEditAttachmentsHeader(count: number): string {
  return INGEST_UI.messageEdit.attachmentsHeader.replace("{count}", String(count));
}

export function workspaceFileMessageEditLabels() {
  return INGEST_UI.messageEdit;
}

export function workspaceFileComposerLabels() {
  return {
    clearAttachments: INGEST_UI.composer.clearAttachments,
    attachMenuLabel: INGEST_UI.composer.attachMenuLabel,
  };
}

export function workspaceFileAgentIngestLabels() {
  return INGEST_UI.agent;
}

export function workspaceFileProjectIngestLabels() {
  return INGEST_UI.project;
}

export function workspaceFileProjectFileKindLabel(date?: string): string {
  if (!date?.trim()) {
    return INGEST_UI.project.fileKindLabel;
  }

  return INGEST_UI.project.fileKindWithDate.replace("{date}", date.trim());
}

export function workspaceFileContextIngestLabels() {
  return INGEST_UI.context;
}

export function workspaceFileContextBinaryLine(name: string, type: string): string {
  return INGEST_UI.context.binaryFileLine
    .replace("{name}", name)
    .replace("{type}", type || "binário");
}
