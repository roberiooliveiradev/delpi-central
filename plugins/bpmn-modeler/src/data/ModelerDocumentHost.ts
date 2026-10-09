import type {
  BpmnDocumentHost,
  DocumentMeta,
  RevisionMeta,
  RevisionSummary,
  ValidationReport,
  WriteOutcome,
} from "@delpi/bpmn-editor";
import {
  archiveModel,
  createRevision,
  exportWorkingCopy,
  getModel,
  getRevision,
  getRevisionXml,
  getWorkingCopy,
  listRevisions,
  restoreRevision,
  saveWorkingCopy,
  unarchiveModel,
  validateWorkingCopy,
} from "./api/bpmnModelerApi";

/**
 * ModelerDocumentHost (G7 / ADR-006) — implementa o port `BpmnDocumentHost`
 * sobre o próprio storage do BPMN Modeler (`bpmn_modeler.*` via
 * `bpmn-modeler-api`). O editor compartilhado nunca conhece este endpoint.
 */
export class ModelerDocumentHost implements BpmnDocumentHost {
  private readonly modelId: string;
  private readonly getAccessToken?: () => string | undefined;

  constructor(modelId: string, getAccessToken?: () => string | undefined) {
    this.modelId = modelId;
    this.getAccessToken = getAccessToken;
  }

  async loadDocument(): Promise<DocumentMeta> {
    const { model, version } = await getModel(this.modelId, {
      getAccessToken: this.getAccessToken,
    });
    return {
      id: model.id,
      title: model.display_name,
      version,
      archived_at: model.archived_at,
      latest_revision_number: model.latest_revision_number,
    };
  }

  loadWorkingCopy(): Promise<{ xml: string; version: number }> {
    return getWorkingCopy(this.modelId, { getAccessToken: this.getAccessToken });
  }

  async saveWorkingCopy(xml: string, expectedVersion: number): Promise<WriteOutcome> {
    const out = await saveWorkingCopy(this.modelId, xml, expectedVersion, {
      getAccessToken: this.getAccessToken,
    });
    return { ...out, document_id: out.model_id };
  }

  validate(candidateXml: string): Promise<ValidationReport> {
    return validateWorkingCopy(this.modelId, candidateXml, {
      getAccessToken: this.getAccessToken,
    });
  }

  exportWorkingCopy(): Promise<string> {
    return exportWorkingCopy(this.modelId, {
      getAccessToken: this.getAccessToken,
    });
  }

  async listRevisions(): Promise<RevisionSummary[]> {
    const page = await listRevisions(this.modelId, {
      getAccessToken: this.getAccessToken,
    });
    return page.items;
  }

  createRevision(
    expectedVersion: number,
    meta?: RevisionMeta,
  ): Promise<{ revision_number: number; version: number }> {
    return createRevision(this.modelId, expectedVersion, {
      getAccessToken: this.getAccessToken,
      ...(meta ?? {}),
    });
  }

  loadRevision(revisionNumber: number): Promise<RevisionSummary> {
    return getRevision(this.modelId, revisionNumber, {
      getAccessToken: this.getAccessToken,
    });
  }

  loadRevisionXml(revisionNumber: number): Promise<string> {
    return getRevisionXml(this.modelId, revisionNumber, {
      getAccessToken: this.getAccessToken,
    });
  }

  async restoreRevision(
    revisionNumber: number,
    expectedVersion: number,
  ): Promise<WriteOutcome> {
    const out = await restoreRevision(this.modelId, revisionNumber, expectedVersion, {
      getAccessToken: this.getAccessToken,
    });
    return { ...out, document_id: out.model_id };
  }

  /** Lifecycle Modeler-only (não entra no port genérico). */
  async toggleArchive(archived: boolean, expectedVersion: number): Promise<void> {
    if (archived) {
      await unarchiveModel(this.modelId, expectedVersion, {
        getAccessToken: this.getAccessToken,
      });
    } else {
      await archiveModel(this.modelId, expectedVersion, {
        getAccessToken: this.getAccessToken,
      });
    }
  }
}
