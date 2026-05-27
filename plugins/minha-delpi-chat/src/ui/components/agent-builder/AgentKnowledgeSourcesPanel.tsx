import { FileText, Plus, Trash2, Upload } from "lucide-react";
import { useCallback, useMemo, useRef, useState, type ReactNode } from "react";

import type { ChatWorkspaceSource } from "../../../data/api/chatTypes";
import { getSourceContentHash, sha256HexFromFile } from "../../../utils/fileContentHash";

import "./AgentKnowledgeSourcesPanel.css";

type AgentKnowledgeSourcesPanelProps = {
  sources: ChatWorkspaceSource[];
  isUploading?: boolean;
  notice?: string | null;
  onUploadFiles: (files: File[]) => Promise<void>;
  onRemoveSource: (sourceId: string) => Promise<void>;
  onLocalDuplicatesSkipped?: (count: number) => void;
  noteSlot?: ReactNode;
};

function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes || bytes <= 0) {
    return "";
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getSourceLabel(source: ChatWorkspaceSource): string {
  return source.original_filename || source.title || "Arquivo";
}

function getSourceSize(source: ChatWorkspaceSource): string {
  const bytes = source.metadata?.sizeBytes;

  return formatFileSize(typeof bytes === "number" ? bytes : null);
}

export function AgentKnowledgeSourcesPanel({
  sources,
  isUploading = false,
  notice,
  onUploadFiles,
  onRemoveSource,
  onLocalDuplicatesSkipped,
  noteSlot,
}: AgentKnowledgeSourcesPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [pendingHashes, setPendingHashes] = useState<Set<string>>(new Set());

  const knownHashes = useMemo(() => {
    const hashes = new Set<string>();

    for (const source of sources) {
      const hash = getSourceContentHash(source.metadata);

      if (hash) {
        hashes.add(hash);
      }
    }

    return hashes;
  }, [sources]);

  const processFiles = useCallback(
    async (fileList: FileList | File[]) => {
      const files = Array.from(fileList).filter((file) => file.size > 0);

      if (files.length === 0) {
        return;
      }

      const accepted: File[] = [];
      const localHashes = new Set(knownHashes);

      for (const file of files) {
        const hash = await sha256HexFromFile(file);

        if (localHashes.has(hash) || pendingHashes.has(hash)) {
          continue;
        }

        localHashes.add(hash);
        accepted.push(file);
      }

      if (accepted.length === 0) {
        if (files.length > 0) {
          onLocalDuplicatesSkipped?.(files.length);
        }

        return;
      }

      const uploadHashes = await Promise.all(accepted.map((file) => sha256HexFromFile(file)));

      setPendingHashes((current) => {
        const next = new Set(current);
        uploadHashes.forEach((hash) => next.add(hash));
        return next;
      });

      try {
        await onUploadFiles(accepted);
      } finally {
        setPendingHashes((current) => {
          const next = new Set(current);
          uploadHashes.forEach((hash) => next.delete(hash));
          return next;
        });
      }
    },
    [knownHashes, onLocalDuplicatesSkipped, onUploadFiles, pendingHashes],
  );

  function handleDragOver(event: React.DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragActive(true);
  }

  function handleDragLeave(event: React.DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragActive(false);
  }

  function handleDrop(event: React.DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragActive(false);

    if (isUploading) {
      return;
    }

    void processFiles(event.dataTransfer.files);
  }

  return (
    <div className="mdc-agent-knowledge">
      <div
        className={[
          "mdc-agent-knowledge__dropzone",
          isDragActive ? "mdc-agent-knowledge__dropzone--active" : "",
          isUploading ? "mdc-agent-knowledge__dropzone--busy" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        onDragEnter={handleDragOver}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (!isUploading) {
            inputRef.current?.click();
          }
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Adicionar arquivos de conhecimento"
      >
        <span className="mdc-agent-knowledge__dropzone-icon">
          <Upload size={20} aria-hidden="true" />
        </span>
        <div className="mdc-agent-knowledge__dropzone-copy">
          <strong>Arraste arquivos aqui</strong>
          <span>ou clique para selecionar · PDF, TXT, MD e outros formatos suportados</span>
        </div>
        <span className="mdc-chat-ws-outline-btn mdc-agent-knowledge__dropzone-action">
          <Plus size={16} aria-hidden="true" />
          <span>Adicionar</span>
        </span>
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          disabled={isUploading}
          onChange={(event) => {
            if (event.target.files?.length) {
              void processFiles(event.target.files);
            }

            event.target.value = "";
          }}
        />
      </div>

      {notice ? <p className="mdc-agent-knowledge__notice">{notice}</p> : null}

      {isUploading ? (
        <p className="mdc-agent-knowledge__status">Enviando arquivos...</p>
      ) : null}

      {sources.length > 0 ? (
        <ul className="mdc-agent-knowledge__cards" aria-label="Arquivos do agente">
          {sources.map((source) => {
            const hash = getSourceContentHash(source.metadata);
            const isDuplicateMarked = source.duplicate === true;

            return (
              <li key={source.id}>
                <article
                  className={[
                    "mdc-agent-knowledge__card",
                    isDuplicateMarked ? "mdc-agent-knowledge__card--duplicate" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  title={getSourceLabel(source)}
                >
                  <span className="mdc-agent-knowledge__card-icon">
                    <FileText size={18} aria-hidden="true" />
                  </span>
                  <div className="mdc-agent-knowledge__card-copy">
                    <strong>{getSourceLabel(source)}</strong>
                    {getSourceSize(source) ? <small>{getSourceSize(source)}</small> : null}
                    {isDuplicateMarked ? (
                      <em>Já indexado — conteúdo igual</em>
                    ) : hash && knownHashes.has(hash) ? null : null}
                  </div>
                  <button
                    type="button"
                    className="mdc-agent-knowledge__card-remove"
                    onClick={(event) => {
                      event.stopPropagation();
                      void onRemoveSource(source.id);
                    }}
                    aria-label={`Remover ${getSourceLabel(source)}`}
                  >
                    <Trash2 size={14} aria-hidden="true" />
                  </button>
                </article>
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="mdc-chat-ws-empty">Nenhum arquivo ainda. Arraste documentos para começar.</p>
      )}

      {noteSlot ? <div className="mdc-agent-knowledge__note">{noteSlot}</div> : null}
    </div>
  );
}
