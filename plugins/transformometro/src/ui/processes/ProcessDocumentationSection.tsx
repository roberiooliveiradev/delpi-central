import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  AnchoredPanelPortal,
  ContextMenuItem,
  EmptyState,
  emptyStateCardBemClasses,
  FieldLabel,
  MarkdownDocumentView,
  NativeTextControl,
  buildMarkdownDocumentModel,
} from "@delpi/plugin-ui/index";
import {
  Bold,
  Code,
  GitBranch,
  Heading2,
  Italic,
  Link2,
  List,
  ListChecks,
  MoreHorizontal,
  Pencil,
  Quote,
  Search,
  Table,
  Trash2,
} from "lucide-react";

import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { StateBox } from "../../components/StateBox";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { useUnsavedChangesGuard } from "../../components/ui/UnsavedChangesGuard";
import {
  createProcessDocument,
  deleteProcessDocument,
  fetchProcessDocument,
  fetchProcessDocuments,
  updateProcessDocument,
} from "../../data/api/transformometroProcessDocumentApi";
import { useDirectoryUserLabels } from "../../hooks/useDirectoryUserLabels";
import { useTransformometroEntityWatch } from "../../hooks/useTransformometroEntityWatch";
import type { ProcessDocument, ProcessDocumentSummary } from "../../types/processDocument";
import { getTransformometroClientId } from "../../utils/clientId";
import { formatDateTime } from "../../utils/format";
import {
  buildProcessDocumentHref,
  buildProcessoSectionHref,
  parseProcessDocumentIdFromHash,
} from "./processWorkspaceNav";
import {
  applyMarkdownToolbarAction,
  type MarkdownToolbarAction,
} from "./processDocumentEditor";
import { resolveProcessDocumentEventIntent } from "./processDocumentRealtime";

type Props = {
  processoId: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (href: string) => void;
};

type EditorMode = "view" | "create" | "edit";
type EditorPane = "edit" | "split" | "preview";
type RemoteNotice = { type: "updated" | "deleted" } | null;

const EMPTY = emptyStateCardBemClasses("ds");

const TOOLBAR_GROUPS: Array<
  Array<{ action: MarkdownToolbarAction; label: string; icon: typeof Bold }>
> = [
  [
    { action: "heading", label: "Título de seção", icon: Heading2 },
    { action: "bold", label: "Negrito", icon: Bold },
    { action: "italic", label: "Itálico", icon: Italic },
  ],
  [
    { action: "link", label: "Link", icon: Link2 },
    { action: "list", label: "Lista", icon: List },
    { action: "checklist", label: "Checklist", icon: ListChecks },
    { action: "quote", label: "Citação", icon: Quote },
  ],
  [
    { action: "table", label: "Tabela", icon: Table },
    { action: "code", label: "Bloco de código", icon: Code },
    { action: "mermaid", label: "Diagrama Mermaid", icon: GitBranch },
  ],
];

const EDITOR_PANES: Array<{ id: EditorPane; label: string }> = [
  { id: "edit", label: "Editar" },
  { id: "split", label: "Dividido" },
  { id: "preview", label: "Visualizar" },
];

export function ProcessDocumentationSection({
  processoId,
  getAccessToken,
  onNavigate,
}: Props) {
  const confirm = useConfirm();
  const clientIdRef = useRef(getTransformometroClientId());
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const moreAnchorRef = useRef<HTMLDivElement | null>(null);
  const morePanelRef = useRef<HTMLDivElement | null>(null);
  const readerRef = useRef<HTMLDivElement | null>(null);
  const documentScrollRef = useRef<HTMLDivElement | null>(null);
  const sectionRef = useRef<HTMLElement | null>(null);
  const stickyOffsetRef = useRef(56);

  const [items, setItems] = useState<ProcessDocumentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(() =>
    parseProcessDocumentIdFromHash(window.location.hash),
  );
  const [detail, setDetail] = useState<ProcessDocument | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [mode, setMode] = useState<EditorMode>("view");
  const [draftTitle, setDraftTitle] = useState("");
  const [draftMarkdown, setDraftMarkdown] = useState("");
  const [baseline, setBaseline] = useState<{
    documentId: string | null;
    title: string;
    content_md: string;
  } | null>(null);
  const [editorPane, setEditorPane] = useState<EditorPane>("edit");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [search, setSearch] = useState("");
  const [remoteNotice, setRemoteNotice] = useState<RemoteNotice>(null);
  const [moreOpen, setMoreOpen] = useState(false);
  const [activeHeadingId, setActiveHeadingId] = useState<string | null>(null);

  const editing = mode === "create" || mode === "edit";
  const editingDocumentId = mode === "edit" ? baseline?.documentId ?? null : null;
  const baselineDocumentId = baseline?.documentId ?? null;
  const dirty =
    editing &&
    baseline != null &&
    (draftTitle !== baseline.title || draftMarkdown !== baseline.content_md);

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

  const filteredItems = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((item) => item.title.toLowerCase().includes(needle));
  }, [items, search]);

  const docModel = useMemo(
    () =>
      detail
        ? buildMarkdownDocumentModel(detail.content_md, {
            documentTitle: detail.title,
          })
        : null,
    [detail],
  );

  const draftModel = useMemo(
    () =>
      buildMarkdownDocumentModel(draftMarkdown, { documentTitle: draftTitle }),
    [draftMarkdown, draftTitle],
  );

  const outlineItems = useMemo(() => docModel?.outline ?? [], [docModel]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  useEffect(() => {
    const syncFromHash = () => {
      setSelectedId(parseProcessDocumentIdFromHash(window.location.hash));
    };
    window.addEventListener("hashchange", syncFromHash);
    return () => window.removeEventListener("hashchange", syncFromHash);
  }, []);

  useEffect(() => {
    if (!selectedId || editing) return;
    void loadDetail(selectedId);
  }, [editing, loadDetail, selectedId]);

  // Canonical sticky offset: measured height of the MFE sticky top bar
  // (delpi-ui-topbar--sticky sits at top:0 of the portal `.content` scroller).
  // One measured value feeds rail/outline sticky `top` and heading
  // `scroll-margin-top` via --tm-documentation-sticky-offset.
  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    const scope = section.closest(".dashboard-transformometro") ?? document;
    const topbar =
      scope.querySelector<HTMLElement>(".delpi-ui-topbar--sticky") ??
      scope.querySelector<HTMLElement>(".delpi-ui-topbar");
    const apply = () => {
      const height = Math.ceil(topbar?.getBoundingClientRect().height ?? 0) || 56;
      stickyOffsetRef.current = height;
      section.style.setProperty(
        "--tm-documentation-sticky-offset",
        `${height}px`,
      );
    };
    apply();
    if (!topbar || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(apply);
    observer.observe(topbar);
    return () => observer.disconnect();
  }, []);

  // Active heading highlight in the outline (enhancement only — derived from
  // the DOM, never persisted). The reader uses its own document scroller on
  // desktop, so observation roots on it — not on the portal `.content`.
  // IntersectionObserver callbacks are async, so the setState below never
  // runs synchronously inside the effect body.
  useEffect(() => {
    if (editing || outlineItems.length === 0) return;
    const scroller =
      documentScrollRef.current ??
      sectionRef.current?.closest<HTMLElement>(".content") ??
      null;
    const headings = outlineItems
      .map((item) =>
        readerRef.current?.querySelector<HTMLElement>(
          `#${CSS.escape(item.id)}`,
        ),
      )
      .filter((el): el is HTMLElement => el != null);
    if (headings.length === 0 || typeof IntersectionObserver === "undefined")
      return;
    const pickActive = () => {
      const isInternal = scroller === documentScrollRef.current;
      const limit =
        (scroller?.getBoundingClientRect().top ?? 0) +
        (isInternal ? 24 : stickyOffsetRef.current + 24);
      let current: string | null = null;
      for (const heading of headings) {
        if (heading.getBoundingClientRect().top <= limit) current = heading.id;
      }
      setActiveHeadingId(current ?? headings[0]?.id ?? null);
    };
    const observer = new IntersectionObserver(pickActive, { root: scroller });
    for (const heading of headings) observer.observe(heading);
    return () => observer.disconnect();
  }, [detail, editing, outlineItems]);

  // Remote delete while viewing the deleted doc: deterministic fallback
  // (first remaining doc) or back to the section root when the list is empty.
  const handleRemoteDeleteView = useCallback(async () => {
    setRemoteNotice(null);
    const next = await loadList();
    setDetail(null);
    const target = next?.[0]?.id ?? null;
    onNavigate(
      target
        ? buildProcessDocumentHref(processoId, target)
        : buildProcessoSectionHref(processoId, "documentacao"),
    );
  }, [loadList, onNavigate, processoId]);

  // Realtime invalidation: document writes land on the processo room.
  const handleRemoteEvent = useCallback(
    async (event: Parameters<typeof resolveProcessDocumentEventIntent>[0]) => {
      const intent = resolveProcessDocumentEventIntent(event, {
        selectedId,
        editingDocumentId,
        clientId: clientIdRef.current,
      });
      switch (intent.type) {
        case "ignore":
          return;
        case "refresh-list":
          void loadList();
          return;
        case "refresh-list-and-detail":
          void loadList();
          if (selectedId) void loadDetail(selectedId);
          return;
        case "stale-draft":
          void loadList();
          setRemoteNotice({ type: "updated" });
          return;
        case "remote-delete": {
          void loadList();
          if (intent.editing) {
            setRemoteNotice({ type: "deleted" });
            return;
          }
          void handleRemoteDeleteView();
          return;
        }
      }
    },
    [
      editingDocumentId,
      handleRemoteDeleteView,
      loadDetail,
      loadList,
      selectedId,
    ],
  );

  useTransformometroEntityWatch({
    entities: [{ entityType: "processo", entityId: processoId }],
    getAccessToken,
    enabled: Boolean(processoId),
    onEntityUpdated: (event) => {
      void handleRemoteEvent(event);
    },
  });

  const resetEditor = useCallback(() => {
    setMode("view");
    setBaseline(null);
    setDraftTitle("");
    setDraftMarkdown("");
    setEditorPane("edit");
    setSaveError(null);
    setRemoteNotice(null);
  }, []);

  const openDocument = (documentId: string) => {
    setSaveError(null);
    onNavigate(buildProcessDocumentHref(processoId, documentId));
  };

  const startCreate = () => {
    setMode("create");
    setBaseline({ documentId: null, title: "", content_md: "" });
    setDraftTitle("");
    setDraftMarkdown("");
    setEditorPane("edit");
    setSaveError(null);
    setRemoteNotice(null);
    onNavigate(buildProcessoSectionHref(processoId, "documentacao"));
  };

  const startEdit = () => {
    if (!detail) return;
    setMode("edit");
    setBaseline({
      documentId: detail.id,
      title: detail.title,
      content_md: detail.content_md,
    });
    setDraftTitle(detail.title);
    setDraftMarkdown(detail.content_md);
    setEditorPane("edit");
    setSaveError(null);
    setRemoteNotice(null);
  };

  const cancelEditor = async () => {
    if (dirty) {
      const okLeave = await confirm({
        title: "Descartar alterações?",
        message: "As alterações não salvas deste documento serão perdidas.",
        confirmLabel: "Descartar",
        cancelLabel: "Continuar editando",
        variant: "danger",
      });
      if (!okLeave) return;
    }
    resetEditor();
    if (mode === "edit" && selectedId) void loadDetail(selectedId);
  };

  const saveDocument = useCallback(async () => {
    const title = draftTitle.trim();
    if (!title) {
      setSaveError("Informe um título para o documento.");
      throw new Error("missing title");
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
        resetEditor();
        onNavigate(buildProcessDocumentHref(processoId, created.id));
        setDetail(created);
        return;
      }
      if (!baselineDocumentId) return;
      const updated = await updateProcessDocument(
        processoId,
        baselineDocumentId,
        { title, content_md: draftMarkdown },
        getAccessToken,
      );
      await loadList();
      setDetail(updated);
      resetEditor();
    } catch (reason) {
      setSaveError(reason instanceof Error ? reason.message : "Não foi possível salvar.");
      throw reason;
    } finally {
      setSaving(false);
    }
  }, [
    baselineDocumentId,
    draftMarkdown,
    draftTitle,
    getAccessToken,
    loadList,
    mode,
    onNavigate,
    processoId,
    resetEditor,
  ]);

  useUnsavedChangesGuard({
    id: `processo:${processoId}:documentacao`,
    editing,
    dirty,
    onSave: saveDocument,
    onDiscard: resetEditor,
    enabled: Boolean(processoId),
  });

  const reloadRemoteDocument = async () => {
    if (!baselineDocumentId) return;
    const fresh = await fetchProcessDocument(
      processoId,
      baselineDocumentId,
      getAccessToken,
    );
    setBaseline({
      documentId: fresh.id,
      title: fresh.title,
      content_md: fresh.content_md,
    });
    setDraftTitle(fresh.title);
    setDraftMarkdown(fresh.content_md);
    setRemoteNotice(null);
    setDetail(fresh);
  };

  const removeDocument = async () => {
    if (!selectedId || !detail) return;
    const okLeave = await confirm({
      title: "Excluir documento?",
      message: `O documento “${detail.title}” será removido da documentação deste processo.`,
      confirmLabel: "Excluir",
      cancelLabel: "Cancelar",
      variant: "danger",
    });
    if (!okLeave) return;
    setDeleting(true);
    try {
      await deleteProcessDocument(processoId, selectedId, getAccessToken);
      const next = await loadList();
      setMode("view");
      setDetail(null);
      const fallback = next?.[0]?.id ?? null;
      onNavigate(
        fallback
          ? buildProcessDocumentHref(processoId, fallback)
          : buildProcessoSectionHref(processoId, "documentacao"),
      );
    } catch (reason) {
      setDetailError(reason instanceof Error ? reason.message : "Não foi possível excluir.");
    } finally {
      setDeleting(false);
    }
  };

  const applyToolbar = (action: MarkdownToolbarAction) => {
    const area = textareaRef.current;
    const start = area?.selectionStart ?? draftMarkdown.length;
    const end = area?.selectionEnd ?? start;
    const result = applyMarkdownToolbarAction(draftMarkdown, start, end, action);
    setDraftMarkdown(result.next);
    requestAnimationFrame(() => {
      area?.focus();
      area?.setSelectionRange(result.selectionStart, result.selectionEnd);
    });
  };

  const scrollToHeading = (id: string) => {
    const target = readerRef.current?.querySelector(`#${CSS.escape(id)}`);
    if (!target) return;
    const scroller = documentScrollRef.current;
    if (scroller && scroller.contains(target)) {
      const top =
        target.getBoundingClientRect().top -
        scroller.getBoundingClientRect().top +
        scroller.scrollTop -
        12;
      scroller.scrollTo({ top, behavior: "smooth" });
      return;
    }
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const createdLabel = detail ? nameFor(detail.created_by_user_id) : null;
  const updatedLabel = detail ? nameFor(detail.updated_by_user_id) : null;

  const libraryMode = !editing && selectedId == null;

  const renderPreview = () => (
    <div className="tm-process-documentation__preview" aria-label="Pré-visualização">
      {draftModel.segments.length > 0 ? (
        <MarkdownDocumentView
          model={draftModel}
          onInternalAnchorNavigate={scrollToHeading}
        />
      ) : (
        <p className="ds-hint">Nada para visualizar ainda.</p>
      )}
    </div>
  );

  const searchField = (
    <div className="tm-process-documentation__rail-search">
      <Search size={14} aria-hidden="true" />
      <input
        type="search"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Buscar por título"
        aria-label="Buscar documento por título"
      />
    </div>
  );

  const searchEmptyNotice =
    !listLoading && items.length > 0 && filteredItems.length === 0 ? (
      <p className="ds-hint tm-process-documentation__rail-empty">
        Nenhum documento corresponde a “{search.trim()}”.
        <button
          type="button"
          className="tm-process-documentation__link-btn"
          onClick={() => setSearch("")}
        >
          Limpar busca
        </button>
      </p>
    ) : null;

  return (
    <section
      ref={sectionRef}
      className={`ds-card tm-processo-workspace-panel tm-process-documentation${
        libraryMode ? " is-library" : ""
      }`}
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

      {listError ? <StateBox variant="error">{listError}</StateBox> : null}

      {libraryMode ? (
        <div className="tm-process-documentation__library">
          <div className="tm-process-documentation__library-head">
            {searchField}
            <span className="tm-process-documentation__rail-count">
              {items.length} {items.length === 1 ? "documento" : "documentos"}
            </span>
          </div>

          {listLoading ? (
            <LoadingActivityCard
              title="Carregando documentação"
              description="Buscando documentos deste processo."
            />
          ) : null}

          {searchEmptyNotice}

          {!listLoading && items.length === 0 ? (
            <div className="tm-process-documentation__library-empty">
              <EmptyState
                classNames={EMPTY}
                title="Nenhum documento criado"
                defaultMessage="Este processo ainda não possui documentação registrada."
              />
              <button
                type="button"
                className="ds-btn ds-btn--primary"
                onClick={startCreate}
              >
                Novo documento
              </button>
            </div>
          ) : null}

          <ul className="tm-process-documentation__library-items">
            {filteredItems.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className="tm-process-documentation__library-row"
                  onClick={() => openDocument(item.id)}
                >
                  <span className="tm-process-documentation__library-row-title">
                    {item.title}
                  </span>
                  <span className="tm-process-documentation__library-row-meta">
                    {item.updated_by_user_id
                      ? `Atualizado por ${nameFor(item.updated_by_user_id)} · `
                      : "Atualizado "}
                    {formatDateTime(item.updated_at)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : (
      <div
        className={`tm-process-documentation__layout${
          !editing && outlineItems.length > 0 ? " has-outline" : ""
        }`}
      >
        <aside
          className="tm-process-documentation__rail"
          aria-label="Documentos do processo"
        >
          <div className="tm-process-documentation__rail-head">
            <span className="tm-process-documentation__rail-title">
              Documentos
              <span className="tm-process-documentation__rail-count">{items.length}</span>
            </span>
            {searchField}
          </div>

          {listLoading ? (
            <LoadingActivityCard
              title="Carregando documentação"
              description="Buscando documentos deste processo."
            />
          ) : null}

          {searchEmptyNotice}

          <ul className="tm-process-documentation__items">
            {filteredItems.map((item) => {
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
                    <span className="tm-process-documentation__item-title">
                      {item.title}
                    </span>
                    <span className="tm-process-documentation__item-meta">
                      {formatDateTime(item.updated_at)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        <div
          className="tm-process-documentation__reader"
          aria-live="polite"
          ref={readerRef}
        >
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

              <div
                className="tm-process-documentation__toolbar"
                role="toolbar"
                aria-label="Formatação Markdown"
              >
                {TOOLBAR_GROUPS.map((group, groupIndex) => (
                  <div
                    key={groupIndex}
                    className="tm-process-documentation__tool-group"
                    role="group"
                  >
                    {group.map(({ action, label, icon: Icon }) => (
                      <button
                        key={action}
                        type="button"
                        className="tm-process-documentation__tool"
                        title={label}
                        aria-label={label}
                        onClick={() => applyToolbar(action)}
                      >
                        <Icon size={16} aria-hidden="true" />
                      </button>
                    ))}
                  </div>
                ))}
              </div>

              <div
                className="tm-process-documentation__tabs"
                role="tablist"
                aria-label="Modo do editor"
              >
                {EDITOR_PANES.map((pane) => (
                  <button
                    key={pane.id}
                    type="button"
                    role="tab"
                    aria-selected={editorPane === pane.id}
                    className={
                      editorPane === pane.id ? "is-active" : undefined
                    }
                    onClick={() => setEditorPane(pane.id)}
                  >
                    {pane.label}
                  </button>
                ))}
              </div>

              <div
                className={
                  editorPane === "split"
                    ? "tm-process-documentation__panes is-split"
                    : "tm-process-documentation__panes"
                }
              >
                {editorPane !== "preview" ? (
                  <div className="tm-process-documentation__pane-source">
                    <FieldLabel label="Markdown" htmlFor="tm-process-doc-md" />
                    <textarea
                      id="tm-process-doc-md"
                      ref={textareaRef}
                      className="tm-process-documentation__textarea"
                      value={draftMarkdown}
                      onChange={(event) => setDraftMarkdown(event.target.value)}
                      rows={16}
                      aria-label="Conteúdo Markdown"
                      spellCheck={false}
                    />
                  </div>
                ) : null}
                {editorPane !== "edit" ? renderPreview() : null}
              </div>

              {remoteNotice?.type === "updated" ? (
                <StateBox
                  variant="warning"
                  className="tm-process-documentation__stale"
                >
                  <p>
                    Este documento foi atualizado em outro local enquanto você edita.
                    O servidor já possui uma versão mais nova.
                  </p>
                  <div className="tm-process-documentation__actions">
                    <button
                      type="button"
                      className="ds-btn ds-btn--ghost"
                      onClick={() => void reloadRemoteDocument()}
                    >
                      Recarregar versão atual
                    </button>
                    <button
                      type="button"
                      className="ds-btn ds-btn--ghost"
                      onClick={() => setRemoteNotice(null)}
                    >
                      Continuar com meu rascunho
                    </button>
                  </div>
                </StateBox>
              ) : null}

              {remoteNotice?.type === "deleted" ? (
                <StateBox
                  variant="error"
                  className="tm-process-documentation__stale"
                >
                  O documento original foi removido em outro local. Seu rascunho foi
                  preservado — copie o conteúdo se ainda precisar dele.
                </StateBox>
              ) : null}

              {saveError ? (
                <StateBox variant="error">{saveError}</StateBox>
              ) : null}

              <div className="tm-process-documentation__actions">
                <button
                  type="button"
                  className="ds-btn ds-btn--ghost"
                  onClick={() => void cancelEditor()}
                  disabled={saving}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="ds-btn ds-btn--primary"
                  onClick={() => void saveDocument().catch(() => undefined)}
                  disabled={saving || !dirty || remoteNotice?.type === "deleted"}
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
            <StateBox variant="error">{detailError}</StateBox>
          ) : null}

          {!editing && detail ? (
            <article className="tm-process-documentation__article">
              <header className="tm-process-documentation__article-header">
                <div className="tm-process-documentation__article-heading">
                  <h3 className="ds-section-subtitle">{detail.title}</h3>
                  <p className="ds-hint">
                    {createdLabel ? `Criado por ${createdLabel}` : "Criado"}
                    {detail.created_at ? ` · ${formatDateTime(detail.created_at)}` : ""}
                    {" · "}
                    {updatedLabel ? `Atualizado por ${updatedLabel}` : "Atualizado"}
                    {detail.updated_at ? ` · ${formatDateTime(detail.updated_at)}` : ""}
                  </p>
                </div>
                <div className="tm-process-documentation__article-actions">
                  <button
                    type="button"
                    className="ds-btn ds-btn--ghost"
                    onClick={startEdit}
                  >
                    <Pencil size={14} aria-hidden="true" />
                    Editar
                  </button>
                  <div
                    ref={moreAnchorRef}
                    className="tm-process-documentation__more"
                  >
                    <button
                      type="button"
                      className="ds-btn ds-btn--ghost"
                      aria-label="Mais ações do documento"
                      aria-expanded={moreOpen}
                      aria-haspopup="menu"
                      onClick={() => setMoreOpen((open) => !open)}
                    >
                      <MoreHorizontal size={16} aria-hidden="true" />
                    </button>
                    <AnchoredPanelPortal
                      open={moreOpen}
                      anchorRef={moreAnchorRef}
                      panelRef={morePanelRef}
                      className="delpi-ui-context-menu"
                      variant="bare"
                      role="menu"
                      aria-label="Ações do documento"
                      preferredPlacement="bottom"
                      horizontalAlign="end"
                      gap={10}
                      portalScopeClassName="dashboard-transformometro"
                      onDismiss={() => setMoreOpen(false)}
                    >
                      <ContextMenuItem
                        label={deleting ? "Excluindo…" : "Excluir documento"}
                        icon={Trash2}
                        destructive
                        disabled={deleting}
                        onSelect={() => {
                          setMoreOpen(false);
                          void removeDocument();
                        }}
                      />
                    </AnchoredPanelPortal>
                  </div>
                </div>
              </header>

              <div
                ref={documentScrollRef}
                className="tm-process-documentation__document-scroll"
                role="region"
                aria-label="Conteúdo do documento"
                tabIndex={0}
              >
                {outlineItems.length > 0 ? (
                  <details className="tm-process-documentation__outline-popover">
                    <summary>Sumário</summary>
                    <nav aria-label="Sumário do documento">
                      <ul>
                        {outlineItems.map((item) => (
                          <li key={item.id} data-depth={item.depth}>
                            <button
                              type="button"
                              onClick={() => scrollToHeading(item.id)}
                            >
                              {item.text}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </nav>
                  </details>
                ) : null}

                <div className="tm-process-documentation__body">
                  {detail.content_md.trim() && docModel ? (
                    <MarkdownDocumentView
                      model={docModel}
                      className="tm-process-documentation__markdown"
                      onInternalAnchorNavigate={scrollToHeading}
                    />
                  ) : (
                    <p className="ds-hint">Documento sem conteúdo Markdown.</p>
                  )}
                </div>
              </div>
            </article>
          ) : null}
        </div>

        {!editing && outlineItems.length > 0 ? (
          <aside
            className="tm-process-documentation__outline"
            aria-label="Sumário do documento"
          >
            <span className="tm-process-documentation__outline-title">
              Nesta página
            </span>
            <nav>
              <ul>
                {outlineItems.map((item) => (
                  <li key={item.id} data-depth={item.depth}>
                    <button
                      type="button"
                      className={
                        item.id === activeHeadingId ? "is-active" : undefined
                      }
                      aria-current={
                        item.id === activeHeadingId ? "true" : undefined
                      }
                      onClick={() => {
                        setActiveHeadingId(item.id);
                        scrollToHeading(item.id);
                      }}
                    >
                      {item.text}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>
        ) : null}
      </div>
      )}
    </section>
  );
}
