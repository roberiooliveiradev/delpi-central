/**
 * BpmnDocumentHost — port de persistência do BPMN Editor compartilhado (G7).
 *
 * `EDITOR É COMPARTILHADO. ARTEFATO NÃO.` — a superfície nunca conhece
 * endpoint, app ou storage; todo I/O de documento passa por este port.
 * Cada bounded context provê a própria implementação:
 *
 *   ModelerDocumentHost          → bpmn-modeler API → bpmn_modeler.*
 *   TransformometroBpmnDocumentHost → transformometro API → transformometro.*
 *
 * Contrato de concorrência: `version` inteiro crescente; toda escrita leva
 * `expectedVersion` (o host serializa como `If-Match "v<n>"` quando o
 * backend usa ETag). Stale → `BpmnDocumentError` status 409.
 */
import type {
  DocumentMeta,
  RevisionSummary,
  ValidationReport,
  WriteOutcome,
} from "./types";

export type RevisionMeta = { name?: string; description?: string };

export interface BpmnDocumentHost {
  /** Metadados do documento (título, version, archived, latest revision). */
  loadDocument(): Promise<DocumentMeta>;

  /** Working copy canônico: XML + version corrente. */
  loadWorkingCopy(): Promise<{ xml: string; version: number }>;

  /** Escrita atômica com optimistic concurrency (fail no stale). */
  saveWorkingCopy(xml: string, expectedVersion: number): Promise<WriteOutcome>;

  /** Validação governada do artefato — não persiste. */
  validate(xml: string): Promise<ValidationReport>;

  /** Revisões explícitas, imutáveis, append-only. */
  listRevisions(): Promise<RevisionSummary[]>;

  /** Cria revisão explícita a partir do working copy corrente. */
  createRevision(
    expectedVersion: number,
    meta?: RevisionMeta,
  ): Promise<{ revision_number: number; version: number }>;

  /** Metadados de uma revisão (para a página histórica). */
  loadRevision(revisionNumber: number): Promise<RevisionSummary>;

  /** XML canônico de uma revisão histórica. */
  loadRevisionXml(revisionNumber: number): Promise<string>;

  /** Artefato canônico do working copy para export (.bpmn server-side). */
  exportWorkingCopy(): Promise<string>;

  /** Restaura revisão: working copy ← artefato histórico + nova revisão
   *  com proveniência. Ausente quando o host não suporta restore. */
  restoreRevision?(
    revisionNumber: number,
    expectedVersion: number,
  ): Promise<WriteOutcome>;
}
