import type { KaizenEvidence } from "../../types/kaizen";
import {
  canPreviewFile,
  resolveFilePreviewKind,
  type FilePreviewKind,
} from "@delpi/plugin-ui";

export type EvidencePreviewMode = FilePreviewKind;

export function resolveEvidencePreviewMode(evidence: KaizenEvidence): EvidencePreviewMode {
  return resolveFilePreviewKind({
    mimeType: evidence.mime_type,
    fileName: evidence.file_name,
    declaredType: evidence.type,
  });
}

export function resolveLocalFilePreviewMode(file: File): EvidencePreviewMode {
  return resolveFilePreviewKind({
    mimeType: file.type,
    fileName: file.name,
  });
}

export function canPreviewEvidence(evidence: KaizenEvidence): boolean {
  return canPreviewFile({
    mimeType: evidence.mime_type,
    fileName: evidence.file_name,
    declaredType: evidence.type,
  });
}

export function canPreviewLocalFile(file: File): boolean {
  return canPreviewFile({
    mimeType: file.type,
    fileName: file.name,
  });
}

export function evidencePreviewTitle(evidence: KaizenEvidence): string {
  return evidence.file_name ?? evidence.description ?? evidence.id;
}
