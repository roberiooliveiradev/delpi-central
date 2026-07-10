import type { PlanEvidence } from "../../types/rnc8d";
import {
  canPreviewFile as canPreviewFileBase,
  resolveFilePreviewKind,
  type FilePreviewKind,
} from "@delpi/plugin-ui/index";

export type EvidencePreviewMode = FilePreviewKind;

function evidenceInput(evidence: PlanEvidence) {
  return {
    mimeType: evidence.mime_type,
    fileName: evidence.file_name,
    declaredType: evidence.type,
  };
}

export function resolveEvidencePreviewMode(evidence: PlanEvidence): EvidencePreviewMode {
  return resolveFilePreviewKind(evidenceInput(evidence));
}

export function canPreviewEvidence(evidence: PlanEvidence): boolean {
  return canPreviewFileBase(evidenceInput(evidence));
}

export function evidencePreviewTitle(evidence: PlanEvidence): string {
  return evidence.file_name ?? evidence.description ?? evidence.id;
}

export function resolveLocalFilePreviewMode(file: File): EvidencePreviewMode {
  return resolveFilePreviewKind({
    mimeType: file.type,
    fileName: file.name,
  });
}

export function canPreviewLocalFile(file: File): boolean {
  return canPreviewFileBase({
    mimeType: file.type,
    fileName: file.name,
  });
}

export function isImageEvidence(evidence: PlanEvidence): boolean {
  return resolveEvidencePreviewMode(evidence) === "image";
}

export function isPdfEvidence(evidence: PlanEvidence): boolean {
  return resolveEvidencePreviewMode(evidence) === "pdf";
}
