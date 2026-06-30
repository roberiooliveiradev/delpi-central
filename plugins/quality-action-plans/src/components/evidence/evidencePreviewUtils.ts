import type { PlanEvidence } from "../../types/rnc8d";

export type EvidencePreviewMode = "image" | "pdf" | "text" | "none";

function fileName(evidence: PlanEvidence): string {
  return (evidence.file_name ?? "").toLowerCase();
}

function mime(evidence: PlanEvidence): string {
  return (evidence.mime_type ?? "").toLowerCase();
}

export function isImageEvidence(evidence: PlanEvidence): boolean {
  return evidence.type === "image" || mime(evidence).startsWith("image/");
}

export function isPdfEvidence(evidence: PlanEvidence): boolean {
  return evidence.type === "pdf" || mime(evidence) === "application/pdf";
}

export function isTextEvidence(evidence: PlanEvidence): boolean {
  const name = fileName(evidence);
  const type = mime(evidence);
  return (
    evidence.type === "manual_text"
    || evidence.type === "spreadsheet"
    || type.startsWith("text/")
    || name.endsWith(".txt")
    || name.endsWith(".csv")
  );
}

export function isSpreadsheetEvidence(evidence: PlanEvidence): boolean {
  const name = fileName(evidence);
  const type = mime(evidence);
  return (
    evidence.type === "spreadsheet"
    || type.includes("spreadsheet")
    || type.includes("excel")
    || name.endsWith(".xlsx")
    || name.endsWith(".xls")
  );
}

export function isDocumentEvidence(evidence: PlanEvidence): boolean {
  const name = fileName(evidence);
  const type = mime(evidence);
  return (
    type.includes("wordprocessingml")
    || type === "application/msword"
    || name.endsWith(".docx")
    || name.endsWith(".doc")
  );
}

export function resolveEvidencePreviewMode(evidence: PlanEvidence): EvidencePreviewMode {
  if (isImageEvidence(evidence)) return "image";
  if (isPdfEvidence(evidence)) return "pdf";
  if (
    isTextEvidence(evidence)
    || isSpreadsheetEvidence(evidence)
    || isDocumentEvidence(evidence)
  ) {
    return "text";
  }
  return "none";
}

export function canPreviewEvidence(evidence: PlanEvidence): boolean {
  return resolveEvidencePreviewMode(evidence) !== "none";
}

export function evidencePreviewTitle(evidence: PlanEvidence): string {
  return evidence.file_name ?? evidence.description ?? evidence.id;
}

export function resolveLocalFilePreviewMode(file: File): EvidencePreviewMode {
  const mime = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  if (mime.startsWith("image/")) return "image";
  if (mime === "application/pdf") return "pdf";
  if (mime.startsWith("text/") || name.endsWith(".txt") || name.endsWith(".csv")) {
    return "text";
  }
  return "none";
}

export function canPreviewLocalFile(file: File): boolean {
  return resolveLocalFilePreviewMode(file) !== "none";
}
