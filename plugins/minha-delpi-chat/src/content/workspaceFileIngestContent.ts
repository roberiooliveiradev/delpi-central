import attachmentsContent from "./attachments_content.json";
import { ingestProgressPercentLabel } from "./ingestProgress";

export type WorkspaceFileDropzoneContentVariant =
  | "session"
  | "workspace"
  | "agent"
  | "project"
  | "context";

type ReadingStatusKey = keyof typeof attachmentsContent.preview.readingStatus;

export type WorkspaceFileStatusTone = "default" | "pending" | "success" | "error";

export type WorkspaceFileIconTone = "brand" | "pdf" | "image" | "pending" | "error";

export type WorkspaceFileIngestProgress = {
  active: boolean;
  percent?: number | null;
  label?: string;
};

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
  _filename: string,
  previewKind: "image" | "file",
  statusTone: WorkspaceFileStatusTone,
): WorkspaceFileIconTone {
  if (statusTone === "error") {
    return "error";
  }

  if (previewKind === "image") {
    return "image";
  }

  return "brand";
}

export function workspaceFileComposerAttachmentStatusLabel(input: {
  status?: string | null;
  parsed?: boolean;
  readingStatus?: string | null;
  uploadPercent?: number;
}): string | undefined {
  const indexPresentation = workspaceFileAttachmentIndexPresentation(input);
  const baseStatusLabel = indexPresentation.statusLabel;
  const normalizedStatus = normalizeStatus(input.status);

  if (
    (normalizedStatus === "uploading" || normalizedStatus === "queued") &&
    typeof input.uploadPercent === "number"
  ) {
    const progressLabel = ingestProgressPercentLabel(input.uploadPercent);
    const uploadLabel = workspaceFileReadingStatusLabel("uploading");

    if (baseStatusLabel && baseStatusLabel !== workspaceFileReadingStatusLabel("default")) {
      return `${baseStatusLabel} · ${progressLabel}`;
    }

    return `${uploadLabel} · ${progressLabel}`;
  }

  return baseStatusLabel;
}

export function workspaceFileIngestProgressState(input: {
  status?: string | null;
  uploadPercent?: number | null;
  label?: string;
}): WorkspaceFileIngestProgress | undefined {
  const normalized = normalizeStatus(input.status);

  if (
    normalized !== "queued" &&
    normalized !== "uploading" &&
    normalized !== "uploaded" &&
    normalized !== "indexing"
  ) {
    return undefined;
  }

  return {
    active: true,
    percent: input.uploadPercent,
    label: input.label,
  };
}

export type WorkspaceFileIndexPresentation = {
  statusLabel?: string;
  statusTone: WorkspaceFileStatusTone;
};

export function workspaceFileIndexPresentation(input: {
  chunkCount?: number | null;
  status?: string | null;
  parsed?: boolean;
  readingStatus?: string | null;
  indexStatus?: string | null;
}): WorkspaceFileIndexPresentation {
  if ((input.chunkCount ?? 0) > 0 || input.parsed) {
    return {
      statusLabel: workspaceFileReadingStatusLabel("indexed", true),
      statusTone: workspaceFileReadingStatusTone("indexed", true),
    };
  }

  const raw =
    (typeof input.readingStatus === "string" && input.readingStatus.trim()) ||
    (typeof input.indexStatus === "string" && input.indexStatus.trim()) ||
    (typeof input.status === "string" && input.status.trim()) ||
    null;

  if (!raw) {
    return { statusTone: "default" };
  }

  const normalized = raw.toLowerCase();

  return {
    statusLabel: workspaceFileReadingStatusLabel(normalized, false),
    statusTone: workspaceFileReadingStatusTone(normalized, false),
  };
}

export function workspaceFileSourceIndexPresentation(source: {
  chunk_count?: number | null;
  metadata?: Record<string, unknown> | null;
}): WorkspaceFileIndexPresentation {
  const metadata = source.metadata;

  return workspaceFileIndexPresentation({
    chunkCount: source.chunk_count,
    readingStatus:
      typeof metadata?.readingStatus === "string" ? metadata.readingStatus : null,
    indexStatus: typeof metadata?.indexStatus === "string" ? metadata.indexStatus : null,
    status: typeof metadata?.status === "string" ? metadata.status : null,
  });
}

export function workspaceFileAttachmentIndexPresentation(input: {
  status?: string | null;
  parsed?: boolean;
  readingStatus?: string | null;
}): WorkspaceFileIndexPresentation {
  const parsed =
    input.parsed === true ||
    normalizeStatus(input.status) === "indexed" ||
    input.status === "indexed";

  const effectiveStatus = input.readingStatus?.trim() || input.status;

  if (!effectiveStatus && !parsed) {
    return { statusTone: "default" };
  }

  return {
    statusLabel: workspaceFileReadingStatusLabel(effectiveStatus, parsed),
    statusTone: workspaceFileReadingStatusTone(effectiveStatus, parsed),
  };
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
    uploadingStatus: INGEST_UI.messageEdit.uploadingStatus,
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
