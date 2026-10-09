import type {
  BpmnDocumentHost,
  DocumentMeta,
  RevisionMeta,
  RevisionSummary,
  ValidationReport,
  WriteOutcome,
} from "@delpi/bpmn-editor";

import {
  createProcessBpmnDocument,
  createProcessBpmnRevision,
  exportProcessBpmnWorkingCopy,
  fetchProcessBpmnDocument,
  fetchProcessBpmnRevision,
  fetchProcessBpmnRevisionXml,
  fetchProcessBpmnRevisions,
  fetchProcessBpmnWorkingCopy,
  restoreProcessBpmnRevision,
  saveProcessBpmnWorkingCopy,
  validateProcessBpmnWorkingCopy,
  type ProcessBpmnRevision,
} from "./api/bpmnDocumentApi";

type GetToken = (() => string | undefined) | undefined;

/**
 * TmProcessDocumentHost (G7 / ADR-006) — implementa o port `BpmnDocumentHost`
 * sobre o storage do Transformômetro (`transformometro.processo_bpmn_*` via
 * transformometro-api). O editor compartilhado nunca conhece este endpoint;
 * `EDITOR É COMPARTILHADO. ARTEFATO NÃO.`
 */
export class TmProcessDocumentHost implements BpmnDocumentHost {
  private readonly processoId: string;
  private readonly title: string;
  private readonly getAccessToken: GetToken;

  constructor(processoId: string, title: string, getAccessToken?: GetToken) {
    this.processoId = processoId;
    this.title = title;
    this.getAccessToken = getAccessToken;
  }

  async loadDocument(): Promise<DocumentMeta> {
    const payload = await fetchProcessBpmnDocument(
      this.processoId,
      this.getAccessToken,
    );
    if (!payload) {
      throw new Error("O processo não possui documento BPMN nativo.");
    }
    const revisions = await fetchProcessBpmnRevisions(
      this.processoId,
      this.getAccessToken,
    );
    return {
      id: payload.document.document_id,
      title: this.title,
      version: payload.version,
      archived_at: null,
      latest_revision_number:
        revisions.items.length > 0
          ? Math.max(...revisions.items.map((r) => r.revision_number))
          : null,
    };
  }

  loadWorkingCopy(): Promise<{ xml: string; version: number }> {
    return fetchProcessBpmnWorkingCopy(this.processoId, this.getAccessToken);
  }

  async saveWorkingCopy(
    xml: string,
    expectedVersion: number,
  ): Promise<WriteOutcome> {
    const doc = await saveProcessBpmnWorkingCopy(
      this.processoId,
      xml,
      expectedVersion,
      this.getAccessToken,
    );
    return {
      document_id: doc.document_id,
      version: doc.version,
      changed: true,
      artifact_sha256: doc.working_copy_sha256,
    };
  }

  async validate(xml: string): Promise<ValidationReport> {
    const result = await validateProcessBpmnWorkingCopy(
      this.processoId,
      xml,
      this.getAccessToken,
    );
    const report = result.report;
    return {
      evaluated_stages: report.evaluated_stages ?? [],
      not_evaluated_stages: report.not_evaluated_stages ?? [],
      issues: (report.issues ?? []) as ValidationReport["issues"],
    };
  }

  async listRevisions(): Promise<RevisionSummary[]> {
    const payload = await fetchProcessBpmnRevisions(
      this.processoId,
      this.getAccessToken,
    );
    return payload.items.map((rev) => this.toSummary(rev));
  }

  async createRevision(
    expectedVersion: number,
    meta?: RevisionMeta,
  ): Promise<{ revision_number: number; version: number }> {
    const rev = await createProcessBpmnRevision(
      this.processoId,
      expectedVersion,
      { name: meta?.name, description: meta?.description },
      this.getAccessToken,
    );
    // criar revisão não incrementa version do working copy (snapshot apenas);
    // a página recarrega loadDocument() para a versão autoritativa.
    return { revision_number: rev.revision_number, version: expectedVersion };
  }

  async loadRevision(revisionNumber: number): Promise<RevisionSummary> {
    const payload = await fetchProcessBpmnRevision(
      this.processoId,
      revisionNumber,
      this.getAccessToken,
    );
    return this.toSummary(payload.revision);
  }

  loadRevisionXml(revisionNumber: number): Promise<string> {
    return fetchProcessBpmnRevisionXml(
      this.processoId,
      revisionNumber,
      this.getAccessToken,
    );
  }

  exportWorkingCopy(): Promise<string> {
    return exportProcessBpmnWorkingCopy(this.processoId, this.getAccessToken);
  }

  async restoreRevision(
    revisionNumber: number,
    expectedVersion: number,
  ): Promise<WriteOutcome> {
    const doc = await restoreProcessBpmnRevision(
      this.processoId,
      revisionNumber,
      expectedVersion,
      this.getAccessToken,
    );
    return {
      document_id: doc.document_id,
      version: doc.version,
      changed: true,
      artifact_sha256: doc.working_copy_sha256,
    };
  }

  /** Criação do documento nativo (blank ou import) — chamada pelo card da
   *  página do processo, fora da superfície do editor. */
  async createDocument(xml: string | null) {
    return createProcessBpmnDocument(this.processoId, xml, this.getAccessToken);
  }

  private toSummary(rev: ProcessBpmnRevision): RevisionSummary {
    return {
      revision_number: rev.revision_number,
      artifact_sha256: rev.artifact_sha256,
      origin: rev.origin === "restore" ? "restore" : "explicit",
      source_revision_number: rev.source_revision_number ?? null,
      created_at: rev.created_at ?? "",
      created_by: rev.created_by ?? "",
      created_by_name: rev.created_by_name ?? null,
      name: rev.name ?? null,
      description: rev.description ?? null,
    };
  }
}
