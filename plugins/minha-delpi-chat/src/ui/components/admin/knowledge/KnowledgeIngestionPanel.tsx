import { type DragEvent, useRef, useState } from "react";

import type {
  KnowledgeIngestionActions,
  KnowledgeIngestionMode,
} from "./knowledgeTypes";

import "./KnowledgeIngestionPanel.css";

type KnowledgeIngestionPanelProps = KnowledgeIngestionActions & {
  isMutating: boolean;
};

const ACCEPTED_KNOWLEDGE_EXTENSIONS = ".pdf,.txt,.md,.doc,.docx,.xls,.xlsx,.csv,.json";

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
  createDocument,
  uploadDocumentFile,
}: KnowledgeIngestionPanelProps) {
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("diretriz");
  const [sourceRef, setSourceRef] = useState("");
  const [content, setContent] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ingestMode, setIngestMode] = useState<KnowledgeIngestionMode>("file");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canSubmitDocument =
    title.trim().length > 0 &&
    sourceType.trim().length > 0 &&
    (ingestMode === "text" ? content.trim().length > 0 : Boolean(selectedFile));

  function resetForm() {
    setTitle("");
    setSourceRef("");
    setContent("");
    setSelectedFile(null);
    setIsDragging(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function selectFile(file: File | null) {
    setSelectedFile(file);

    if (file && !title.trim()) {
      setTitle(file.name);
    }
  }

  function hasDraggedFiles(event: DragEvent<HTMLElement>) {
    return Array.from(event.dataTransfer.types).includes("Files");
  }

  function handleDragOver(event: DragEvent<HTMLElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = "copy";
    setIsDragging(true);
  }

  function handleDragLeave(event: DragEvent<HTMLElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    const relatedTarget = event.relatedTarget;

    if (relatedTarget instanceof Node && event.currentTarget.contains(relatedTarget)) {
      return;
    }

    setIsDragging(false);
  }

  function handleDrop(event: DragEvent<HTMLElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);

    const file = Array.from(event.dataTransfer.files ?? [])[0] ?? null;

    if (file) {
      selectFile(file);
    }
  }

  async function handleSubmit() {
    if (!canSubmitDocument || isMutating) {
      return;
    }

    if (ingestMode === "file") {
      if (!selectedFile) {
        return;
      }

      await uploadDocumentFile({
        file: selectedFile,
        title: title.trim() || selectedFile.name,
        sourceType: sourceType.trim() || "admin_upload",
        sourceRef: sourceRef.trim() || undefined,
        metadata: {
          scope: "global",
          origin: "admin_upload",
          adminContext: "knowledge_base",
        },
      });
    } else {
      await createDocument({
        title: title.trim(),
        sourceType: sourceType.trim(),
        sourceRef: sourceRef.trim() || undefined,
        content: content.trim(),
        metadata: {
          scope: "global",
          origin: "admin_manual",
          adminContext: "knowledge_base",
        },
      });
    }

    resetForm();
  }

  return (
    <article className="mdc-knowledge-ingestion">
      <div className="mdc-knowledge-ingestion__header">
        <div>
          <p className="mdc-chat-eyebrow">Base global</p>
          <h2>Adicionar conhecimento</h2>
        </div>

        <span>Global</span>
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
          <label
            className={
              isDragging
                ? "mdc-knowledge-ingestion__dropzone is-dragging"
                : "mdc-knowledge-ingestion__dropzone"
            }
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <span>Arquivo de conhecimento</span>
            <input
              ref={fileInputRef}
              type="file"
              disabled={isMutating}
              accept={ACCEPTED_KNOWLEDGE_EXTENSIONS}
              onChange={(event) => {
                selectFile(event.target.files?.[0] ?? null);
              }}
            />

            <strong>
              {selectedFile ? selectedFile.name : "Selecionar ou arrastar arquivo"}
            </strong>

            <small>
              {selectedFile
                ? formatFileSize(selectedFile.size)
                : "Formatos: txt, md, csv, json, docx, xlsx e pdf."}
            </small>
          </label>
        ) : (
          <label>
            <span>Conteúdo</span>
            <textarea
              value={content}
              disabled={isMutating}
              rows={8}
              placeholder="Cole aqui diretrizes, glossários ou instruções globais."
              onChange={(event) => setContent(event.target.value)}
            />
          </label>
        )}

        <div className="mdc-knowledge-ingestion__grid">
          <label>
            <span>Título</span>
            <input
              value={title}
              disabled={isMutating}
              placeholder="Ex.: Diretrizes gerais do atendimento"
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>

          <label>
            <span>Tipo</span>
            <select
              value={sourceType}
              disabled={isMutating}
              onChange={(event) => setSourceType(event.target.value)}
            >
              <option value="diretriz">Diretriz</option>
              <option value="glossario">Glossário</option>
              <option value="manual">Manual</option>
              <option value="politica">Política</option>
              <option value="admin_upload">Upload admin</option>
            </select>
          </label>
        </div>

        <label>
          <span>Referência</span>
          <input
            value={sourceRef}
            disabled={isMutating}
            placeholder="Ex.: global:diretrizes-atendimento"
            onChange={(event) => setSourceRef(event.target.value)}
          />
        </label>

        <div className="mdc-knowledge-ingestion__future">
          <strong>Próximas integrações</strong>
          <small>
            Teste RAG, versionamento e publicação ficarão plugados neste painel sem alterar a estrutura da aba.
          </small>
        </div>

        <button type="submit" disabled={!canSubmitDocument || isMutating}>
          {isMutating ? "Processando..." : "Ingerir na base global"}
        </button>
      </form>
    </article>
  );
}
