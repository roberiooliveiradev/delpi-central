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
  acceptTicketSolution,
  acceptTicketValidation,
  beginGlpiLink,
  createFollowup,
  createTicket,
  fetchTicketAttachmentBlob,
  getSessionCapabilities,
  getTicket,
  listCategories,
  listTickets,
  listUrgencies,
  listUsers,
  rejectTicketSolution,
  rejectTicketValidation,
  setTicketAssignee,
  submitTicketSatisfaction,
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
  assigneeFromCreateDraft,
  clearCreateDraft,
  clearReplyDraft,
  readCreateDraft,
  readReplyDraft,
  writeCreateDraft,
  writeReplyDraft,
} from "../presentation/ticketDraftStorage";
import {
  HELPDESK_CREATE_DRAFT_SCOPE,
  canRewritePendingDraftHtml,
  clearHelpdeskDraftPendingFiles,
  pendingFilesMapToDraftRows,
  readHelpdeskDraftPendingFiles,
  rekeyDraftFileToDocument,
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
  HelpdeskAssigneePicker,
  type HelpdeskAssigneeValue,
} from "../components/HelpdeskAssigneePicker";
import {
  HELPDESK_TICKET_LIST_VIEW_LAYOUT_KEY,
  HelpdeskEmptyState,
  HelpdeskFormActions,
  HelpdeskIconButton,
  HelpdeskAttachButton,
  HelpdeskListPaginationFooter,
  HelpdeskLoadingCard,
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
import type { HelpdeskRichTextFieldHandle } from "../ui/helpdeskUi";

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
        {view === "loading" ? (
          <HelpdeskLoadingCard
            title="Carregando chamados…"
            description="Buscando seus chamados no helpdesk."
            variant="panel"
          />
        ) : null}
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
  const [assignee, setAssignee] = useState<HelpdeskAssigneeValue | null>(() =>
    assigneeFromCreateDraft(savedDraft),
  );
  /** null = ainda carregando capabilities — evita flash select→input. */
  const [canAssign, setCanAssign] = useState<boolean | null>(null);
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
  const createComposerRef = useRef<HelpdeskRichTextFieldHandle>(null);

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
    void Promise.allSettled([
      listCategories(controller.signal),
      listUrgencies(controller.signal),
      getSessionCapabilities(controller.signal),
    ])
      .then(([categoryResult, urgencyResult, capsResult]) => {
        if (controller.signal.aborted) return;
        const draft = readCreateDraft();
        if (capsResult.status === "fulfilled") {
          setCanAssign(Boolean(capsResult.value.can_assign));
        } else {
          setCanAssign(false);
        }
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
      assigneeId: assignee?.id ?? "",
      assigneeName: assignee?.name ?? "",
      assigneeEmail: assignee?.email ?? "",
      assigneeDirectoryUserId: assignee?.directoryUserId ?? "",
      assigneeHasPhoto: Boolean(assignee?.hasPhoto),
      categoryId,
      urgencyId,
    });
  }, [title, description, observerIdsInput, assignee, categoryId, urgencyId]);

  /** Rascunho legado (só id) — rehidrata nome/e-mail/foto via GET /users. */
  useEffect(() => {
    const id = (assignee?.id || "").trim();
    if (!id || !/^\d+$/.test(id)) return;
    const stubName = !assignee?.name?.trim() || /^Usuário\s+\d+$/i.test(assignee.name.trim());
    if (!stubName) return;
    const controller = new AbortController();
    void listUsers({ q: id, limit: 5 }, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        const match = (result.items || []).find((row) => String(row.id) === id);
        if (!match) return;
        setAssignee({
          id: String(match.id),
          name: (match.display_name || "").trim() || `Usuário ${match.id}`,
          email: (match.email || "").trim(),
          directoryUserId: (match.directory_user_id || "").trim() || undefined,
          hasPhoto: Boolean(match.has_photo),
        });
      })
      .catch(() => {
        /* soft-fail — mantém snapshot local */
      });
    return () => controller.abort();
  }, [assignee?.id, assignee?.name]);

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
        {loading ? (
          <HelpdeskLoadingCard
            title="Carregando categorias…"
            description="Preparando o formulário de abertura."
            variant="panel"
          />
        ) : null}
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
                assignee_id: canAssign === true && assignee?.id ? Number(assignee.id) : undefined,
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
                ref={createComposerRef}
                label="Descrição"
                hint={helpTooltips.createUi.description}
                value={description}
                onChange={(next) => setDescription(persistHelpdeskAttachmentHtml(next))}
                minHeight={180}
                fill
                enableMentions
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
              <HelpdeskAssigneePicker
                label="Técnico atribuído"
                hint={helpTooltips.createUi.assignee}
                value={assignee}
                onChange={setAssignee}
                emptyLabel="Sem técnico"
                disabled={canAssign !== true || saving || loading}
              />
              <HelpdeskTextField
                label="Observadores"
                hint={helpTooltips.createUi.observers}
                value={observerIdsInput}
                onChange={setObserverIdsInput}
                icon={<Users size={14} aria-hidden />}
              />
              <div className="helpdesk-create-layout__aside-actions">
                <HelpdeskAttachButton
                  hint={helpTooltips.createUi.attach}
                  disabled={saving || loading}
                  className="helpdesk-compose-attach"
                  onClick={() => createComposerRef.current?.openAttachPicker()}
                />
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
  /** False until IDB draft files are read — editor must not paint placeholder before seed (H4). */
  const [draftFilesReady, setDraftFilesReady] = useState(false);
  const [assigneePick, setAssigneePick] = useState<HelpdeskAssigneeValue | null>(null);
  const [assignSaving, setAssignSaving] = useState(false);
  const [assignKey, setAssignKey] = useState(newIdempotencyKey);
  const [cycleNote, setCycleNote] = useState("");
  const [cycleSaving, setCycleSaving] = useState(false);
  const [cycleKey, setCycleKey] = useState(newIdempotencyKey);
  const [satisfactionScore, setSatisfactionScore] = useState(5);
  const [satisfactionComment, setSatisfactionComment] = useState("");
  /** Bumps resolve identity after IDB seed (create parity). */
  const [pendingHydrated, setPendingHydrated] = useState(0);
  const myPhotoUrl = useMyPersonProfilePhoto();
  const pendingFilesRef = useRef<Map<string, File>>(new Map());
  const replyComposerRef = useRef<HelpdeskRichTextFieldHandle>(null);

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

  const persistReplyPendingFiles = useCallback((): Promise<void> => {
    return writeHelpdeskDraftPendingFiles(
      replyDraftPendingScope(ticketId),
      pendingFilesMapToDraftRows(pendingFilesRef.current),
    );
  }, [ticketId]);

  useEffect(() => {
    let cancelled = false;
    setDraftFilesReady(false);
    void readHelpdeskDraftPendingFiles(replyDraftPendingScope(ticketId)).then((rows) => {
      if (cancelled) return;
      for (const row of rows) {
        pendingFilesRef.current.set(row.id, row.file);
        // Keys are pending uuid and/or document id after upload rekey.
        attachmentPreview.seedFile(row.id, row.file);
      }
      if (rows.length > 0) setPendingHydrated((n) => n + 1);
      setDraftFilesReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, [ticketId, attachmentPreview.seedFile]);

  // Create parity: File map is source of truth after F5; srcs may be pruned/raced.
  const resolveReplyAttachmentImageSrc = useCallback(
    (attachmentId: string) => {
      const fromHook = attachmentPreview.resolveAttachmentImageSrc(attachmentId);
      if (fromHook) return fromHook;
      const file = pendingFilesRef.current.get(String(attachmentId || "").trim());
      if (!file) return null;
      return attachmentPreview.seedFile(attachmentId, file);
    },
    // pendingHydrated forces RichTextEditor to re-apply after IDB restore
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [attachmentPreview.resolveAttachmentImageSrc, attachmentPreview.seedFile, pendingHydrated],
  );

  useEffect(() => {
    writeReplyDraft(ticketId, attachmentPreview.persistHtml(content));
  }, [ticketId, content, attachmentPreview.persistHtml]);

  function load() {
    setLoading(true);
    setErrorText(null);
    void getTicket(ticketId)
      .then((next) => {
        setTicket(next);
        setAssigneePick(
          next.assigned_user_id
            ? {
                id: String(next.assigned_user_id),
                name: (next.assigned_display_name || "").trim() || `Usuário ${next.assigned_user_id}`,
                email: "",
              }
            : null,
        );
      })
      .catch((error) => setErrorText(messageFor(error).text))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, [ticketId]);

  function assignTechnician() {
    if (!ticket?.can_assign || !assigneePick?.id || assignSaving) return;
    const userId = Number(assigneePick.id);
    if (!Number.isFinite(userId) || userId <= 0) return;
    setAssignSaving(true);
    setErrorText(null);
    void setTicketAssignee(ticketId, userId, assignKey)
      .then((result) => {
        setTicket((current) =>
          current
            ? {
                ...current,
                assigned_user_id: result.user_id,
                assigned_display_name: result.assigned_display_name,
              }
            : current,
        );
        setAssigneePick({
          id: String(result.user_id),
          name: result.assigned_display_name || assigneePick.name,
          email: assigneePick.email,
        });
        setAssignKey(newIdempotencyKey());
      })
      .catch((error) => setErrorText(messageFor(error).text))
      .finally(() => setAssignSaving(false));
  }

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
        {loading ? (
          <HelpdeskLoadingCard
            title="Carregando chamado…"
            description="Buscando conversa, anexos e status."
            variant="panel"
          />
        ) : null}
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
            {ticket.can_assign ? (
              <div className="helpdesk-assign-panel" aria-label="Atribuir técnico">
                <HelpdeskAssigneePicker
                  label={ticket.assigned_user_id ? "Reatribuir técnico" : "Atribuir técnico"}
                  hint={helpTooltips.detailUi.assignee}
                  value={assigneePick}
                  onChange={setAssigneePick}
                />
                <HintAction
                  hint={helpTooltips.detailUi.assigneeAction}
                  ariaLabel="Ajuda: Confirmar atribuição"
                >
                  <ActionButton
                    variant="default"
                    type="button"
                    disabled={
                      assignSaving ||
                      !assigneePick?.id ||
                      Number(assigneePick.id) === Number(ticket.assigned_user_id || 0)
                    }
                    onClick={assignTechnician}
                  >
                    {assignSaving
                      ? "Salvando…"
                      : ticket.assigned_user_id
                        ? "Reatribuir"
                        : "Atribuir"}
                  </ActionButton>
                </HintAction>
              </div>
            ) : null}
            {(() => {
              const cue = solicitanteLifecycleCue({
                statusId: ticket.status_id,
                hasSolution: timelineHasSolution(ticket.timeline),
                canAcceptSolution: ticket.can_accept_solution,
                canRejectSolution: ticket.can_reject_solution,
                canSubmitSatisfaction: ticket.can_submit_satisfaction,
                canDecideValidation: ticket.can_decide_validation,
                satisfaction: ticket.satisfaction,
              });
              if (!cue) return null;
              const pendingValidations = (ticket.validations ?? []).filter((item) => item.mine_to_decide);
              const runCycle = (action: "accept" | "reject") => {
                setCycleSaving(true);
                setErrorText(null);
                const runner =
                  action === "accept"
                    ? acceptTicketSolution(ticketId, cycleNote, cycleKey)
                    : rejectTicketSolution(ticketId, cycleNote, cycleKey);
                void runner
                  .then(() => {
                    setCycleNote("");
                    setCycleKey(newIdempotencyKey());
                    load();
                  })
                  .catch((error) => setErrorText(messageFor(error).text))
                  .finally(() => setCycleSaving(false));
              };
              const runSatisfaction = () => {
                setCycleSaving(true);
                setErrorText(null);
                void submitTicketSatisfaction(
                  ticketId,
                  { satisfaction: satisfactionScore, comment: satisfactionComment },
                  cycleKey,
                )
                  .then(() => {
                    setSatisfactionComment("");
                    setCycleKey(newIdempotencyKey());
                    load();
                  })
                  .catch((error) => setErrorText(messageFor(error).text))
                  .finally(() => setCycleSaving(false));
              };
              const runValidation = (validationId: number, action: "accept" | "reject") => {
                setCycleSaving(true);
                setErrorText(null);
                const runner =
                  action === "accept"
                    ? acceptTicketValidation(ticketId, validationId, cycleNote, cycleKey)
                    : rejectTicketValidation(ticketId, validationId, cycleNote, cycleKey);
                void runner
                  .then(() => {
                    setCycleNote("");
                    setCycleKey(newIdempotencyKey());
                    load();
                  })
                  .catch((error) => setErrorText(messageFor(error).text))
                  .finally(() => setCycleSaving(false));
              };
              return (
                <div className="helpdesk-lifecycle-cue">
                  <HelpdeskStateBanner variant={cue.variant}>
                    <div className="helpdesk-lifecycle-cue__row">
                      <p className="helpdesk-lifecycle-cue__text">{cue.message}</p>
                      {cue.ctaLabel ? (
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
                      ) : null}
                    </div>
                    {cue.showNativeActions ? (
                      <div className="helpdesk-lifecycle-actions">
                        <label className="helpdesk-lifecycle-note">
                          <span>Comentário (opcional)</span>
                          <input
                            type="text"
                            value={cycleNote}
                            onChange={(event) => setCycleNote(event.target.value)}
                            disabled={cycleSaving}
                            maxLength={2000}
                          />
                        </label>
                        <div className="helpdesk-lifecycle-actions__buttons">
                          {ticket.can_accept_solution ? (
                            <HintAction
                              hint={helpTooltips.detailUi.acceptSolution}
                              ariaLabel="Ajuda: Aceitar solução"
                            >
                              <ActionButton
                                variant="primary"
                                type="button"
                                disabled={cycleSaving}
                                onClick={() => runCycle("accept")}
                              >
                                {cycleSaving ? "Salvando…" : "Aceitar solução"}
                              </ActionButton>
                            </HintAction>
                          ) : null}
                          {ticket.can_reject_solution ? (
                            <HintAction
                              hint={helpTooltips.detailUi.rejectSolution}
                              ariaLabel="Ajuda: Recusar solução"
                            >
                              <ActionButton
                                variant="default"
                                type="button"
                                disabled={cycleSaving}
                                onClick={() => runCycle("reject")}
                              >
                                Recusar / reabrir
                              </ActionButton>
                            </HintAction>
                          ) : null}
                        </div>
                      </div>
                    ) : null}
                    {cue.showValidationActions ? (
                      <div className="helpdesk-lifecycle-actions">
                        {pendingValidations.map((item) => (
                          <div key={item.id} className="helpdesk-lifecycle-validation">
                            {item.submission_comment ? (
                              <p className="helpdesk-lifecycle-cue__text">{item.submission_comment}</p>
                            ) : null}
                            <label className="helpdesk-lifecycle-note">
                              <span>Comentário (opcional)</span>
                              <input
                                type="text"
                                value={cycleNote}
                                onChange={(event) => setCycleNote(event.target.value)}
                                disabled={cycleSaving}
                                maxLength={2000}
                              />
                            </label>
                            <div className="helpdesk-lifecycle-actions__buttons">
                              <HintAction
                                hint={helpTooltips.detailUi.acceptValidation}
                                ariaLabel="Ajuda: Aceitar aprovação"
                              >
                                <ActionButton
                                  variant="primary"
                                  type="button"
                                  disabled={cycleSaving}
                                  onClick={() => runValidation(item.id, "accept")}
                                >
                                  {cycleSaving ? "Salvando…" : "Aceitar aprovação"}
                                </ActionButton>
                              </HintAction>
                              <HintAction
                                hint={helpTooltips.detailUi.rejectValidation}
                                ariaLabel="Ajuda: Recusar aprovação"
                              >
                                <ActionButton
                                  variant="default"
                                  type="button"
                                  disabled={cycleSaving}
                                  onClick={() => runValidation(item.id, "reject")}
                                >
                                  Recusar aprovação
                                </ActionButton>
                              </HintAction>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {cue.showSatisfactionForm ? (
                      <div className="helpdesk-lifecycle-actions">
                        <label className="helpdesk-lifecycle-note">
                          <span>Nota (1–5)</span>
                          <select
                            value={satisfactionScore}
                            onChange={(event) => setSatisfactionScore(Number(event.target.value))}
                            disabled={cycleSaving}
                          >
                            {[1, 2, 3, 4, 5].map((score) => (
                              <option key={score} value={score}>
                                {score}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="helpdesk-lifecycle-note">
                          <span>Comentário (opcional)</span>
                          <input
                            type="text"
                            value={satisfactionComment}
                            onChange={(event) => setSatisfactionComment(event.target.value)}
                            disabled={cycleSaving}
                            maxLength={2000}
                          />
                        </label>
                        <HintAction
                          hint={helpTooltips.detailUi.submitSatisfaction}
                          ariaLabel="Ajuda: Enviar avaliação"
                        >
                          <ActionButton
                            variant="primary"
                            type="button"
                            disabled={cycleSaving}
                            onClick={runSatisfaction}
                          >
                            {cycleSaving ? "Enviando…" : "Enviar avaliação"}
                          </ActionButton>
                        </HintAction>
                      </div>
                    ) : null}
                  </HelpdeskStateBanner>
                </div>
              );
            })()}
            <HelpdeskMessageThread
              listAriaLabel="Conversa do chamado"
              emptyLabel="Nenhuma mensagem"
              resolveAttachmentImageSrc={resolveReplyAttachmentImageSrc}
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
            {ticket.can_followup !== false && draftFilesReady ? (
            <form
              className="helpdesk-reply-form"
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
                ref={replyComposerRef}
                label="Responder"
                hint={helpTooltips.detailUi.reply}
                value={content}
                onChange={(next) => setContent(attachmentPreview.persistHtml(next))}
                minHeight={120}
                fill
                enableMentions
                resolveAttachmentImageSrc={resolveReplyAttachmentImageSrc}
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
                  void persistReplyPendingFiles();
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
                          // Keep File under document id + pending for F5 dual cover.
                          rekeyDraftFileToDocument(
                            pendingFilesRef.current,
                            item.pendingId,
                            uploaded.document_id,
                          );
                        }
                        // Await serialized IDB write so rekey wins over the paste write (H1).
                        await persistReplyPendingFiles();
                        if (Object.keys(mapping).length > 0) {
                          const scope = replyDraftPendingScope(ticketId);
                          const rows = await readHelpdeskDraftPendingFiles(scope);
                          setContent((current) => {
                            const rewritten = attachmentPreview.persistHtml(
                              rewritePendingInlineImages(current, mapping),
                            );
                            // H3 gate: never leave HTML on documentId if IDB cannot seed it.
                            if (!canRewritePendingDraftHtml(rewritten, rows)) {
                              return current;
                            }
                            return rewritten;
                          });
                        }
                        // Do not load() here: compose-time image upload must keep the
                        // local blob seed. Reloading the ticket while the Document is
                        // not yet in attachments retriggers GET→404 storms.
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
                <HelpdeskAttachButton
                  hint={helpTooltips.detailUi.attach}
                  disabled={saving}
                  className="helpdesk-compose-attach"
                  onClick={() => replyComposerRef.current?.openAttachPicker()}
                />
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
