import { useCallback, useEffect, useMemo, useState } from "react";
import {
  EmptyState,
  emptyStateCardBemClasses,
  FieldLabel,
  MessageBodyReadonly,
  NativeTextControl,
} from "@delpi/plugin-ui/index";

import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import {
  createProcessDocument,
  deleteProcessDocument,
  fetchProcessDocument,
  fetchProcessDocuments,
  updateProcessDocument,
} from "../../data/api/transformometroProcessDocumentApi";
import { useDirectoryUserLabels } from "../../hooks/useDirectoryUserLabels";
import type { ProcessDocument, ProcessDocumentSummary } from "../../types/processDocument";
import { formatDateTime } from "../../utils/format";
import {
  buildProcessDocumentHref,
  buildProcessoSectionHref,
  parseProcessDocumentIdFromHash,
} from "./processWorkspaceNav";

type Props = {
  processoId: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (href: string) => void;
};

type EditorMode = "view" | "create" | "edit";

const EMPTY = emptyStateCardBemClasses("ds");

export function ProcessDocumentationSection({
  processoId,
  getAccessToken,
  onNavigate,
}: Props) {
  const confirm = useConfirm();
  const [items, setItems] = useState<ProcessDocumentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ProcessDocument | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [mode, setMode] = useState<EditorMode>("view");
  const [draftTitle, setDraftTitle] = useState("");
  const [draftMarkdown, setDraftMarkdown] = useState("");
  const [previewTab, setPreviewTab] = useState<"edit" | "preview">("edit");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const authorIds = useMemo(() => {
    const ids = new Set<string>();
    for (const item of items) {
      if (item.created_by_user_id) ids.add(item.created_by_user_id);
      if (item.updated_by_user_id) ids.add(item.updated_by_user_id);
    }
    if (detail?.created_by_user_id) ids.add(detail.created_by_user_id);
    if (detail?.updated_by_user_id) ids.add(detail.updated_by_user_id);
    return Array.from(ids);
  }, [items, detail]);
  const { nameFor } = useDirectoryUserLabels(authorIds, getAccessToken);

  const loadList = useCallback(async () => {
    setListLoading(true);
    setListError(null);
    try {
      const next = await fetchProcessDocuments(processoId, getAccessToken);
      setItems(next);
      return next;
    } catch (reason) {
      setListError(reason instanceof Error ? reason.message : "Erro ao listar documentação.");
      return null;
    } finally {
      setListLoading(false);
    }
  }, [getAccessToken, processoId]);

  const loadDetail = useCallback(
    async (documentId: string) => {
      setDetailLoading(true);
      setDetailError(null);
      try {
        const next = await fetchProcessDocument(processoId, documentId, getAccessToken);
        setDetail(next);
        return next;
      } catch (reason) {
        setDetail(null);
        setDetailError(reason instanceof Error ? reason.message : "Erro ao abrir documento.");
        return null;
      } finally {
        setDetailLoading(false);
      }
    },
    [getAccessToken, processoId],
  );

  useEffect(() => {
    void loadList();
  }, [loadList]);

  useEffect(() => {
    const syncFromHash = () => {
      const fromHash = parseProcessDocumentIdFromHash(window.location.hash);
      setSelectedId(fromHash);
      if (!fromHash) {
        setDetail(null);
        if (mode !== "create") setMode("view");
      }
    };
    syncFromHash();
    window.addEventListener("hashchange", syncFromHash);
    return () => window.removeEventListener("hashchange", syncFromHash);
  }, [mode]);

  useEffect(() => {
    if (!selectedId || mode === "create") return;
    void loadDetail(selectedId);
  }, [loadDetail, mode, selectedId]);

  const openDocument = (documentId: string) => {
    setMode("view");
    setSaveError(null);
    onNavigate(buildProcessDocumentHref(processoId, documentId));
  };

  const startCreate = () => {
    setMode("create");
    setSelectedId(null);
    setDetail(null);
    setDraftTitle("");
    setDraftMarkdown("");
    setPreviewTab("edit");
    setSaveError(null);
    onNavigate(buildProcessoSectionHref(processoId, "documentacao"));
  };

  const startEdit = () => {
    if (!detail) return;
    setMode("edit");
    setDraftTitle(detail.title);
    setDraftMarkdown(detail.content_md);
    setPreviewTab("edit");
    setSaveError(null);
  };

  const cancelEditor = () => {
    setSaveError(null);
    if (mode === "create") {
      setMode("view");
      setDraftTitle("");
      setDraftMarkdown("");
      return;
    }
    setMode("view");
    if (selectedId) void loadDetail(selectedId);
  };

  const saveDocument = async () => {
    const title = draftTitle.trim();
    if (!title) {
      setSaveError("Informe um título para o documento.");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      if (mode === "create") {
        const created = await createProcessDocument(
          processoId,
          { title, content_md: draftMarkdown },
          getAccessToken,
        );
        await loadList();
        setMode("view");
        onNavigate(buildProcessDocumentHref(processoId, created.id));
        setDetail(created);
        return;
      }
      if (!selectedId) return;
      const updated = await updateProcessDocument(
        processoId,
        selectedId,
        { title, content_md: draftMarkdown },
        getAccessToken,
      );
      await loadList();
      setDetail(updated);
      setMode("view");
    } catch (reason) {
      setSaveError(reason instanceof Error ? reason.message : "Não foi possível salvar.");
    } finally {
      setSaving(false);
    }
  };

  const removeDocument = async () => {
    if (!selectedId || !detail) return;
    const ok = await confirm({
      title: "Excluir documento?",
      message: `O documento “${detail.title}” será removido da documentação deste processo.`,
      confirmLabel: "Excluir",
      cancelLabel: "Cancelar",
      variant: "danger",
    });
    if (!ok) return;
    setDeleting(true);
    try {
      await deleteProcessDocument(processoId, selectedId, getAccessToken);
      const next = await loadList();
      const fallback = next?.[0]?.id ?? null;
      setMode("view");
      setDetail(null);
      if (fallback) {
        onNavigate(buildProcessDocumentHref(processoId, fallback));
      } else {
        onNavigate(buildProcessoSectionHref(processoId, "documentacao"));
      }
    } catch (reason) {
      setDetailError(reason instanceof Error ? reason.message : "Não foi possível excluir.");
    } finally {
      setDeleting(false);
    }
  };

  const editing = mode === "create" || mode === "edit";
  const createdLabel = detail ? nameFor(detail.created_by_user_id) : null;
  const updatedLabel = detail ? nameFor(detail.updated_by_user_id) : null;

  return (
    <section
      className="ds-card tm-processo-workspace-panel tm-process-documentation"
      aria-labelledby="tm-process-documentacao-title"
    >
      <div className="tm-process-documentation__header">
        <div>
          <h2 id="tm-process-documentacao-title" className="ds-section-title">
            Documentação
          </h2>
          <p className="ds-hint">
            Documentos em Markdown que descrevem o processo. Não substituem diagrama, revisão
            nem dados estruturados.
          </p>
        </div>
        {!editing ? (
          <button type="button" className="ds-btn ds-btn--primary" onClick={startCreate}>
            Novo documento
          </button>
        ) : null}
      </div>

      {listError ? (
        <div className="ds-alert ds-alert--error" role="alert">
          {listError}
        </div>
      ) : null}

      <div className="tm-process-documentation__layout">
        <aside className="tm-process-documentation__list" aria-label="Lista de documentos">
          {listLoading ? (
            <LoadingActivityCard
              title="Carregando documentação"
              description="Buscando documentos deste processo."
            />
          ) : null}
          {!listLoading && items.length === 0 && !editing ? (
            <EmptyState
              classNames={EMPTY}
              title="Sem documentação"
              defaultMessage="Nenhum documento de processo registrado."
            >
              <button type="button" className="ds-btn ds-btn--primary" onClick={startCreate}>
                Novo documento
              </button>
            </EmptyState>
          ) : null}
          <ul className="tm-process-documentation__items">
            {items.map((item) => {
              const active = item.id === selectedId && !editing;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={
                      active
                        ? "tm-process-documentation__item is-active"
                        : "tm-process-documentation__item"
                    }
                    aria-current={active ? "true" : undefined}
                    onClick={() => openDocument(item.id)}
                  >
                    <span className="tm-process-documentation__item-title">{item.title}</span>
                    <span className="tm-process-documentation__item-meta">
                      {formatDateTime(item.updated_at)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        <div className="tm-process-documentation__detail" aria-live="polite">
          {editing ? (
            <div className="tm-process-documentation__editor">
              <FieldLabel label="Título" htmlFor="tm-process-doc-title" />
              <NativeTextControl
                id="tm-process-doc-title"
                value={draftTitle}
                onChange={setDraftTitle}
                maxLength={200}
                required
                aria-label="Título do documento"
              />

              <div className="tm-process-documentation__tabs" role="tablist" aria-label="Editor">
                <button
                  type="button"
                  role="tab"
                  aria-selected={previewTab === "edit"}
                  className={previewTab === "edit" ? "is-active" : undefined}
                  onClick={() => setPreviewTab("edit")}
                >
                  Editar
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={previewTab === "preview"}
                  className={previewTab === "preview" ? "is-active" : undefined}
                  onClick={() => setPreviewTab("preview")}
                >
                  Visualizar
                </button>
              </div>

              {previewTab === "edit" ? (
                <>
                  <FieldLabel label="Markdown" htmlFor="tm-process-doc-md" />
                  <textarea
                    id="tm-process-doc-md"
                    className="tm-process-documentation__textarea"
                    value={draftMarkdown}
                    onChange={(event) => setDraftMarkdown(event.target.value)}
                    rows={16}
                    aria-label="Conteúdo Markdown"
                  />
                </>
              ) : (
                <div className="tm-process-documentation__preview" aria-label="Pré-visualização">
                  <h3 className="ds-section-subtitle">Pré-visualização</h3>
                  {draftMarkdown.trim() ? (
                    <MessageBodyReadonly markdown={draftMarkdown} />
                  ) : (
                    <p className="ds-hint">Nada para visualizar ainda.</p>
                  )}
                </div>
              )}

              {saveError ? (
                <div className="ds-alert ds-alert--error" role="alert">
                  {saveError}
                </div>
              ) : null}

              <div className="tm-process-documentation__actions">
                <button
                  type="button"
                  className="ds-btn ds-btn--ghost"
                  onClick={cancelEditor}
                  disabled={saving}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="ds-btn ds-btn--primary"
                  onClick={() => void saveDocument()}
                  disabled={saving}
                  aria-busy={saving || undefined}
                >
                  {saving ? "Salvando…" : "Salvar"}
                </button>
              </div>
            </div>
          ) : null}

          {!editing && detailLoading ? (
            <LoadingActivityCard
              title="Carregando documento"
              description="Abrindo o conteúdo selecionado."
            />
          ) : null}

          {!editing && detailError ? (
            <div className="ds-alert ds-alert--error" role="alert">
              {detailError}
            </div>
          ) : null}

          {!editing && !detailLoading && !detail && items.length > 0 ? (
            <p className="ds-hint">Selecione um documento na lista.</p>
          ) : null}

          {!editing && detail ? (
            <article className="tm-process-documentation__article">
              <header className="tm-process-documentation__article-header">
                <h3 className="ds-section-subtitle">{detail.title}</h3>
                <p className="ds-hint">
                  {createdLabel ? `Criado por ${createdLabel}` : "Criado"}
                  {detail.created_at ? ` · ${formatDateTime(detail.created_at)}` : ""}
                  {" · "}
                  {updatedLabel ? `Atualizado por ${updatedLabel}` : "Atualizado"}
                  {detail.updated_at ? ` · ${formatDateTime(detail.updated_at)}` : ""}
                </p>
                <div className="tm-process-documentation__actions">
                  <button type="button" className="ds-btn ds-btn--ghost" onClick={startEdit}>
                    Editar
                  </button>
                  <button
                    type="button"
                    className="ds-btn ds-btn--danger"
                    onClick={() => void removeDocument()}
                    disabled={deleting}
                    aria-busy={deleting || undefined}
                  >
                    {deleting ? "Excluindo…" : "Excluir"}
                  </button>
                </div>
              </header>
              <div className="tm-process-documentation__body">
                {detail.content_md.trim() ? (
                  <MessageBodyReadonly markdown={detail.content_md} />
                ) : (
                  <p className="ds-hint">Documento sem conteúdo Markdown.</p>
                )}
              </div>
            </article>
          ) : null}
        </div>
      </div>
    </section>
  );
}
