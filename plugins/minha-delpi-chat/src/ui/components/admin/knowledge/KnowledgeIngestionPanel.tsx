import { useState } from "react";

import { workspaceFileProjectIngestLabels } from "../../../../content/workspaceFileIngestContent";
import { AdminFileDropzone } from "../shared/AdminFileDropzone";
import { IngestProgressIndicator } from "../../shared/IngestProgressIndicator";
import { KnowledgeCuratorialFields } from "./KnowledgeCuratorialFields";
import type {
  KnowledgeIngestionActions,
  KnowledgeIngestionMode,
} from "./knowledgeTypes";

import "./KnowledgeIngestionPanel.css";

type KnowledgeIngestionPanelProps = KnowledgeIngestionActions & {
  isMutating: boolean;
  canManageKnowledge: boolean;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size} bytes`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function KnowledgeIngestionPanel({
  isMutating,
  canManageKnowledge,
  createDocument,
  uploadDocumentFile,
  previewIngestion,
  ingestionPreview,
  getAccessToken,
}: KnowledgeIngestionPanelProps) {
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("diretriz");
  const [sourceRef, setSourceRef] = useState("");
  const [content, setContent] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ingestMode, setIngestMode] = useState<KnowledgeIngestionMode>("file");
  const [category, setCategory] = useState("");
  const [tags, setTags] = useState("");
  const [namespace, setNamespace] = useState("");
  const [domain, setDomain] = useState("");
  const [priority, setPriority] = useState("");
  const [qualityScore, setQualityScore] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadPercent, setUploadPercent] = useState<number | null>(null);
  const [previewPercent, setPreviewPercent] = useState<number | null>(null);

  const canSubmitDocument =
    title.trim().length > 0 &&
    sourceType.trim().length > 0 &&
    (ingestMode === "text" ? content.trim().length > 0 : Boolean(selectedFile));

  const canPreviewPipeline =
    (ingestMode === "text" && content.trim().length > 0) ||
    (ingestMode === "file" && Boolean(selectedFile));

  async function handlePreviewPipeline() {
    if (!canPreviewPipeline || isMutating) {
      return;
    }

    if (ingestMode === "file" && selectedFile) {
      setPreviewPercent(0);

      try {
        await previewIngestion({
          file: selectedFile,
          title: title.trim() || selectedFile.name,
          sourceType: sourceType.trim() || "admin_preview_upload",
          sourceRef: sourceRef.trim() || undefined,
          onUploadProgress: setPreviewPercent,
        });
      } finally {
        setPreviewPercent(null);
      }

      return;
    }

    await previewIngestion({
      content: content.trim(),
      title: title.trim() || "Pré-visualização",
      sourceType: sourceType.trim(),
      sourceRef: sourceRef.trim() || undefined,
      metadata: {
        scope: "global",
        category: category.trim() || undefined,
        tags: tags.trim() || undefined,
        namespace: namespace.trim() || undefined,
        domain: domain.trim() || undefined,
      },
    });
  }

  function resetForm() {
    setTitle("");
    setSourceRef("");
    setContent("");
    setCategory("");
    setTags("");
    setNamespace("");
    setDomain("");
    setPriority("");
    setQualityScore("");
    setSelectedFile(null);
    setIsDragging(false);
  }

  function selectFile(file: File | null) {
    setSelectedFile(file);

    if (file && !title.trim()) {
      setTitle(file.name);
    }
  }

  async function handleSubmit() {
    if (!canManageKnowledge || !canSubmitDocument || isMutating) {
      return;
    }

    if (ingestMode === "file") {
      if (!selectedFile) {
        return;
      }

      setUploadPercent(0);

      try {
        await uploadDocumentFile({
          file: selectedFile,
          title: title.trim() || selectedFile.name,
          sourceType: sourceType.trim() || "admin_upload",
          sourceRef: sourceRef.trim() || undefined,
          category: category.trim() || undefined,
          tags: tags.trim() || undefined,
          namespace: namespace.trim() || undefined,
          domain: domain.trim() || undefined,
          priority: priority ? Number(priority) : undefined,
          qualityScore: qualityScore ? Number(qualityScore) : undefined,
          metadata: {
            origin: "admin_upload",
            adminContext: "knowledge_base",
          },
          onUploadProgress: setUploadPercent,
        });
      } finally {
        setUploadPercent(null);
      }
    } else {
      await createDocument({
        title: title.trim(),
        sourceType: sourceType.trim(),
        sourceRef: sourceRef.trim() || undefined,
        content: content.trim(),
        category: category.trim() || undefined,
        tags: tags.trim() || undefined,
        namespace: namespace.trim() || undefined,
        domain: domain.trim() || undefined,
        priority: priority ? Number(priority) : undefined,
        qualityScore: qualityScore ? Number(qualityScore) : undefined,
        metadata: {
          origin: "admin_manual",
          adminContext: "knowledge_base",
        },
      });
    }

    resetForm();
  }

  return (
    <article className="mdc-admin-panel mdc-knowledge-ingestion">
      <div className="mdc-knowledge-ingestion__header">
        <div>
          <p className="mdc-chat-eyebrow">Base global</p>
          <h2>Adicionar conhecimento</h2>
        </div>

        <span>{canManageKnowledge ? "Global" : "Somente leitura"}</span>
      </div>

      <p className="mdc-knowledge-ingestion__description">
        Use esta área somente para documentos que orientam todo o Minha DELPI Chat.
        Anexos de conversas, agentes e projetos não entram aqui.
      </p>

      <form
        className="mdc-knowledge-ingestion__form"
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit();
        }}
      >
        <div className="mdc-knowledge-ingestion__mode" role="tablist" aria-label="Modo de ingestão">
          <button
            type="button"
            className={ingestMode === "file" ? "is-active" : undefined}
            onClick={() => setIngestMode("file")}
          >
            Arquivo
          </button>
          <button
            type="button"
            className={ingestMode === "text" ? "is-active" : undefined}
            onClick={() => setIngestMode("text")}
          >
            Texto
          </button>
        </div>

        {ingestMode === "file" ? (
          <AdminFileDropzone
            label="Arquivo de conhecimento"
            ingestFamily="global_knowledge"
            getAccessToken={getAccessToken}
            disabled={isMutating || !canManageKnowledge}
            isBusy={isMutating}
            isDragActive={isDragging}
            title={selectedFile ? selectedFile.name : "Arraste arquivos aqui"}
            hint={
              selectedFile
                ? formatFileSize(selectedFile.size)
                : "ou clique para selecionar · txt, md, csv, json, docx, xlsx e pdf"
            }
            actionLabel={selectedFile ? "Trocar" : "Selecionar"}
            onDragActiveChange={setIsDragging}
            onFilesSelected={(files) => {
              selectFile(files[0] ?? null);
            }}
            footerSlot={
              selectedFile ? (
                <p className="mdc-admin-file-dropzone-field__meta">
                  Arquivo pronto para ingestão na base global.
                </p>
              ) : null
            }
          />
        ) : (
          <label className="mdc-admin-field">
            <span>Conteúdo</span>
            <textarea
              value={content}
              disabled={isMutating || !canManageKnowledge}
              rows={8}
              placeholder="Cole aqui diretrizes, glossários ou instruções globais."
              onChange={(event) => setContent(event.target.value)}
            />
          </label>
        )}

        {uploadPercent != null || previewPercent != null ? (
          <IngestProgressIndicator
            className="mdc-knowledge-ingestion__progress"
            label={workspaceFileProjectIngestLabels().uploadingStatus}
            percent={uploadPercent ?? previewPercent ?? undefined}
          />
        ) : null}

        <label className="mdc-admin-field">
          <span>Título</span>
          <input
            value={title}
            disabled={isMutating || !canManageKnowledge}
            placeholder="Ex.: Diretrizes gerais do atendimento"
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>

        <label className="mdc-admin-field">
          <span>Tipo</span>
          <select
            value={sourceType}
            disabled={isMutating || !canManageKnowledge}
            onChange={(event) => setSourceType(event.target.value)}
          >
            <option value="diretriz">Diretriz</option>
            <option value="glossario">Glossário</option>
            <option value="manual">Manual</option>
            <option value="politica">Política</option>
            <option value="admin_upload">Upload admin</option>
          </select>
        </label>

        <label className="mdc-admin-field">
          <span>Referência</span>
          <input
            value={sourceRef}
            disabled={isMutating}
            placeholder="Ex.: global:diretrizes-atendimento"
            onChange={(event) => setSourceRef(event.target.value)}
          />
        </label>

        <KnowledgeCuratorialFields
          category={category}
          tags={tags}
          namespace={namespace}
          domain={domain}
          priority={priority}
          qualityScore={qualityScore}
          disabled={isMutating || !canManageKnowledge}
          onCategoryChange={setCategory}
          onTagsChange={setTags}
          onNamespaceChange={setNamespace}
          onDomainChange={setDomain}
          onPriorityChange={setPriority}
          onQualityScoreChange={setQualityScore}
        />

        <div className="mdc-knowledge-ingestion__actions">
          <button
            type="button"
            className="mdc-admin-btn"
            disabled={!canManageKnowledge || !canPreviewPipeline || isMutating}
            onClick={() => {
              void handlePreviewPipeline();
            }}
          >
            Pré-visualizar pipeline
          </button>

          <button
            type="submit"
            className="mdc-admin-btn mdc-admin-btn--primary"
            disabled={!canManageKnowledge || !canSubmitDocument || isMutating}
            title={
              canManageKnowledge
                ? undefined
                : "Você não tem permissão para adicionar conhecimento global."
            }
          >
            {isMutating ? "Processando..." : "Ingerir na base global"}
          </button>
        </div>

        {ingestionPreview ? (
          <div className="mdc-knowledge-ingestion__preview">
            <strong>Prévia do pipeline</strong>
            <p className="mdc-chat-muted">
              {ingestionPreview.pipeline.chunksAfterDedup} chunk(s) · estratégia{" "}
              {ingestionPreview.pipeline.chunkStrategy} ·{" "}
              {ingestionPreview.pipeline.duplicatesRemoved} duplicata(s) removida(s) ·{" "}
              {ingestionPreview.pipeline.charsRemoved} caractere(s) limpos
            </p>
            <ul>
              {ingestionPreview.chunks.map((chunk) => (
                <li key={chunk.index}>
                  <span>
                    Chunk {chunk.index + 1} · {chunk.wordCount} palavra(s) · {chunk.charCount}{" "}
                    caractere(s)
                  </span>
                  <p>{chunk.preview}</p>
                </li>
              ))}
            </ul>

            {ingestionPreview.semanticDuplicates &&
            ingestionPreview.semanticDuplicates.length > 0 ? (
              <div className="mdc-knowledge-ingestion__semantic">
                <strong>Possíveis duplicatas semânticas</strong>
                <ul>
                  {ingestionPreview.semanticDuplicates.map((duplicate) => (
                    <li key={`${duplicate.chunkId}-${duplicate.similarity}`}>
                      <span>
                        {duplicate.title || duplicate.documentId} · similaridade{" "}
                        {Math.round(duplicate.similarity * 100)}%
                      </span>
                      <p>{duplicate.preview}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}
      </form>
    </article>
  );
}
