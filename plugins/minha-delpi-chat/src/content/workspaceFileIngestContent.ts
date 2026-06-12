import attachmentsContent from "./attachments_content.json";

type ReadingStatusKey = keyof typeof attachmentsContent.preview.readingStatus;

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

export function workspaceFileDropzoneContent(
  variant: "session" | "workspace" | "agent" | "project" | "context" = "workspace",
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
