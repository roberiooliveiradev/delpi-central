import { useState } from "react";

import type { AdminKnowledgeDocument } from "../../../../data/api/adminTypes";
import { KnowledgeCuratorialFields } from "./KnowledgeCuratorialFields";
import type {
  KnowledgeBackendPlaceholders,
  KnowledgeDocumentActions,
} from "./knowledgeTypes";
import {
  formatSourceTypeLabel,
  sourceTypeBadgeClass,
} from "./knowledgeCuratorialUtils";
import { useConfirmDialog } from "../../useConfirmDialog";

import "./KnowledgeDocumentCard.css";

type KnowledgeDocumentCardProps = KnowledgeDocumentActions &
  KnowledgeBackendPlaceholders & {
    document: AdminKnowledgeDocument;
    isMutating: boolean;
    canManageMetadata: boolean;
    canDeleteKnowledgeDocuments: boolean;
    canReindexKnowledgeDocuments: boolean;
  };

function tagsToInput(tags?: string[]): string {
  return (tags ?? []).join(", ");
}

export function KnowledgeDocumentCard({
  document,
  isMutating,
  deleteDocument,
  deactivateDocument,
  reactivateDocument,
  reindexDocument,
  updateDocumentMetadata,
  testDocument,
  canManageMetadata,
  canDeleteKnowledgeDocuments,
  canReindexKnowledgeDocuments,
}: KnowledgeDocumentCardProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const [isEditingMetadata, setIsEditingMetadata] = useState(false);
  const [category, setCategory] = useState(document.category ?? "");
  const [tags, setTags] = useState(tagsToInput(document.tags));
  const [namespace, setNamespace] = useState(document.namespace ?? "");
  const [domain, setDomain] = useState(document.domain ?? "");
  const [priority, setPriority] = useState(
    document.priority ? String(document.priority) : "",
  );
  const [qualityScore, setQualityScore] = useState(
    document.qualityScore !== undefined && document.qualityScore !== null
      ? String(document.qualityScore)
      : "",
  );

  const sourceBadgeClass = sourceTypeBadgeClass(document.sourceType);

  async function handleSaveMetadata() {
    await updateDocumentMetadata(document.id, {
      category: category.trim() || undefined,
      tags: tags.trim() || undefined,
      namespace: namespace.trim() || undefined,
      domain: domain.trim() || undefined,
      priority: priority ? Number(priority) : undefined,
      qualityScore: qualityScore ? Number(qualityScore) : undefined,
    });
    setIsEditingMetadata(false);
  }

  return (
    <article className="mdc-admin-entity-row mdc-knowledge-document-card">
      {confirmDialog}

      <div className="mdc-admin-entity-row__body">
        <div className="mdc-admin-entity-row__title-line">
          <strong>{document.title}</strong>
          <span
            className={`mdc-admin-badge ${
              document.active ? "mdc-admin-badge--success" : "mdc-admin-badge--danger"
            }`}
          >
            {document.active ? "Ativo" : "Inativo"}
          </span>
          <span className={`mdc-knowledge-badge ${sourceBadgeClass}`}>
            {formatSourceTypeLabel(document.sourceType)}
          </span>
        </div>

        <div className="mdc-admin-entity-row__meta mdc-knowledge-document-card__meta">
          {document.category ? (
            <span className="mdc-knowledge-badge mdc-knowledge-badge--category">
              {document.category}
            </span>
          ) : null}
          {document.namespace ? (
            <span className="mdc-knowledge-badge mdc-knowledge-badge--namespace">
              {document.namespace}
            </span>
          ) : null}
          {document.domain ? (
            <span className="mdc-knowledge-badge mdc-knowledge-badge--domain">
              {document.domain}
            </span>
          ) : null}
          {document.priority ? (
            <span className="mdc-knowledge-badge mdc-knowledge-badge--priority">
              P{document.priority}
            </span>
          ) : null}
          {document.qualityScore !== undefined && document.qualityScore !== null ? (
            <span className="mdc-knowledge-badge mdc-knowledge-badge--quality">
              Q{document.qualityScore}
            </span>
          ) : null}
          {(document.tags ?? []).map((tag) => (
            <span key={tag} className="mdc-knowledge-badge mdc-knowledge-badge--tag">
              #{tag}
            </span>
          ))}
        </div>

        <p className="mdc-admin-entity-row__detail">
          {document.sourceRef || "sem referência"} · {document.chunkCount} chunk(s)
        </p>

        <small className="mdc-admin-entity-row__detail">
          Atualizado em {new Date(document.updatedAt).toLocaleString()}
        </small>

        {isEditingMetadata ? (
          <div className="mdc-knowledge-document-card__editor">
            <KnowledgeCuratorialFields
              category={category}
              tags={tags}
              namespace={namespace}
              domain={domain}
              priority={priority}
              qualityScore={qualityScore}
              disabled={isMutating || !canManageMetadata}
              onCategoryChange={setCategory}
              onTagsChange={setTags}
              onNamespaceChange={setNamespace}
              onDomainChange={setDomain}
              onPriorityChange={setPriority}
              onQualityScoreChange={setQualityScore}
            />
            <div className="mdc-admin-entity-row__actions mdc-knowledge-document-card__editor-actions">
              <button
                type="button"
                className="mdc-admin-btn mdc-admin-btn--primary"
                disabled={isMutating || !canManageMetadata}
                onClick={() => {
                  void handleSaveMetadata();
                }}
              >
                Salvar metadados
              </button>
              <button
                type="button"
                className="mdc-admin-btn"
                disabled={isMutating}
                onClick={() => setIsEditingMetadata(false)}
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : null}
      </div>

      <div className="mdc-admin-entity-row__actions">
        {canManageMetadata ? (
          <button
            type="button"
            className="mdc-admin-btn"
            disabled={isMutating}
            onClick={() => setIsEditingMetadata((current) => !current)}
          >
            {isEditingMetadata ? "Fechar" : "Metadados"}
          </button>
        ) : null}

        <button
          type="button"
          className="mdc-admin-btn"
          disabled={isMutating || !testDocument}
          title={testDocument ? "Testar documento" : "Aguardando endpoint de teste RAG"}
          onClick={() => {
            void testDocument?.(document.id);
          }}
        >
          Testar
        </button>

        {document.active ? (
          <button
            type="button"
            className="mdc-admin-btn"
            disabled={isMutating || !canDeleteKnowledgeDocuments}
            title={
              canDeleteKnowledgeDocuments
                ? "Desativar documento"
                : "Você não tem permissão para alterar documentos."
            }
            onClick={() => deactivateDocument(document.id)}
          >
            Desativar
          </button>
        ) : (
          <button
            type="button"
            className="mdc-admin-btn"
            disabled={isMutating || !canDeleteKnowledgeDocuments}
            title={
              canDeleteKnowledgeDocuments
                ? "Reativar documento"
                : "Você não tem permissão para alterar documentos."
            }
            onClick={() => reactivateDocument(document.id)}
          >
            Reativar
          </button>
        )}

        <button
          type="button"
          className="mdc-admin-btn"
          disabled={isMutating || !canReindexKnowledgeDocuments}
          title={
            canReindexKnowledgeDocuments
              ? "Reindexar documento"
              : "Você não tem permissão para reindexar documentos."
          }
          onClick={() => reindexDocument(document.id)}
        >
          Reindexar
        </button>

        <button
          type="button"
          className="mdc-admin-btn mdc-admin-btn--danger mdc-admin-entity-row__danger"
          disabled={isMutating || !canDeleteKnowledgeDocuments}
          title={
            canDeleteKnowledgeDocuments
              ? "Excluir documento"
              : "Você não tem permissão para excluir documentos."
          }
          onClick={() => {
            void confirm({
              title: "Excluir documento",
              description: `Excluir definitivamente "${document.title}" da base de conhecimento?`,
              confirmLabel: "Excluir",
              cancelLabel: "Cancelar",
              danger: true,
            }).then((confirmed) => {
              if (confirmed) {
                void deleteDocument(document.id);
              }
            });
          }}
        >
          Excluir
        </button>
      </div>
    </article>
  );
}
