import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  ActionButton,
  FilePreviewModal,
  HintAction,
  TableColumnVisibilityMenu,
} from "@delpi/plugin-ui/index";
import { AlignLeft, ArrowUpDown, ChevronLeft, ExternalLink, FilterX, FolderTree, Gauge, ListFilter, Plus, RefreshCw, Send, TicketPlus, Type, Users } from "lucide-react";

import {
  HelpdeskApiError,
  beginGlpiLink,
  createFollowup,
  createTicket,
  fetchTicketAttachmentBlob,
  getTicket,
  listCategories,
  listTickets,
  listUrgencies,
  uploadTicketAttachment,
  type TicketAttachment,
  type TicketDetail,
  type TicketSummary,
} from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
import {
  conversationAuthorSrc,
  conversationMessages,
  detailRecordHeading,
  detailRecordSubtitle,
  hasVisibleRichText,
  isTicketFilterActive,
  newIdempotencyKey,
  parseObserverIdsInput,
  parseTicketListFilters,
  statusBadgeVariant,
  stampHelpdeskAttachmentIds,
  nextTicketSort,
  parseTicketSort,
  ticketListSearch,
  ticketRecordFields,
  type TicketListFilters,
  viewForTicketLoad,
} from "../presentation/ticketView";
import {
  listPendingInlineIds,
  normalizeInlineAttachmentSrcs,
  rewritePendingInlineImages,
  stripPendingInlineImages,
} from "../presentation/inlineUpload";
import type { HelpdeskInlineUploadResult } from "../ui/helpdeskUi";
import { helpdeskListPaginationBounds } from "../presentation/listPagination";
import { glpiTicketFormUrl } from "../presentation/glpiPublicLinks";
import { solicitanteLifecycleCue, timelineHasSolution } from "../presentation/solicitanteLifecycle";
import { navigateHelpdesk, type HelpdeskRoute } from "../routing/helpdeskRoute";
import { lastHelpdeskListPath, rememberHelpdeskListPath } from "../presentation/listNavigationMemory";
import {
  clearCreateDraft,
  clearReplyDraft,
  readCreateDraft,
  readReplyDraft,
  writeCreateDraft,
  writeReplyDraft,
} from "../presentation/ticketDraftStorage";
import {
  HELPDESK_CREATE_DRAFT_SCOPE,
  clearHelpdeskDraftPendingFiles,
  pendingFilesMapToDraftRows,
  readHelpdeskDraftPendingFiles,
  replyDraftPendingScope,
  writeHelpdeskDraftPendingFiles,
} from "../presentation/helpdeskDraftPendingFiles";
import {
  persistHelpdeskAttachmentHtml,
  useAuthenticatedAttachmentSrcs,
} from "../presentation/useAuthenticatedAttachmentSrcs";
import { useMyPersonProfilePhoto } from "../presentation/useMyPersonProfilePhoto";
import {
  emptyFilterGroup,
  formatTicketSortLevels,
  parseTicketSortLevels,
  ticketListFiltersFromFilterGroup,
  ticketListViewModelFromFilters,
  type TicketListFilterGroup,
  type TicketListSortLevel,
} from "../presentation/ticketListViewModel";
import { useHelpdeskTicketListColumns } from "../presentation/useHelpdeskTicketListColumns";
import { TicketAttachmentPreview } from "./TicketAttachmentPreview";
import { TicketListCards } from "./TicketListCards";
import { TicketListFilterBuilder } from "./TicketListFilterBuilder";
import { TicketListSortBuilder } from "./TicketListSortBuilder";
import { TicketListTable } from "./TicketListTable";
import { TicketListToolbar } from "./TicketListToolbar";
import {
  HELPDESK_TICKET_LIST_VIEW_LAYOUT_KEY,
  HelpdeskEmptyState,
  HelpdeskFormActions,
  HelpdeskIconButton,
  HelpdeskListPaginationFooter,
  HelpdeskLoadingState,
  HelpdeskMessageThread,
  HelpdeskPageHeader,
  HelpdeskRecordCard,
  HelpdeskRichTextField,
  HelpdeskSectionCard,
  HelpdeskSegmentToggle,
  HelpdeskSelect,
  HelpdeskStateBanner,
  HelpdeskStatusBadge,
  HelpdeskTextField,
  usePersistedViewLayout,
} from "../ui/helpdeskUi";

const MESSAGES: Record<string, string> = {
  forbidden: "Você não tem permissão para Meus Chamados de TI.",
  glpi_forbidden: "O helpdesk recusou este chamado para o seu usuário.",
  glpi_unavailable: "O helpdesk está indisponível. Tente novamente em instantes.",
  glpi_feature_disabled: "O envio de anexo está desligado neste ambiente.",
  not_found: "Este chamado não está disponível para você.",
  validation_error: "Revise os campos e envie de novo.",
  idempotency_key_required: "Não foi possível confirmar o envio. Atualize a página e tente outra vez.",
  catalog_unavailable: "Não foi possível carregar as categorias do helpdesk.",
};

function messageFor(error: unknown): { code: string; text: string } {
  if (error instanceof HelpdeskApiError) {
    return { code: error.code, text: MESSAGES[error.code] || "Não foi possível concluir a operação." };
  }
  if (error instanceof Error && error.message.startsWith("Não foi possível")) {
    return { code: "user_message", text: error.message };
  }
  return { code: "request_failed", text: "Não foi possível concluir a operação." };
}

export function HelpdeskPage({ route }: { route: HelpdeskRoute }) {
  if (route.kind === "new") return <CreateTicketPage />;
  if (route.kind === "detail") return <TicketDetailPage ticketId={route.ticketId} />;
  if (route.kind === "unknown") {
    return <HelpdeskStateBanner variant="error">Endereço não encontrado em Meus Chamados de TI.</HelpdeskStateBanner>;
  }
  return <TicketListPage />;
}

function HelpdeskPageStack({ children }: { children: ReactNode }) {
  return <div className="helpdesk-page-stack">{children}</div>;
}

function HelpdeskBackButton({ hint }: { hint?: string }) {
  const button = (
    <HelpdeskIconButton aria-label="Voltar" onClick={() => navigateHelpdesk(lastHelpdeskListPath())}>
      <ChevronLeft size={16} aria-hidden />
    </HelpdeskIconButton>
  );
  if (!hint) return button;
  return (
    <HintAction hint={hint} ariaLabel="Ajuda: Voltar">
      {button}
    </HintAction>
  );
}

function currentListFilters(): TicketListFilters {
  return parseTicketListFilters(typeof window === "undefined" ? "" : window.location.search);
}

function writeListFilters(filters: TicketListFilters) {
  const path = `/apps/helpdesk${ticketListSearch(filters)}`;
  window.history.replaceState({}, "", path);
  rememberHelpdeskListPath(path);
}

function TicketListPage() {
  const [filters, setFilters] = useState(currentListFilters);
  const [items, setItems] = useState<TicketSummary[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const [urgencies, setUrgencies] = useState<{ id: number; name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [linking, setLinking] = useState(false);
  const [showFilterBuilder, setShowFilterBuilder] = useState(true);
  const [showSortBuilder, setShowSortBuilder] = useState(false);
  const [builderGroup, setBuilderGroup] = useState<TicketListFilterGroup>(() =>
    ticketListViewModelFromFilters(filters).filterRoot,
  );
  const [sortDraft, setSortDraft] = useState<TicketListSortLevel[]>(() =>
    parseTicketSortLevels(filters.sort),
  );
  const {
    columnPreferences,
    menuColumns,
    visibility,
    setColumnVisible,
    reorderColumns,
    resetPreferences,
  } = useHelpdeskTicketListColumns();
  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: HELPDESK_TICKET_LIST_VIEW_LAYOUT_KEY,
    defaultMode: "table",
  });
  const showCards = layout === "cards";

  useEffect(() => {
    rememberHelpdeskListPath(`/apps/helpdesk${ticketListSearch(filters)}`);
  }, [filters]);

  function commitFilters(next: TicketListFilters) {
    setFilters(next);
    writeListFilters(next);
  }

  function clearListFilters() {
    commitFilters({
      ...currentListFilters(),
      q: "",
      status: "",
      urgency_id: "",
      category_id: "",
      updated_from: "",
      updated_to: "",
      created_from: "",
      created_to: "",
      page: 1,
      sort: filters.sort,
      page_size: filters.page_size,
    });
  }

  async function load(next = filters) {
    setLoading(true);
    setErrorCode(null);
    setErrorText(null);
    try {
      const body = await listTickets({
        q: next.q || undefined,
        status: next.status || undefined,
        urgency_id: next.urgency_id || undefined,
        category_id: next.category_id || undefined,
        updated_from: next.updated_from || undefined,
        updated_to: next.updated_to || undefined,
        created_from: next.created_from || undefined,
        created_to: next.created_to || undefined,
        sort: next.sort || undefined,
        page: next.page,
        page_size: next.page_size,
      });
      setItems(body.items);
      setHasMore(body.has_more);
    } catch (error) {
      const mapped = messageFor(error);
      setItems([]);
      setHasMore(false);
      setErrorCode(mapped.code);
      setErrorText(mapped.text);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(filters);
  }, [filters]);

  useEffect(() => {
    void Promise.all([listCategories(), listUrgencies()])
      .then(([categoryBody, urgencyBody]) => {
        setCategories(categoryBody.items);
        setUrgencies(urgencyBody.items);
      })
      .catch(() => {
        setCategories([]);
        setUrgencies([]);
      });
  }, []);

  useEffect(() => {
    const onPop = () => {
      setFilters(currentListFilters());
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const view = viewForTicketLoad({
    loading,
    errorCode,
    itemCount: items.length,
    filterActive: isTicketFilterActive(filters),
  });
  const filterActive = isTicketFilterActive(filters);
  const listViewModel = ticketListViewModelFromFilters(filters, columnPreferences);
  const paginationBounds = helpdeskListPaginationBounds({
    page: filters.page,
    pageSize: filters.page_size,
    itemCount: items.length,
    hasMore,
  });

  useEffect(() => {
    setBuilderGroup(ticketListViewModelFromFilters(filters).filterRoot);
    setSortDraft(parseTicketSortLevels(filters.sort));
  }, [filters]);

  return (
    <HelpdeskPageStack>
      <HelpdeskPageHeader
        title="Meus Chamados de TI"
        subtitle="Chamados no seu nome"
        compact
        actions={
          <HintAction hint={helpTooltips.listUi.refreshPage} ariaLabel="Ajuda: Atualizar">
            <HelpdeskIconButton
              tone="primary"
              aria-label="Atualizar"
              disabled={loading}
              onClick={() => void load(filters)}
            >
              <RefreshCw size={16} aria-hidden />
            </HelpdeskIconButton>
          </HintAction>
        }
      />
      <HelpdeskSectionCard
        title="Meus chamados"
        hint={helpTooltips.list}
        fill
        actions={
          <HintAction hint={helpTooltips.listUi.openTicket} ariaLabel="Ajuda: Abrir chamado">
            <HelpdeskIconButton
              tone="primary"
              aria-label="Abrir chamado"
              onClick={() => navigateHelpdesk("/apps/helpdesk/tickets/new")}
            >
              <Plus size={16} aria-hidden />
            </HelpdeskIconButton>
          </HintAction>
        }
      >
        {view === "link" || view === "forbidden" ? null : (
          <TicketListToolbar
            viewModel={listViewModel}
            onRefresh={() => {
              void load(filters);
            }}
            leading={
              <HintAction hint={helpTooltips.listUi.viewLayout} ariaLabel="Ajuda: Tabela ou Cards">
                <HelpdeskSegmentToggle
                  ariaLabel="Modo de visualização"
                  idPrefix="helpdesk-ticket-list-layout"
                  size="sm"
                  value={showCards ? "cards" : "table"}
                  onChange={(value) => {
                    if (value === "table" || value === "cards") setLayout(value);
                  }}
                  options={[
                    { value: "table", label: "Tabela" },
                    { value: "cards", label: "Cards" },
                  ]}
                />
              </HintAction>
            }
            clearFiltersSlot={
              filterActive ? (
                <HintAction hint={helpTooltips.listUi.clearFilters} ariaLabel="Ajuda: Limpar filtros">
                  <HelpdeskIconButton aria-label="Limpar filtros" onClick={clearListFilters}>
                    <FilterX size={16} aria-hidden />
                  </HelpdeskIconButton>
                </HintAction>
              ) : null
            }
            filterBuilderToggle={
              <HintAction
                hint={helpTooltips.listUi.filterBuilderToggle}
                ariaLabel="Ajuda: Construtor de filtros"
              >
                <HelpdeskIconButton
                  aria-label={showFilterBuilder ? "Fechar construtor de filtros" : "Abrir construtor de filtros"}
                  onClick={() => {
                    setShowFilterBuilder((open) => {
                      if (!open) {
                        setBuilderGroup(ticketListViewModelFromFilters(filters, columnPreferences).filterRoot);
                      }
                      return !open;
                    });
                    setShowSortBuilder(false);
                  }}
                >
                  <ListFilter size={16} aria-hidden />
                </HelpdeskIconButton>
              </HintAction>
            }
            sortBuilderSlot={
              <HintAction
                hint={helpTooltips.listUi.sortBuilderToggle}
                ariaLabel="Ajuda: Ordenação"
              >
                <HelpdeskIconButton
                  aria-label={showSortBuilder ? "Fechar ordenação" : "Ordenação em níveis"}
                  onClick={() => {
                    setShowSortBuilder((open) => {
                      if (!open) setSortDraft(parseTicketSortLevels(filters.sort));
                      return !open;
                    });
                    setShowFilterBuilder(false);
                  }}
                >
                  <ArrowUpDown size={16} aria-hidden />
                </HelpdeskIconButton>
              </HintAction>
            }
            columnPreferencesSlot={
              showCards ? null : (
                <HintAction hint={helpTooltips.listUi.columns} ariaLabel="Ajuda: Colunas">
                  <TableColumnVisibilityMenu
                    columns={menuColumns}
                    visibility={visibility}
                    onToggleColumn={setColumnVisible}
                    onReset={resetPreferences}
                    onReorderColumns={reorderColumns}
                    labels={{
                      trigger: "Colunas",
                      panelTitle: "Colunas da lista",
                      reset: "Restaurar padrão",
                      hint: helpTooltips.listUi.columns,
                      columnAriaLabel: (label) => `Mostrar coluna ${label}`,
                    }}
                  />
                </HintAction>
              )
            }
          />
        )}
        {showFilterBuilder && view !== "link" && view !== "forbidden" ? (
          <TicketListFilterBuilder
            group={builderGroup}
            onChange={setBuilderGroup}
            urgencies={urgencies}
            categories={categories}
            onClear={() => setBuilderGroup(emptyFilterGroup())}
            onApply={() => {
              const next = ticketListFiltersFromFilterGroup(builderGroup, filters);
              commitFilters(next);
              setShowFilterBuilder(false);
            }}
          />
        ) : null}
        {showSortBuilder && view !== "link" && view !== "forbidden" ? (
          <TicketListSortBuilder
            levels={sortDraft}
            onChange={setSortDraft}
            onApply={() => {
              commitFilters({ ...filters, sort: formatTicketSortLevels(sortDraft), page: 1 });
              setShowSortBuilder(false);
            }}
          />
        ) : null}
        {view === "loading" ? <HelpdeskLoadingState /> : null}
        {view === "forbidden" || view === "unavailable" || view === "error" ? (
          <HelpdeskStateBanner variant="error">{errorText}</HelpdeskStateBanner>
        ) : null}
        {view === "link" ? (
          <HelpdeskStateBanner>
            {helpTooltips.link}
            <HelpdeskFormActions>
              <ActionButton
                variant="primary"
                disabled={linking}
                onClick={() => {
                  setLinking(true);
                  void beginGlpiLink()
                    .then((url) => {
                      window.location.assign(url);
                    })
                    .catch((error) => {
                      setErrorText(messageFor(error).text);
                      setLinking(false);
                    });
                }}
              >
                Autorizar no helpdesk
              </ActionButton>
            </HelpdeskFormActions>
          </HelpdeskStateBanner>
        ) : null}
        {view === "empty" ? (
          <HelpdeskEmptyState
            message={filterActive ? "Nenhum chamado neste recorte." : undefined}
          />
        ) : null}
        {view === "list" ? (
          showCards ? (
            <TicketListCards
              items={items}
              onOpen={(ticketId) => navigateHelpdesk(`/apps/helpdesk/tickets/${ticketId}`)}
            />
          ) : (
            <TicketListTable
              items={items}
              loading={loading}
              sort={parseTicketSort(filters.sort)}
              columnPreferences={columnPreferences}
              onSortChange={(columnKey) =>
                commitFilters({ ...filters, sort: nextTicketSort(filters.sort, columnKey), page: 1 })
              }
              onOpen={(ticketId) => navigateHelpdesk(`/apps/helpdesk/tickets/${ticketId}`)}
            />
          )
        ) : null}
        {view === "list" || (view === "empty" && filters.page > 1) ? (
          <HelpdeskListPaginationFooter
            page={filters.page}
            pageSize={filters.page_size}
            total={paginationBounds.total}
            onPageChange={(page) => commitFilters({ ...filters, page })}
            onPageSizeChange={(page_size) =>
              commitFilters({ ...filters, page_size: page_size || 20, page: 1 })
            }
          />
        ) : null}
      </HelpdeskSectionCard>
    </HelpdeskPageStack>
  );
}

function CreateTicketPage() {
  const savedDraft = readCreateDraft();
  const [title, setTitle] = useState(savedDraft?.title ?? "");
  const [description, setDescription] = useState(() =>
    persistHelpdeskAttachmentHtml(savedDraft?.description ?? ""),
  );
  const [observerIdsInput, setObserverIdsInput] = useState(savedDraft?.observerIdsInput ?? "");
  const [categoryId, setCategoryId] = useState(savedDraft?.categoryId ?? "");
  const [urgencyId, setUrgencyId] = useState(savedDraft?.urgencyId ?? "");
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const [urgencies, setUrgencies] = useState<{ id: number; name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [idempotencyKey] = useState(newIdempotencyKey);
  const [pendingHydrated, setPendingHydrated] = useState(0);
  const pendingFilesRef = useRef<Map<string, File>>(new Map());
  const pendingPreviewUrlsRef = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    return () => {
      for (const url of pendingPreviewUrlsRef.current.values()) {
        try {
          URL.revokeObjectURL(url);
        } catch {
          /* ignore */
        }
      }
      pendingPreviewUrlsRef.current.clear();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    void readHelpdeskDraftPendingFiles(HELPDESK_CREATE_DRAFT_SCOPE).then((rows) => {
      if (cancelled) return;
      for (const row of rows) {
        pendingFilesRef.current.set(row.id, row.file);
      }
      if (rows.length > 0) setPendingHydrated((n) => n + 1);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const persistCreatePendingFiles = useCallback(() => {
    void writeHelpdeskDraftPendingFiles(
      HELPDESK_CREATE_DRAFT_SCOPE,
      pendingFilesMapToDraftRows(pendingFilesRef.current),
    );
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void Promise.allSettled([listCategories(controller.signal), listUrgencies(controller.signal)])
      .then(([categoryResult, urgencyResult]) => {
        if (controller.signal.aborted) return;
        const draft = readCreateDraft();
        if (urgencyResult.status === "fulfilled") {
          const items = urgencyResult.value.items;
          setUrgencies(items);
          setUrgencyId((current) => {
            if (current && items.some((item) => String(item.id) === current)) return current;
            if (draft?.urgencyId && items.some((item) => String(item.id) === draft.urgencyId)) {
              return draft.urgencyId;
            }
            return items[0] ? String(items[0].id) : "";
          });
        }
        if (categoryResult.status === "fulfilled") {
          const items = categoryResult.value.items;
          setCategories(items);
          setCategoryId((current) => {
            if (current && items.some((item) => String(item.id) === current)) return current;
            if (draft?.categoryId && items.some((item) => String(item.id) === draft.categoryId)) {
              return draft.categoryId;
            }
            return items[0] ? String(items[0].id) : "";
          });
          return;
        }
        setErrorText(MESSAGES.catalog_unavailable);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    writeCreateDraft({
      title,
      description: persistHelpdeskAttachmentHtml(description),
      observerIdsInput,
      categoryId,
      urgencyId,
    });
  }, [title, description, observerIdsInput, categoryId, urgencyId]);

  const resolveCreatePendingSrc = useCallback(
    (attachmentId: string) => {
      const cached = pendingPreviewUrlsRef.current.get(attachmentId);
      if (cached) return cached;
      const file = pendingFilesRef.current.get(attachmentId);
      if (!file) return null;
      const url = URL.createObjectURL(file);
      pendingPreviewUrlsRef.current.set(attachmentId, url);
      return url;
    },
    // pendingHydrated forces re-bind after IDB restore so RichTextEditor re-resolves srcs
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [pendingHydrated],
  );

  const persistCreatePendingSrc = useCallback((attachmentId: string) => {
    const pending = String(attachmentId || "").trim();
    if (!pending) return null;
    return `attachment:pending:${pending}`;
  }, []);

  const queuePendingFiles = async (files: File[]): Promise<HelpdeskInlineUploadResult[]> => {
    const results: HelpdeskInlineUploadResult[] = [];
    for (const file of files) {
      const pendingId = newIdempotencyKey();
      pendingFilesRef.current.set(pendingId, file);
      if (file.type.startsWith("image/") || /\.(png|jpe?g|gif|webp|bmp)$/i.test(file.name || "")) {
        let src = pendingPreviewUrlsRef.current.get(pendingId);
        if (!src) {
          src = URL.createObjectURL(file);
          pendingPreviewUrlsRef.current.set(pendingId, src);
        }
        results.push({
          kind: "pending",
          pendingId,
          src,
          alt: file.name || "imagem",
        });
      }
    }
    persistCreatePendingFiles();
    return results;
  };

  return (
    <HelpdeskPageStack>
      <HelpdeskPageHeader
        title="Abrir chamado"
        subtitle="No seu nome, na entidade padrão do helpdesk"
        compact
        nav={<HelpdeskBackButton hint={helpTooltips.createUi.back} />}
        icon={<TicketPlus size={18} aria-hidden />}
      />
      <HelpdeskSectionCard title="Abrir chamado" hint={helpTooltips.create} fill>
        {loading ? <HelpdeskLoadingState message="Carregando categorias…" /> : null}
        {errorText ? <HelpdeskStateBanner variant="error">{errorText}</HelpdeskStateBanner> : null}
        <form
          className="helpdesk-create-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (saving || !title.trim() || !hasVisibleRichText(description)) return;
            setSaving(true);
            setErrorText(null);
            const pendingIds = [
              ...new Set([...listPendingInlineIds(description), ...pendingFilesRef.current.keys()]),
            ];
            const openingHtml = stripPendingInlineImages(description).trim() || "<p>Anexo(s)</p>";
            void createTicket(
              {
                title: title.trim(),
                description: openingHtml,
                category_id: Number(categoryId),
                urgency_id: Number(urgencyId),
                observer_ids: parseObserverIdsInput(observerIdsInput),
              },
              idempotencyKey,
            )
              .then(async (created) => {
                const ticketId = String(created.id);
                const mapping: Record<string, { documentId: number; ticketId: string }> = {};
                for (const pendingId of pendingIds) {
                  const file = pendingFilesRef.current.get(pendingId);
                  if (!file) continue;
                  const uploaded = await uploadTicketAttachment(
                    ticketId,
                    file,
                    `${idempotencyKey}:file:${pendingId}`,
                  );
                  if (file.type.startsWith("image/")) {
                    mapping[pendingId] = { documentId: uploaded.document_id, ticketId };
                  }
                  pendingFilesRef.current.delete(pendingId);
                }
                if (Object.keys(mapping).length > 0) {
                  const rewritten = rewritePendingInlineImages(description, mapping);
                  const imageBlocks = rewritten.match(/<p>\s*<img\b[\s\S]*?<\/p>/gi) || [];
                  if (imageBlocks.length > 0) {
                    await createFollowup(
                      ticketId,
                      imageBlocks.join(""),
                      `${idempotencyKey}:images`,
                    );
                  }
                }
                clearCreateDraft();
                void clearHelpdeskDraftPendingFiles(HELPDESK_CREATE_DRAFT_SCOPE);
                navigateHelpdesk(`/apps/helpdesk/tickets/${created.id}`);
              })
              .catch((error) => {
                setErrorText(messageFor(error).text);
                setSaving(false);
              });
          }}
        >
          <div className="helpdesk-create-layout">
            <div className="helpdesk-create-layout__main">
              <HelpdeskTextField
                label="Título"
                hint={helpTooltips.createUi.title}
                value={title}
                onChange={setTitle}
                required
                icon={<Type size={14} aria-hidden />}
              />
              <HelpdeskRichTextField
                label="Descrição"
                hint={helpTooltips.createUi.description}
                attachHint={helpTooltips.createUi.attach}
                value={description}
                onChange={(next) => setDescription(persistHelpdeskAttachmentHtml(next))}
                minHeight={220}
                icon={<AlignLeft size={14} aria-hidden />}
                onUploadFiles={queuePendingFiles}
                onUploadError={(error) => setErrorText(messageFor(error).text)}
                resolveAttachmentImageSrc={resolveCreatePendingSrc}
                persistAttachmentImageSrc={persistCreatePendingSrc}
              />
            </div>
            <aside className="helpdesk-create-layout__aside" aria-label="Classificação do chamado">
              <HelpdeskSelect
                label="Categoria"
                hint={helpTooltips.createUi.category}
                value={categoryId}
                onChange={setCategoryId}
                required
                searchable
                options={categories.map((item) => ({ value: String(item.id), label: item.name }))}
                icon={<FolderTree size={14} aria-hidden />}
              />
              <HelpdeskSelect
                label="Urgência"
                hint={helpTooltips.createUi.urgency}
                value={urgencyId}
                onChange={setUrgencyId}
                required
                options={urgencies.map((item) => ({ value: String(item.id), label: item.name }))}
                icon={<Gauge size={14} aria-hidden />}
              />
              <HelpdeskTextField
                label="Observadores"
                hint={helpTooltips.createUi.observers}
                value={observerIdsInput}
                onChange={setObserverIdsInput}
                icon={<Users size={14} aria-hidden />}
              />
              <div className="helpdesk-create-layout__aside-actions">
                <HintAction hint={helpTooltips.createUi.send} ariaLabel="Ajuda: Enviar chamado">
                  <ActionButton
                    variant="primary"
                    type="submit"
                    className="helpdesk-create-send"
                    aria-label={saving ? "Enviando" : "Enviar chamado"}
                    disabled={saving || loading || !title.trim() || !hasVisibleRichText(description)}
                  >
                    <Send size={18} aria-hidden />
                    {saving ? "Enviando…" : "Enviar"}
                  </ActionButton>
                </HintAction>
              </div>
            </aside>
          </div>
        </form>
      </HelpdeskSectionCard>
    </HelpdeskPageStack>
  );
}

function TicketDetailPage({ ticketId }: { ticketId: string }) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [content, setContent] = useState(() =>
    persistHelpdeskAttachmentHtml(
      normalizeInlineAttachmentSrcs(stampHelpdeskAttachmentIds(readReplyDraft(ticketId)), ticketId),
      ticketId,
    ),
  );
  const [saving, setSaving] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [inlinePreview, setInlinePreview] = useState<TicketAttachment | null>(null);
  const myPhotoUrl = useMyPersonProfilePhoto();
  const pendingFilesRef = useRef<Map<string, File>>(new Map());

  const conversationHtml = useMemo(() => {
    if (!ticket) return "";
    return conversationMessages(ticket, new Date())
      .map((message) => message.bodyHtml || "")
      .join("\n");
  }, [ticket]);

  const attachmentPreview = useAuthenticatedAttachmentSrcs({
    ticketId,
    html: `${content}\n${conversationHtml}`,
    fetchBlob: fetchTicketAttachmentBlob,
    extraDocumentIds: ticket?.attachments.map((item) => item.document_id),
  });

  const persistReplyPendingFiles = useCallback(() => {
    void writeHelpdeskDraftPendingFiles(
      replyDraftPendingScope(ticketId),
      pendingFilesMapToDraftRows(pendingFilesRef.current),
    );
  }, [ticketId]);

  useEffect(() => {
    let cancelled = false;
    void readHelpdeskDraftPendingFiles(replyDraftPendingScope(ticketId)).then((rows) => {
      if (cancelled || rows.length === 0) return;
      for (const row of rows) {
        pendingFilesRef.current.set(row.id, row.file);
        attachmentPreview.seedFile(row.id, row.file);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [ticketId, attachmentPreview.seedFile]);

  useEffect(() => {
    writeReplyDraft(ticketId, attachmentPreview.persistHtml(content));
  }, [ticketId, content, attachmentPreview.persistHtml]);

  function load() {
    setLoading(true);
    setErrorText(null);
    void getTicket(ticketId)
      .then(setTicket)
      .catch((error) => setErrorText(messageFor(error).text))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, [ticketId]);

  return (
    <HelpdeskPageStack>
      <HelpdeskPageHeader
        title={ticket?.title || "Chamado"}
        compact
        nav={<HelpdeskBackButton hint={helpTooltips.detailUi.back} />}
        onRefresh={load}
        refreshing={loading}
      />
      <HelpdeskSectionCard title="Conversa" hint={helpTooltips.detail} fill>
        {loading ? <HelpdeskLoadingState message="Carregando chamado…" /> : null}
        {errorText ? <HelpdeskStateBanner variant="error">{errorText}</HelpdeskStateBanner> : null}
        {ticket ? (
          <>
            <HelpdeskRecordCard
              title={detailRecordHeading(ticket.category, ticket.urgency).title}
              subtitle={detailRecordSubtitle({
                id: ticket.id,
                urgency: ticket.urgency,
                assigned_display_name: ticket.assigned_display_name,
              })}
              status={<HelpdeskStatusBadge label={ticket.status} variant={statusBadgeVariant(ticket.status_id)} />}
              fields={ticketRecordFields({
                id: ticket.id,
                category: ticket.category,
                urgency: ticket.urgency,
                assigned_display_name: ticket.assigned_display_name,
                observers_display_name: ticket.observers_display_name,
                created_at: ticket.created_at,
                updated_at: ticket.updated_at,
                solved_at: ticket.solved_at,
                closed_at: ticket.closed_at,
                sla_ttr: ticket.sla_ttr,
                sla_tto: ticket.sla_tto,
              })
                .filter((field) =>
                  ["observers", "sla_ttr", "sla_tto", "created_at", "updated_at", "solved_at", "closed_at"].includes(
                    field.id,
                  ),
                )
                .map((field) => ({
                  id: field.id,
                  label: field.label,
                  value: field.value,
                  present: field.present,
                }))}
            />
            {(() => {
              const cue = solicitanteLifecycleCue({
                statusId: ticket.status_id,
                hasSolution: timelineHasSolution(ticket.timeline),
              });
              if (!cue) return null;
              return (
                <div className="helpdesk-lifecycle-cue">
                  <HelpdeskStateBanner variant={cue.variant}>
                    <div className="helpdesk-lifecycle-cue__row">
                      <p className="helpdesk-lifecycle-cue__text">{cue.message}</p>
                      <HintAction hint={helpTooltips.detailUi.openInGlpi} ariaLabel="Ajuda: Abrir no helpdesk">
                        <ActionButton
                          variant="primary"
                          type="button"
                          className="helpdesk-lifecycle-cue__cta"
                          aria-label={cue.ctaLabel}
                          onClick={() => {
                            window.open(glpiTicketFormUrl(ticket.id), "_blank", "noopener,noreferrer");
                          }}
                        >
                          <ExternalLink size={16} aria-hidden />
                          {cue.ctaLabel}
                        </ActionButton>
                      </HintAction>
                    </div>
                  </HelpdeskStateBanner>
                </div>
              );
            })()}
            <HelpdeskMessageThread
              listAriaLabel="Conversa do chamado"
              emptyLabel="Nenhuma mensagem"
              resolveAttachmentImageSrc={attachmentPreview.resolveAttachmentImageSrc}
              onAttachmentImageClick={(attachmentId) => {
                const documentId = Number(attachmentId);
                if (!Number.isFinite(documentId)) return;
                const known = ticket.attachments.find((item) => item.document_id === documentId);
                setInlinePreview(
                  known ?? {
                    document_id: documentId,
                    filename: "imagem",
                    mime: "image/*",
                  },
                );
              }}
              messages={conversationMessages(ticket, new Date()).map((message) => ({
                id: message.id,
                kind: message.kind,
                headingText: message.headingText || undefined,
                bodyText: message.bodyText,
                bodyHtml: message.bodyHtml || undefined,
                createdAtLabel: message.createdAtLabel,
                authorName: message.authorName || undefined,
                authorSrc: conversationAuthorSrc(message.mine, myPhotoUrl),
                mine: message.mine,
                belowBody:
                  message.attachmentIds.length > 0 ? (
                    <TicketAttachmentPreview
                      ticketId={ticketId}
                      attachments={ticket.attachments.filter((item) => message.attachmentIds.includes(item.document_id))}
                      onError={(text) => setErrorText(text)}
                    />
                  ) : undefined,
              }))}
            />
            <FilePreviewModal
              open={Boolean(inlinePreview)}
              title={inlinePreview?.filename || "Anexo"}
              fileName={inlinePreview?.filename}
              mimeType={inlinePreview?.mime}
              source={
                inlinePreview
                  ? () => fetchTicketAttachmentBlob(ticketId, inlinePreview.document_id)
                  : null
              }
              portalScopeClassName="dashboard-helpdesk"
              onClose={() => setInlinePreview(null)}
              headerActions={
                inlinePreview ? (
                  <ActionButton
                    onClick={() => {
                      void fetchTicketAttachmentBlob(ticketId, inlinePreview.document_id)
                        .then((blob) => {
                          const url = URL.createObjectURL(blob);
                          const link = document.createElement("a");
                          link.href = url;
                          link.download = inlinePreview.filename || "anexo";
                          link.click();
                          URL.revokeObjectURL(url);
                        })
                        .catch((error) => setErrorText(messageFor(error).text));
                    }}
                  >
                    Baixar
                  </ActionButton>
                ) : null
              }
            />
            {ticket.can_followup !== false ? (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                if (saving || !hasVisibleRichText(content)) return;
                setSaving(true);
                const payload = attachmentPreview.persistHtml(content.trim());
                void createFollowup(ticketId, payload, idempotencyKey)
                  .then(() => {
                    setContent("");
                    clearReplyDraft(ticketId);
                    pendingFilesRef.current.clear();
                    void clearHelpdeskDraftPendingFiles(replyDraftPendingScope(ticketId));
                    setIdempotencyKey(newIdempotencyKey());
                    load();
                  })
                  .catch((error) => setErrorText(messageFor(error).text))
                  .finally(() => setSaving(false));
              }}
            >
              <HelpdeskRichTextField
                label="Responder"
                hint={helpTooltips.detailUi.reply}
                attachHint={helpTooltips.detailUi.attach}
                value={content}
                onChange={(next) => setContent(attachmentPreview.persistHtml(next))}
                minHeight={120}
                resolveAttachmentImageSrc={attachmentPreview.resolveAttachmentImageSrc}
                persistAttachmentImageSrc={attachmentPreview.persistAttachmentImageSrc}
                onUploadFiles={async (files) => {
                  // InteractionRoom parity: pending local first, upload rewrite after.
                  const results: HelpdeskInlineUploadResult[] = [];
                  const pendingUploads: { pendingId: string; file: File }[] = [];
                  for (const file of files) {
                    const isImage =
                      file.type.startsWith("image/") ||
                      /\.(png|jpe?g|gif|webp|bmp)$/i.test(file.name || "");
                    if (!isImage) {
                      await uploadTicketAttachment(ticketId, file, newIdempotencyKey());
                      continue;
                    }
                    const pendingId = newIdempotencyKey();
                    pendingFilesRef.current.set(pendingId, file);
                    const src = attachmentPreview.seedFile(pendingId, file);
                    results.push({
                      kind: "pending",
                      pendingId,
                      src,
                      alt: file.name || "imagem",
                    });
                    pendingUploads.push({ pendingId, file });
                  }
                  persistReplyPendingFiles();
                  if (pendingUploads.length > 0) {
                    void (async () => {
                      const mapping: Record<string, { documentId: number; ticketId: string }> = {};
                      try {
                        for (const item of pendingUploads) {
                          const uploaded = await uploadTicketAttachment(
                            ticketId,
                            item.file,
                            newIdempotencyKey(),
                          );
                          // Keep focused-editor preview: alias pending→document without revoking blob.
                          attachmentPreview.transferPendingSeed(
                            item.pendingId,
                            uploaded.document_id,
                          );
                          mapping[item.pendingId] = {
                            documentId: uploaded.document_id,
                            ticketId,
                          };
                          pendingFilesRef.current.delete(item.pendingId);
                        }
                        persistReplyPendingFiles();
                        if (Object.keys(mapping).length > 0) {
                          setContent((current) =>
                            attachmentPreview.persistHtml(
                              rewritePendingInlineImages(current, mapping),
                            ),
                          );
                        }
                        load();
                      } catch (error) {
                        setErrorText(messageFor(error).text);
                      }
                    })();
                  } else if (files.length > 0) {
                    load();
                  }
                  return results;
                }}
                onUploadError={(error) => setErrorText(messageFor(error).text)}
              />
              <HelpdeskFormActions align="end">
                <HintAction hint={helpTooltips.detailUi.send} ariaLabel="Ajuda: Enviar resposta">
                  <ActionButton
                    variant="primary"
                    type="submit"
                    aria-label={saving ? "Enviando" : "Enviar resposta"}
                    disabled={saving || !hasVisibleRichText(content)}
                  >
                    <Send size={18} aria-hidden />
                    {saving ? "Enviando…" : "Enviar"}
                  </ActionButton>
                </HintAction>
              </HelpdeskFormActions>
            </form>
            ) : null}
          </>
        ) : null}
      </HelpdeskSectionCard>
    </HelpdeskPageStack>
  );
}
