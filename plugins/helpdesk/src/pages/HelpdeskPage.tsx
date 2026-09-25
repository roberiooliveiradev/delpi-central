import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import {
  ActionButton,
  FilePreviewModal,
  HintAction,
  SectionHintLabel,
  TableColumnVisibilityMenu,
} from "@delpi/plugin-ui/index";
import { AlignLeft, ChevronLeft, ExternalLink, FilterX, FolderTree, Gauge, Plus, RefreshCw, Send, TicketPlus, Type, Users } from "lucide-react";

import {
  HelpdeskApiError,
  acceptTicketSolution,
  acceptTicketValidation,
  beginGlpiLink,
  createFollowup,
  createTicket,
  createTicketSolution,
  createTicketTask,
  fetchTicketAttachmentBlob,
  getSessionCapabilities,
  getTicket,
  listCategories,
  listTickets,
  listUrgencies,
  listUsers,
  rejectTicketSolution,
  rejectTicketValidation,
  requestTicketApproval,
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
  TICKET_STATUS_FILTERS,
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
import { shouldForceTicketCards } from "../presentation/listViewport";
import { glpiTicketFormUrl } from "../presentation/glpiPublicLinks";
import {
  clearGlpiAutoLinkAttempt,
  markGlpiAutoLinkAttempted,
  shouldAutoStartGlpiLink,
} from "../presentation/glpiAutoLink";
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
import { TicketActionCard } from "./TicketActionCard";
import { TicketActionMenu } from "./TicketActionMenu";
import {
  EMPTY_TICKET_TASK_FORM,
  TicketTaskActionFields,
  ticketTaskFormToBody,
} from "./TicketTaskActionFields";
import {
  EMPTY_TICKET_REPLY_META,
  TicketReplyActionFields,
  type TicketReplyMetaState,
} from "./TicketReplyActionFields";
import {
  EMPTY_TICKET_SOLUTION_FORM,
  TicketSolutionActionFields,
  ticketSolutionFormToBody,
} from "./TicketSolutionActionFields";
import { TicketApprovalActionFields } from "./TicketApprovalActionFields";
import { TicketContextPanel } from "./TicketContextPanel";
import { TicketListCards } from "./TicketListCards";
import { ticketActionPresentation } from "../presentation/ticketActionPresentation";
import {
  defaultTicketWorkspaceAction,
  ticketWorkspaceActions,
  ticketWorkspaceActionById,
  ticketWorkspaceSelectorActions,
  TICKET_WORKSPACE_SURFACES,
  type TicketWorkspaceActionId,
  type TicketWorkspaceSurfaceId,
} from "../presentation/ticketWorkspaceActions";
import {
  conversationMessageVisible,
  DEFAULT_TIMELINE_VISIBILITY,
  ticketTasksFromTimeline,
  type TimelineVisibilityState,
} from "../presentation/timelineVisibility";
import { TicketListFilterPopover } from "./TicketListFilterPopover";
import { TicketListSortPopover } from "./TicketListSortPopover";
import { TicketListTable } from "./TicketListTable";
import { TicketListToolbar } from "./TicketListToolbar";
import { TicketTaskListPopover, TicketTimelineFilterPopover } from "./TicketTimelineTools";
import {
  HelpdeskAssigneePicker,
  type HelpdeskAssigneeValue,
} from "../components/HelpdeskAssigneePicker";
import {
  HELPDESK_TICKET_LIST_VIEW_LAYOUT_KEY,
  HelpdeskEmptyState,
  HelpdeskFilterInput,
  HelpdeskFormActions,
  HelpdeskIconButton,
  HelpdeskAttachButton,
  HelpdeskListPaginationFooter,
  HelpdeskLoadingCard,
  HelpdeskMessageThread,
  HelpdeskPageHeader,
  HelpdeskPageHero,
  HelpdeskRichTextField,
  HelpdeskScopeChipBar,
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
  const [assignees, setAssignees] = useState<{ id: number; name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [linking, setLinking] = useState(false);
  const autoLinkStartedRef = useRef(false);
  const [searchDraft, setSearchDraft] = useState(() => currentListFilters().q);
  const [canAssign, setCanAssign] = useState<boolean | null>(null);
  const [viewportWidth, setViewportWidth] = useState(() =>
    typeof window === "undefined" ? 1280 : window.innerWidth,
  );
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
  } = useHelpdeskTicketListColumns({ canAssign: canAssign === true });
  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: HELPDESK_TICKET_LIST_VIEW_LAYOUT_KEY,
    defaultMode: "table",
  });
  const forceCards = shouldForceTicketCards(viewportWidth);
  const showCards = forceCards || layout === "cards";

  useEffect(() => {
    rememberHelpdeskListPath(`/apps/helpdesk${ticketListSearch(filters)}`);
  }, [filters]);

  useEffect(() => {
    setSearchDraft(filters.q);
  }, [filters.q]);

  useEffect(() => {
    const onResize = () => setViewportWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);


  useEffect(() => {
    const controller = new AbortController();
    void getSessionCapabilities(controller.signal)
      .then((caps) => setCanAssign(Boolean(caps.can_assign)))
      .catch(() => setCanAssign(false));
    return () => controller.abort();
  }, []);

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
      assignee_id: "",
      updated_from: "",
      updated_to: "",
      created_from: "",
      created_to: "",
      page: 1,
      sort: filters.sort,
      page_size: filters.page_size,
    });
  }

  function applySearch() {
    const q = searchDraft.trim();
    commitFilters({ ...filters, q, page: 1 });
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
        assignee_id: next.assignee_id || undefined,
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
      clearGlpiAutoLinkAttempt();
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

  function startGlpiAuthorization() {
    setLinking(true);
    markGlpiAutoLinkAttempted();
    void beginGlpiLink()
      .then((url) => {
        window.location.assign(url);
      })
      .catch((error) => {
        clearGlpiAutoLinkAttempt();
        setErrorText(messageFor(error).text);
        setLinking(false);
      });
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
    if (canAssign !== true) {
      setAssignees([]);
      return;
    }
    const controller = new AbortController();
    void listUsers({ q: "", limit: 50, purpose: "assignee" }, controller.signal)
      .then((body) => {
        setAssignees(
          (body.items || []).map((user) => ({
            id: Number(user.id),
            name: (user.display_name || "").trim() || `Usuário ${user.id}`,
          })),
        );
      })
      .catch(() => setAssignees([]));
    return () => controller.abort();
  }, [canAssign]);

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

  useEffect(() => {
    if (view !== "link") return;
    if (autoLinkStartedRef.current) return;
    if (!shouldAutoStartGlpiLink()) return;
    autoLinkStartedRef.current = true;
    startGlpiAuthorization();
  }, [view]);

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

  const statusChips = TICKET_STATUS_FILTERS.map((item) => ({
    id: item.value || "all",
    label: item.label,
    active: filters.status === item.value,
    onSelect: () => commitFilters({ ...filters, status: item.value, page: 1 }),
  }));

  const listChrome = view !== "link" && view !== "forbidden";

  return (
    <HelpdeskPageStack>
      <HelpdeskPageHero
        aria-label="Meus Chamados de TI"
        title={
          <SectionHintLabel label="Meus Chamados de TI" hint={helpTooltips.list} />
        }
        description="Acompanhe suas solicitações e atendimentos de TI."
        actions={
          <div className="helpdesk-list-hero-actions">
            <HintAction hint={helpTooltips.listUi.refreshPage} ariaLabel="Ajuda: Atualizar">
              <ActionButton
                variant="ghost"
                type="button"
                aria-label="Atualizar"
                disabled={loading}
                onClick={() => void load(filters)}
              >
                <RefreshCw size={16} aria-hidden />
                Atualizar
              </ActionButton>
            </HintAction>
            <HintAction hint={helpTooltips.listUi.openTicket} ariaLabel="Ajuda: Abrir chamado">
              <ActionButton
                variant="primary"
                type="button"
                className="helpdesk-open-ticket"
                aria-label="Abrir chamado"
                onClick={() => navigateHelpdesk("/apps/helpdesk/tickets/new")}
              >
                <Plus size={16} aria-hidden />
                Abrir chamado
              </ActionButton>
            </HintAction>
          </div>
        }
      />

      <div className="helpdesk-list-shell">
        {listChrome ? (
          <div className="helpdesk-list-controls">
            <form
              className="helpdesk-list-primary-bar"
              aria-label="Busca e ações da lista"
              onSubmit={(event: FormEvent<HTMLFormElement>) => {
                event.preventDefault();
                applySearch();
              }}
            >
              <HintAction hint={helpTooltips.listUi.search} ariaLabel="Ajuda: Buscar">
                <HelpdeskFilterInput
                  label="Buscar"
                  type="search"
                  value={searchDraft}
                  placeholder="Buscar por número, título ou conteúdo…"
                  onChange={(value) => setSearchDraft(value)}
                />
              </HintAction>
              <div className="helpdesk-list-primary-bar__actions">
                {filterActive ? (
                  <HintAction hint={helpTooltips.listUi.clearFilters} ariaLabel="Ajuda: Limpar filtros">
                    <HelpdeskIconButton aria-label="Limpar filtros" onClick={clearListFilters}>
                      <FilterX size={16} aria-hidden />
                    </HelpdeskIconButton>
                  </HintAction>
                ) : null}
                <HintAction
                  hint={helpTooltips.listUi.filterBuilderToggle}
                  ariaLabel="Ajuda: Filtros avançados"
                >
                  <TicketListFilterPopover
                    group={builderGroup}
                    onChange={setBuilderGroup}
                    urgencies={urgencies}
                    categories={categories}
                    assignees={assignees}
                    onClear={() => setBuilderGroup(emptyFilterGroup())}
                    onApply={() => {
                      const next = ticketListFiltersFromFilterGroup(builderGroup, filters);
                      commitFilters(next);
                    }}
                  />
                </HintAction>
                <HintAction hint={helpTooltips.listUi.sortBuilderToggle} ariaLabel="Ajuda: Ordenação">
                  <TicketListSortPopover
                    levels={sortDraft}
                    onChange={setSortDraft}
                    summaryLabel={listViewModel.primarySortLabel}
                    onApply={() => {
                      commitFilters({
                        ...filters,
                        sort: formatTicketSortLevels(sortDraft),
                        page: 1,
                      });
                    }}
                  />
                </HintAction>
                {showCards ? null : (
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
                )}
                <HintAction hint={helpTooltips.listUi.refreshList} ariaLabel="Ajuda: Atualizar lista">
                  <HelpdeskIconButton aria-label="Atualizar lista" onClick={() => void load(filters)}>
                    <RefreshCw size={16} aria-hidden />
                  </HelpdeskIconButton>
                </HintAction>
              </div>
            </form>

            <div className="helpdesk-list-secondary-bar">
              <HintAction hint={helpTooltips.listUi.statusChips} ariaLabel="Ajuda: Status">
                <HelpdeskScopeChipBar aria-label="Filtro rápido de status" chips={statusChips} />
              </HintAction>
              <TicketListToolbar
                viewModel={listViewModel}
                leading={
                  forceCards ? null : (
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
                  )
                }
              />
            </div>
          </div>
        ) : null}

        {view === "loading" ? (
          <HelpdeskLoadingCard
            title="Carregando chamados…"
            description="Buscando seus chamados no helpdesk."
            variant="panel"
          />
        ) : null}
        {view === "forbidden" || view === "unavailable" || view === "error" ? (
          <HelpdeskStateBanner variant="error">
            {errorText}
            {view === "error" || view === "unavailable" ? (
              <HelpdeskFormActions>
                <ActionButton variant="primary" type="button" onClick={() => void load(filters)}>
                  Tentar novamente
                </ActionButton>
              </HelpdeskFormActions>
            ) : null}
          </HelpdeskStateBanner>
        ) : null}
        {view === "link" ? (
          <HelpdeskStateBanner>
            {linking ? "Abrindo autorização do helpdesk…" : helpTooltips.link}
            <HelpdeskFormActions>
              <ActionButton
                variant="primary"
                disabled={linking}
                onClick={() => {
                  autoLinkStartedRef.current = true;
                  startGlpiAuthorization();
                }}
              >
                {linking ? "Abrindo…" : "Autorizar no helpdesk"}
              </ActionButton>
            </HelpdeskFormActions>
          </HelpdeskStateBanner>
        ) : null}
        {view === "empty" ? (
          <HelpdeskEmptyState
            message={
              filterActive
                ? "Nenhum chamado corresponde aos filtros atuais."
                : "Você ainda não possui chamados."
            }
          />
        ) : null}
        {view === "list" ? (
          showCards ? (
            <TicketListCards
              items={items}
              showRequester={canAssign === true}
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
      </div>
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
    void listUsers({ q: id, limit: 5, purpose: "assignee" }, controller.signal)
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
                      { content: imageBlocks.join("") },
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
                minHeight={120}
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
  const [satisfactionCommentOpen, setSatisfactionCommentOpen] = useState(false);
  const [workspaceSurface, setWorkspaceSurface] = useState<TicketWorkspaceSurfaceId>("conversation");
  const [activeAction, setActiveAction] = useState<TicketWorkspaceActionId | null>(null);
  const [timelineVisibility, setTimelineVisibility] =
    useState<TimelineVisibilityState>(DEFAULT_TIMELINE_VISIBILITY);
  const [documentFiles, setDocumentFiles] = useState<File[]>([]);
  const documentInputRef = useRef<HTMLInputElement>(null);
  const [solutionForm, setSolutionForm] = useState(EMPTY_TICKET_SOLUTION_FORM);
  const [replyMeta, setReplyMeta] = useState<TicketReplyMetaState>(EMPTY_TICKET_REPLY_META);
  const [taskForm, setTaskForm] = useState(EMPTY_TICKET_TASK_FORM);
  const [approvalContent, setApprovalContent] = useState("");
  const [approvalTemplateId, setApprovalTemplateId] = useState<number | null>(null);
  const [approvalApproverType, setApprovalApproverType] = useState<"user" | "group">("user");
  const [approvalGroupId, setApprovalGroupId] = useState<number | null>(null);
  const [approverPick, setApproverPick] = useState<HelpdeskAssigneeValue | null>(null);
  const [documentTitle, setDocumentTitle] = useState("");
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

  useEffect(() => {
    if (!ticket) return;
    const actions = ticketWorkspaceActions(ticket);
    setActiveAction((current) => {
      if (current && actions.some((item) => item.id === current)) return current;
      return defaultTicketWorkspaceAction(actions);
    });
  }, [
    ticket?.id,
    ticket?.can_followup,
    ticket?.can_create_solution,
    ticket?.can_create_task,
    ticket?.can_request_approval,
    ticket?.can_accept_solution,
    ticket?.can_reject_solution,
  ]);

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

  function runCycle(action: "accept" | "reject") {
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
        closeActionAfterSuccess();
        load();
      })
      .catch((error) => setErrorText(messageFor(error).text))
      .finally(() => setCycleSaving(false));
  }

  function isActiveActionDirty(): boolean {
    if (!activeAction) return false;
    if (activeAction === "reply") return hasVisibleRichText(content);
    if (activeAction === "create_solution") return hasVisibleRichText(solutionForm.content);
    if (activeAction === "create_task") return hasVisibleRichText(taskForm.content);
    if (activeAction === "request_approval") {
      return (
        hasVisibleRichText(approvalContent) ||
        Boolean(approverPick) ||
        approvalGroupId != null ||
        approvalApproverType !== "user"
      );
    }
    if (activeAction === "attach_file") {
      return documentFiles.length > 0 || Boolean(documentTitle.trim());
    }
    if (activeAction === "accept_solution" || activeAction === "reject_solution") {
      return hasVisibleRichText(cycleNote);
    }
    return false;
  }

  function confirmDiscardDraft(message: string): boolean {
    if (!isActiveActionDirty()) return true;
    if (typeof window === "undefined") return true;
    return window.confirm(message);
  }

  function selectWorkspaceAction(next: TicketWorkspaceActionId) {
    if (next === activeAction) return;
    if (!confirmDiscardDraft("Há conteúdo em edição. Descartar o rascunho e trocar de ação?")) {
      return;
    }
    setActiveAction(next);
  }

  function cancelActiveActionForm() {
    if (!confirmDiscardDraft("Há conteúdo em edição. Descartar e fechar esta ação?")) {
      return;
    }
    if (activeAction === "reply") {
      /* keep sessionStorage reply draft — only close the card */
    }
    if (activeAction === "create_solution") setSolutionForm(EMPTY_TICKET_SOLUTION_FORM);
    if (activeAction === "create_task") setTaskForm(EMPTY_TICKET_TASK_FORM);
    if (activeAction === "reply") setReplyMeta(EMPTY_TICKET_REPLY_META);
    if (activeAction === "request_approval") {
      setApprovalContent("");
      setApprovalTemplateId(null);
      setApprovalApproverType("user");
      setApprovalGroupId(null);
      setApproverPick(null);
    }
    if (activeAction === "attach_file") {
      setDocumentFiles([]);
      setDocumentTitle("");
    }
    if (activeAction === "accept_solution" || activeAction === "reject_solution") {
      setCycleNote("");
    }
    setActiveAction(null);
  }

  function closeActionAfterSuccess() {
    setActiveAction(null);
  }

  const workspaceActions = ticket ? ticketWorkspaceActions(ticket) : [];
  const selectorActions = ticketWorkspaceSelectorActions(workspaceActions);
  const activeWorkspaceAction = ticketWorkspaceActionById(workspaceActions, activeAction);
  const visibleMessages = ticket
    ? conversationMessages(ticket, new Date()).filter((message) =>
        conversationMessageVisible(message.kind, timelineVisibility),
      )
    : [];
  const ticketTasks = ticket ? ticketTasksFromTimeline(ticket.timeline) : [];

  return (
    <HelpdeskPageStack>
      <HelpdeskPageHeader
        title={ticket?.title || "Chamado"}
        compact
        nav={<HelpdeskBackButton hint={helpTooltips.detailUi.back} />}
        onRefresh={load}
        refreshing={loading}
      />
      <div className="helpdesk-detail helpdesk-ticket-workspace">
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
            <section className="helpdesk-detail__summary" aria-label="Resumo do chamado">
              <div className="helpdesk-ticket-summary-rail">
                <div className="helpdesk-ticket-summary-rail__items">
                  <span className="helpdesk-ticket-summary-rail__lead">
                    {[
                      ticket.id > 0 ? `#${ticket.id}` : "",
                      ticket.category.trim(),
                      ticket.urgency.trim(),
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                  <HelpdeskStatusBadge
                    label={ticket.status}
                    variant={statusBadgeVariant(ticket.status_id)}
                  />
                  <span className="helpdesk-ticket-summary-rail__item">
                    <span className="helpdesk-ticket-summary-rail__label">Técnico</span>
                    <span className="helpdesk-ticket-summary-rail__value">
                      {(ticket.assigned_display_name || "").trim() || "Sem técnico"}
                    </span>
                  </span>
                  {ticketRecordFields({
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
                      ["sla_tto", "sla_ttr", "created_at", "updated_at"].includes(field.id),
                    )
                    .filter((field) => field.present)
                    .map((field) => (
                      <span key={field.id} className="helpdesk-ticket-summary-rail__item">
                        <span className="helpdesk-ticket-summary-rail__label">{field.label}</span>
                        <span className="helpdesk-ticket-summary-rail__value">{field.value}</span>
                      </span>
                    ))}
                </div>
              </div>
            </section>
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
                    setSatisfactionCommentOpen(false);
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
              const showSatisfactionComment =
                satisfactionCommentOpen || satisfactionComment.trim().length > 0;
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
                        <p className="helpdesk-lifecycle-cue__hint">
                          Aceite ou recuse a solução abaixo, ou use o seletor de ação.
                        </p>
                        {ticket.can_accept_solution ? (
                          <ActionButton
                            variant="primary"
                            type="button"
                            disabled={cycleSaving}
                            onClick={() => selectWorkspaceAction("accept_solution")}
                          >
                            Aceitar solução
                          </ActionButton>
                        ) : null}
                        {ticket.can_reject_solution ? (
                          <ActionButton
                            type="button"
                            disabled={cycleSaving}
                            onClick={() => selectWorkspaceAction("reject_solution")}
                          >
                            Recusar / reabrir
                          </ActionButton>
                        ) : null}
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
                      <div className="helpdesk-satisfaction" role="group" aria-label="Avaliação do atendimento">
                        <div
                          className="helpdesk-satisfaction__scores"
                          role="radiogroup"
                          aria-label="Nota de 1 a 5"
                        >
                          {[1, 2, 3, 4, 5].map((score) => {
                            const selected = satisfactionScore === score;
                            return (
                              <label
                                key={score}
                                className={[
                                  "helpdesk-satisfaction__score",
                                  selected ? "helpdesk-satisfaction__score--selected" : null,
                                ]
                                  .filter(Boolean)
                                  .join(" ")}
                              >
                                <input
                                  type="radio"
                                  name="helpdesk-satisfaction-score"
                                  value={score}
                                  checked={selected}
                                  disabled={cycleSaving}
                                  onChange={() => setSatisfactionScore(score)}
                                />
                                <span aria-hidden="true">{score}</span>
                                <span className="helpdesk-sr-only">Nota {score}</span>
                              </label>
                            );
                          })}
                        </div>
                        <div className="helpdesk-satisfaction__aside">
                          {showSatisfactionComment ? (
                            <label className="helpdesk-lifecycle-note helpdesk-satisfaction__comment">
                              <span>Comentário (opcional)</span>
                              <input
                                type="text"
                                value={satisfactionComment}
                                onChange={(event) => setSatisfactionComment(event.target.value)}
                                disabled={cycleSaving}
                                maxLength={2000}
                              />
                            </label>
                          ) : (
                            <button
                              type="button"
                              className="helpdesk-satisfaction__comment-toggle"
                              disabled={cycleSaving}
                              onClick={() => setSatisfactionCommentOpen(true)}
                            >
                              Adicionar comentário
                            </button>
                          )}
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
                      </div>
                    ) : null}
                  </HelpdeskStateBanner>
                </div>
              );
            })()}
            <div className="helpdesk-ticket-workspace__tabs">
              <HelpdeskSegmentToggle
                ariaLabel="Seção do chamado"
                idPrefix="helpdesk-ticket-workspace-surface"
                size="sm"
                widthMode="fill"
                value={workspaceSurface}
                onChange={(value) => {
                  if (value === "conversation" || value === "details") setWorkspaceSurface(value);
                }}
                options={TICKET_WORKSPACE_SURFACES.map((item) => ({
                  value: item.id,
                  label: item.label,
                }))}
              />
            </div>
            <div className="helpdesk-ticket-workspace__body">
              <nav className="helpdesk-ticket-workspace__nav" aria-label="Navegação do chamado">
                {TICKET_WORKSPACE_SURFACES.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={[
                      "helpdesk-ticket-workspace__nav-item",
                      workspaceSurface === item.id
                        ? "helpdesk-ticket-workspace__nav-item--active"
                        : null,
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    aria-current={workspaceSurface === item.id ? "page" : undefined}
                    onClick={() => setWorkspaceSurface(item.id)}
                  >
                    {item.label}
                  </button>
                ))}
              </nav>
              <div className="helpdesk-ticket-workspace__main">
                {workspaceSurface === "details" ? (
                  <TicketContextPanel
                    ticket={ticket}
                    assigneePick={assigneePick}
                    onAssigneeChange={setAssigneePick}
                    onAssignConfirm={assignTechnician}
                    assignSaving={assignSaving}
                  />
                ) : (
                  <div className="helpdesk-detail__conversation">
                    <div className="helpdesk-detail__conversation-toolbar">
                      <TicketTimelineFilterPopover
                        value={timelineVisibility}
                        onChange={setTimelineVisibility}
                      />
                      <TicketTaskListPopover
                        tasks={ticketTasks.map((task) => ({
                          id: task.id,
                          content: task.content,
                          author: task.author,
                        }))}
                      />
                    </div>
                    <div className="helpdesk-detail__conversation-inner">
                      <HelpdeskMessageThread
                        listAriaLabel="Conversa do chamado"
                        emptyLabel="Ainda não há novas mensagens neste chamado."
                        resolveAttachmentImageSrc={resolveReplyAttachmentImageSrc}
                        onAttachmentImageClick={(attachmentId) => {
                          const documentId = Number(attachmentId);
                          if (!Number.isFinite(documentId)) return;
                          const known = ticket.attachments.find(
                            (item) => item.document_id === documentId,
                          );
                          setInlinePreview(
                            known ?? {
                              document_id: documentId,
                              filename: "imagem",
                              mime: "image/*",
                            },
                          );
                        }}
                        messages={visibleMessages.map((message) => ({
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
                                attachments={ticket.attachments.filter((item) =>
                                  message.attachmentIds.includes(item.document_id),
                                )}
                                onError={(text) => setErrorText(text)}
                              />
                            ) : undefined,
                        }))}
                      />
                      {(timelineVisibility.documents || timelineVisibility.approvals) &&
                      ((timelineVisibility.documents && ticket.attachments.length > 0) ||
                        (timelineVisibility.approvals && (ticket.validations?.length ?? 0) > 0)) ? (
                        <div className="helpdesk-timeline-extras">
                          {timelineVisibility.documents && ticket.attachments.length > 0 ? (
                            <section
                              className="helpdesk-timeline-extras__block"
                              data-action-variant="attachment"
                              aria-label="Documentos do chamado"
                            >
                              <h3 className="helpdesk-timeline-extras__title">Documentos</h3>
                              <TicketAttachmentPreview
                                ticketId={ticketId}
                                attachments={ticket.attachments}
                                onError={(text) => setErrorText(text)}
                              />
                            </section>
                          ) : null}
                          {timelineVisibility.approvals && (ticket.validations?.length ?? 0) > 0 ? (
                            <section
                              className="helpdesk-timeline-extras__block"
                              data-action-variant="approval"
                              aria-label="Aprovações do chamado"
                            >
                              <h3 className="helpdesk-timeline-extras__title">Aprovações</h3>
                              <ul className="helpdesk-timeline-extras__list">
                                {(ticket.validations ?? []).map((item) => (
                                  <li key={item.id}>
                                    #{item.id} · status {item.status}
                                    {item.submission_comment
                                      ? ` — ${item.submission_comment}`
                                      : ""}
                                  </li>
                                ))}
                              </ul>
                            </section>
                          ) : null}
                        </div>
                      ) : null}
                      {selectorActions.length > 0 || workspaceActions.length > 0 ? (
                        <div className="helpdesk-ticket-workspace__composer">
                          <HintAction
                            hint={helpTooltips.detailUi.actionMenu}
                            ariaLabel="Ajuda: Ações do chamado"
                          >
                            <TicketActionMenu
                              actions={
                                selectorActions.length > 0 ? selectorActions : workspaceActions
                              }
                              activeId={activeAction}
                              disabled={saving || cycleSaving}
                              onChange={selectWorkspaceAction}
                              idleLabel="Responder"
                            />
                          </HintAction>
                          {activeAction === "reply" && draftFilesReady ? (
                            <TicketActionCard
                              actionId="reply"
                              disabled={saving}
                              onCancel={cancelActiveActionForm}
                              footer={
                                <HelpdeskFormActions align="end" className="helpdesk-reply-form__actions">
                                  <ActionButton
                                    type="button"
                                    variant="ghost"
                                    disabled={saving}
                                    onClick={cancelActiveActionForm}
                                  >
                                    Cancelar
                                  </ActionButton>
                                  <HelpdeskAttachButton
                                    hint={helpTooltips.detailUi.attach}
                                    disabled={saving}
                                    className="helpdesk-compose-attach"
                                    onClick={() => replyComposerRef.current?.openAttachPicker()}
                                  />
                                  <HintAction
                                    hint={helpTooltips.detailUi.send}
                                    ariaLabel="Ajuda: Enviar resposta"
                                  >
                                    <ActionButton
                                      variant="primary"
                                      type="submit"
                                      form="helpdesk-reply-action-form"
                                      aria-label={
                                        saving
                                          ? ticketActionPresentation("reply").submittingLabel
                                          : ticketActionPresentation("reply").submitLabel
                                      }
                                      disabled={saving || !hasVisibleRichText(content)}
                                    >
                                      <Send size={18} aria-hidden />
                                      {saving
                                        ? ticketActionPresentation("reply").submittingLabel
                                        : ticketActionPresentation("reply").submitLabel}
                                    </ActionButton>
                                  </HintAction>
                                </HelpdeskFormActions>
                              }
                            >
                            <form
                              id="helpdesk-reply-action-form"
                              className="helpdesk-reply-form"
                              onSubmit={(event) => {
                                event.preventDefault();
                                if (saving || !hasVisibleRichText(content)) return;
                                setSaving(true);
                                setErrorText(null);
                                const payload = attachmentPreview.persistHtml(content.trim());
                                void createFollowup(
                                  ticketId,
                                  {
                                    content: payload,
                                    ...(replyMeta.requestTypeId != null
                                      ? { request_type_id: replyMeta.requestTypeId }
                                      : null),
                                  },
                                  idempotencyKey,
                                )
                                  .then(() => {
                                    setContent("");
                                    setReplyMeta(EMPTY_TICKET_REPLY_META);
                                    clearReplyDraft(ticketId);
                                    pendingFilesRef.current.clear();
                                    void clearHelpdeskDraftPendingFiles(
                                      replyDraftPendingScope(ticketId),
                                    );
                                    setIdempotencyKey(newIdempotencyKey());
                                    closeActionAfterSuccess();
                                    load();
                                  })
                                  .catch((error) =>
                                    setErrorText(
                                      messageFor(error).text ||
                                        ticketActionPresentation("reply").errorFallback,
                                    ),
                                  )
                                  .finally(() => setSaving(false));
                              }}
                            >
                              <TicketReplyActionFields
                                value={replyMeta}
                                onChange={setReplyMeta}
                                disabled={saving}
                                onApplyContent={(html) =>
                                  setContent(attachmentPreview.persistHtml(html))
                                }
                              />
                              <HelpdeskRichTextField
                                ref={replyComposerRef}
                                label="Responder"
                                hint={helpTooltips.detailUi.reply}
                                value={content}
                                onChange={(next) =>
                                  setContent(attachmentPreview.persistHtml(next))
                                }
                                minHeight={144}
                                enableMentions
                                resolveAttachmentImageSrc={resolveReplyAttachmentImageSrc}
                                persistAttachmentImageSrc={
                                  attachmentPreview.persistAttachmentImageSrc
                                }
                                onUploadFiles={async (files) => {
                                  const results: HelpdeskInlineUploadResult[] = [];
                                  const pendingUploads: { pendingId: string; file: File }[] = [];
                                  for (const file of files) {
                                    const isImage =
                                      file.type.startsWith("image/") ||
                                      /\.(png|jpe?g|gif|webp|bmp)$/i.test(file.name || "");
                                    if (!isImage) {
                                      await uploadTicketAttachment(
                                        ticketId,
                                        file,
                                        newIdempotencyKey(),
                                      );
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
                                      const mapping: Record<
                                        string,
                                        { documentId: number; ticketId: string }
                                      > = {};
                                      try {
                                        for (const item of pendingUploads) {
                                          const uploaded = await uploadTicketAttachment(
                                            ticketId,
                                            item.file,
                                            newIdempotencyKey(),
                                          );
                                          attachmentPreview.transferPendingSeed(
                                            item.pendingId,
                                            uploaded.document_id,
                                          );
                                          mapping[item.pendingId] = {
                                            documentId: uploaded.document_id,
                                            ticketId,
                                          };
                                          rekeyDraftFileToDocument(
                                            pendingFilesRef.current,
                                            item.pendingId,
                                            uploaded.document_id,
                                          );
                                        }
                                        await persistReplyPendingFiles();
                                        if (Object.keys(mapping).length > 0) {
                                          const scope = replyDraftPendingScope(ticketId);
                                          const rows = await readHelpdeskDraftPendingFiles(scope);
                                          setContent((current) => {
                                            const rewritten = attachmentPreview.persistHtml(
                                              rewritePendingInlineImages(current, mapping),
                                            );
                                            if (!canRewritePendingDraftHtml(rewritten, rows)) {
                                              return current;
                                            }
                                            return rewritten;
                                          });
                                        }
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
                            </form>
                            </TicketActionCard>
                          ) : null}
                          {activeAction === "accept_solution" ||
                          activeAction === "reject_solution" ? (
                            <TicketActionCard
                              actionId={activeAction}
                              disabled={cycleSaving}
                              onCancel={cancelActiveActionForm}
                              footer={
                                <HelpdeskFormActions align="end">
                                  <ActionButton
                                    type="button"
                                    variant="ghost"
                                    disabled={cycleSaving}
                                    onClick={cancelActiveActionForm}
                                  >
                                    Cancelar
                                  </ActionButton>
                                  <ActionButton
                                    variant={
                                      activeAction === "accept_solution" ? "primary" : "default"
                                    }
                                    type="button"
                                    disabled={cycleSaving}
                                    onClick={() =>
                                      runCycle(
                                        activeAction === "accept_solution" ? "accept" : "reject",
                                      )
                                    }
                                  >
                                    {cycleSaving
                                      ? ticketActionPresentation(activeAction).submittingLabel
                                      : ticketActionPresentation(activeAction).submitLabel}
                                  </ActionButton>
                                </HelpdeskFormActions>
                              }
                            >
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
                            </TicketActionCard>
                          ) : null}
                          {activeAction === "create_solution" ? (
                            <TicketActionCard
                              actionId="create_solution"
                              disabled={saving}
                              onCancel={cancelActiveActionForm}
                            >
                            <form
                              className="helpdesk-reply-form helpdesk-action-form--solution"
                              onSubmit={(event) => {
                                event.preventDefault();
                                if (saving || !hasVisibleRichText(solutionForm.content)) return;
                                setSaving(true);
                                setErrorText(null);
                                void createTicketSolution(
                                  ticketId,
                                  ticketSolutionFormToBody({
                                    ...solutionForm,
                                    content: solutionForm.content.trim(),
                                  }),
                                  idempotencyKey,
                                )
                                  .then(() => {
                                    setSolutionForm(EMPTY_TICKET_SOLUTION_FORM);
                                    setIdempotencyKey(newIdempotencyKey());
                                    closeActionAfterSuccess();
                                    load();
                                  })
                                  .catch((error) => setErrorText(messageFor(error).text))
                                  .finally(() => setSaving(false));
                              }}
                            >
                              <div className="helpdesk-action-form__solution-layout">
                                <HelpdeskRichTextField
                                  label="Solução"
                                  hint={helpTooltips.detailUi.createSolution}
                                  value={solutionForm.content}
                                  onChange={(next) =>
                                    setSolutionForm((current) => ({ ...current, content: next }))
                                  }
                                  minHeight={144}
                                  enableMentions
                                />
                                <TicketSolutionActionFields
                                  value={solutionForm}
                                  onChange={setSolutionForm}
                                  disabled={saving}
                                />
                              </div>
                              <HelpdeskFormActions align="end">
                                <ActionButton
                                  type="button"
                                  variant="ghost"
                                  disabled={saving}
                                  onClick={cancelActiveActionForm}
                                >
                                  Cancelar
                                </ActionButton>
                                <ActionButton
                                  variant="primary"
                                  type="submit"
                                  disabled={saving || !hasVisibleRichText(solutionForm.content)}
                                >
                                  {saving
                                    ? ticketActionPresentation("create_solution").submittingLabel
                                    : ticketActionPresentation("create_solution").submitLabel}
                                </ActionButton>
                              </HelpdeskFormActions>
                            </form>
                            </TicketActionCard>
                          ) : null}
                          {activeAction === "create_task" ? (
                            <TicketActionCard
                              actionId="create_task"
                              disabled={saving}
                              onCancel={cancelActiveActionForm}
                            >
                            <form
                              className="helpdesk-reply-form helpdesk-action-form--task"
                              onSubmit={(event) => {
                                event.preventDefault();
                                if (saving || !hasVisibleRichText(taskForm.content)) return;
                                setSaving(true);
                                setErrorText(null);
                                void createTicketTask(
                                  ticketId,
                                  ticketTaskFormToBody({
                                    ...taskForm,
                                    content: taskForm.content.trim(),
                                  }),
                                  idempotencyKey,
                                )
                                  .then(() => {
                                    setTaskForm(EMPTY_TICKET_TASK_FORM);
                                    setIdempotencyKey(newIdempotencyKey());
                                    closeActionAfterSuccess();
                                    load();
                                  })
                                  .catch((error) => setErrorText(messageFor(error).text))
                                  .finally(() => setSaving(false));
                              }}
                            >
                              <div className="helpdesk-action-form__task-layout">
                                <HelpdeskRichTextField
                                  label="Tarefa"
                                  hint={helpTooltips.detailUi.createTask}
                                  value={taskForm.content}
                                  onChange={(next) => setTaskForm((current) => ({ ...current, content: next }))}
                                  minHeight={144}
                                  enableMentions
                                />
                                <TicketTaskActionFields
                                  value={taskForm}
                                  onChange={setTaskForm}
                                  disabled={saving}
                                />
                              </div>
                              <HelpdeskFormActions align="end">
                                <ActionButton
                                  type="button"
                                  variant="ghost"
                                  disabled={saving}
                                  onClick={cancelActiveActionForm}
                                >
                                  Cancelar
                                </ActionButton>
                                <ActionButton
                                  variant="primary"
                                  type="submit"
                                  disabled={saving || !hasVisibleRichText(taskForm.content)}
                                >
                                  {saving
                                    ? ticketActionPresentation("create_task").submittingLabel
                                    : ticketActionPresentation("create_task").submitLabel}
                                </ActionButton>
                              </HelpdeskFormActions>
                            </form>
                            </TicketActionCard>
                          ) : null}
                          {activeAction === "request_approval" ? (
                            <TicketActionCard
                              actionId="request_approval"
                              disabled={saving}
                              onCancel={cancelActiveActionForm}
                            >
                            <form
                              className="helpdesk-reply-form"
                              onSubmit={(event) => {
                                event.preventDefault();
                                const approverId =
                                  approvalApproverType === "group"
                                    ? Number(approvalGroupId || 0)
                                    : Number(approverPick?.id || 0);
                                if (saving || !Number.isFinite(approverId) || approverId <= 0) return;
                                setSaving(true);
                                setErrorText(null);
                                void requestTicketApproval(
                                  ticketId,
                                  {
                                    approver_type: approvalApproverType,
                                    approver_id: approverId,
                                    content: approvalContent.trim(),
                                  },
                                  idempotencyKey,
                                )
                                  .then(() => {
                                    setApprovalContent("");
                                    setApprovalTemplateId(null);
                                    setApprovalApproverType("user");
                                    setApprovalGroupId(null);
                                    setApproverPick(null);
                                    setIdempotencyKey(newIdempotencyKey());
                                    closeActionAfterSuccess();
                                    load();
                                  })
                                  .catch((error) => setErrorText(messageFor(error).text))
                                  .finally(() => setSaving(false));
                              }}
                            >
                              <TicketApprovalActionFields
                                templateId={approvalTemplateId}
                                onTemplateIdChange={setApprovalTemplateId}
                                approverType={approvalApproverType}
                                onApproverTypeChange={(next) => {
                                  setApprovalApproverType(next);
                                  if (next === "user") setApprovalGroupId(null);
                                  if (next === "group") setApproverPick(null);
                                }}
                                groupId={approvalGroupId}
                                onGroupIdChange={setApprovalGroupId}
                                onApplyContent={setApprovalContent}
                                disabled={saving}
                              />
                              {approvalApproverType === "user" ? (
                                <div className="helpdesk-ticket-workspace__approval-approver">
                                  <span className="helpdesk-ticket-workspace__field-label">
                                    Aprovador
                                  </span>
                                  <HelpdeskAssigneePicker
                                    label="Aprovador"
                                    value={approverPick}
                                    onChange={setApproverPick}
                                    disabled={saving}
                                    purpose="mention"
                                    placeholder="Buscar aprovador…"
                                    emptyLabel="Nenhum aprovador selecionado"
                                  />
                                </div>
                              ) : null}
                              <HelpdeskRichTextField
                                label="Mensagem"
                                hint={helpTooltips.detailUi.requestApproval}
                                value={approvalContent}
                                onChange={setApprovalContent}
                                minHeight={120}
                                enableMentions
                              />
                              <HelpdeskFormActions align="end">
                                <ActionButton
                                  type="button"
                                  variant="ghost"
                                  disabled={saving}
                                  onClick={cancelActiveActionForm}
                                >
                                  Cancelar
                                </ActionButton>
                                <ActionButton
                                  variant="primary"
                                  type="submit"
                                  disabled={
                                    saving ||
                                    (approvalApproverType === "user"
                                      ? !approverPick?.id ||
                                        !Number.isFinite(Number(approverPick.id))
                                      : approvalGroupId == null || approvalGroupId <= 0)
                                  }
                                >
                                  {saving
                                    ? ticketActionPresentation("request_approval").submittingLabel
                                    : ticketActionPresentation("request_approval").submitLabel}
                                </ActionButton>
                              </HelpdeskFormActions>
                            </form>
                            </TicketActionCard>
                          ) : null}
                          {activeAction === "attach_file" ? (
                            <TicketActionCard
                              actionId="attach_file"
                              disabled={saving}
                              onCancel={cancelActiveActionForm}
                            >
                              <div className="helpdesk-ticket-workspace__document">
                                <input
                                  ref={documentInputRef}
                                  type="file"
                                  multiple
                                  hidden
                                  onChange={(event) => {
                                    setDocumentFiles(Array.from(event.target.files || []));
                                    event.target.value = "";
                                  }}
                                />
                                <SectionHintLabel
                                  label="Anexa arquivos ao chamado sem enviar uma mensagem."
                                  hint={helpTooltips.detailUi.attachFile}
                                />
                                <label className="helpdesk-action-fields__field">
                                  <span>Título (opcional)</span>
                                  <input
                                    type="text"
                                    value={documentTitle}
                                    disabled={saving}
                                    placeholder="Nome exibido no documento"
                                    onChange={(event) => setDocumentTitle(event.target.value)}
                                  />
                                </label>
                                {documentFiles.length > 0 ? (
                                  <ul className="helpdesk-ticket-workspace__document-list">
                                    {documentFiles.map((file) => (
                                      <li key={`${file.name}-${file.size}-${file.lastModified}`}>
                                        {file.name}
                                      </li>
                                    ))}
                                  </ul>
                                ) : null}
                                <HelpdeskFormActions align="end">
                                  <ActionButton
                                    type="button"
                                    variant="ghost"
                                    disabled={saving}
                                    onClick={cancelActiveActionForm}
                                  >
                                    Cancelar
                                  </ActionButton>
                                  <ActionButton
                                    type="button"
                                    variant="ghost"
                                    onClick={() => documentInputRef.current?.click()}
                                    disabled={saving}
                                  >
                                    Escolher arquivos
                                  </ActionButton>
                                  <ActionButton
                                    type="button"
                                    variant="primary"
                                    disabled={saving || documentFiles.length === 0}
                                    onClick={() => {
                                      if (documentFiles.length === 0) return;
                                      setSaving(true);
                                      setErrorText(null);
                                      const title = documentTitle.trim();
                                      void (async () => {
                                        try {
                                          for (const file of documentFiles) {
                                            await uploadTicketAttachment(
                                              ticketId,
                                              file,
                                              newIdempotencyKey(),
                                              title ? { title } : undefined,
                                            );
                                          }
                                          setDocumentFiles([]);
                                          setDocumentTitle("");
                                          closeActionAfterSuccess();
                                          load();
                                        } catch (error) {
                                          setErrorText(
                                            messageFor(error).text ||
                                              ticketActionPresentation("attach_file").errorFallback,
                                          );
                                        } finally {
                                          setSaving(false);
                                        }
                                      })();
                                    }}
                                  >
                                    {saving
                                      ? ticketActionPresentation("attach_file").submittingLabel
                                      : ticketActionPresentation("attach_file").submitLabel}
                                  </ActionButton>
                                </HelpdeskFormActions>
                              </div>
                            </TicketActionCard>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  </div>
                )}
              </div>
              <div className="helpdesk-ticket-workspace__aside">
                <TicketContextPanel
                  ticket={ticket}
                  assigneePick={assigneePick}
                  onAssigneeChange={setAssigneePick}
                  onAssignConfirm={assignTechnician}
                  assignSaving={assignSaving}
                />
              </div>
            </div>
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
          </>
        ) : null}
      </div>
    </HelpdeskPageStack>
  );
}
