import type { AdminKnowledgeDocument } from "../../../../data/api/adminTypes";
import type {
  KnowledgeBackendPlaceholders,
  KnowledgeDocumentActions,
} from "./knowledgeTypes";

import "./KnowledgeDocumentCard.css";

type KnowledgeDocumentCardProps = KnowledgeDocumentActions &
  KnowledgeBackendPlaceholders & {
    document: AdminKnowledgeDocument;
    isMutating: boolean;
    canDeleteKnowledgeDocuments: boolean;
    canReindexKnowledgeDocuments: boolean;
  };

export function KnowledgeDocumentCard({
  document,
  isMutating,
  deleteDocument,
  deactivateDocument,
  reactivateDocument,
  reindexDocument,
  testDocument,
  canDeleteKnowledgeDocuments,
  canReindexKnowledgeDocuments,
}: KnowledgeDocumentCardProps) {
  return (
    <article className="mdc-knowledge-document-card">
      <div>
        <div className="mdc-knowledge-document-card__title">
          <strong>{document.title}</strong>
          <span className={document.active ? "is-active" : "is-inactive"}>
            {document.active ? "Ativo" : "Inativo"}
          </span>
        </div>

        <p>
          {document.sourceType} · {document.sourceRef || "sem referência"} ·{" "}
          {document.chunkCount} chunk(s)
        </p>

        <small>
          Atualizado em {new Date(document.updatedAt).toLocaleString()}
        </small>
      </div>

      <div className="mdc-knowledge-document-card__actions">
        <button
          type="button"
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
          className="mdc-knowledge-document-card__danger"
          disabled={isMutating || !canDeleteKnowledgeDocuments}
          title={
            canDeleteKnowledgeDocuments
              ? "Excluir documento"
              : "Você não tem permissão para excluir documentos."
          }
          onClick={() => {
            if (
              window.confirm(
                `Excluir definitivamente "${document.title}" da base de conhecimento?`,
              )
            ) {
              void deleteDocument(document.id);
            }
          }}
        >
          Excluir
        </button>
      </div>
    </article>
  );
}
