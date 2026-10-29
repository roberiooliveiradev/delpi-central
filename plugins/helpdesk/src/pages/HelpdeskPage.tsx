import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import {
  ActionButton,
  FieldLabel,
  FilePreviewModal,
  HintAction,
  SectionHintLabel,
  TableColumnVisibilityMenu,
} from "@delpi/plugin-ui/index";
import { AlignLeft, Building2, ChevronLeft, ExternalLink, FilterX, FolderTree, Gauge, Image as ImageIcon, Link2, Monitor, Paperclip, Pencil, Plus, RefreshCw, Send, TicketPlus, Trash2, Type, Users, X } from "lucide-react";

import {
  HelpdeskApiError,
  acceptTicketSolution,
  acceptTicketValidation,
  beginGlpiLink,
  createFollowup,
  createTicket,
  createTicketSolution,
  createTicketTask,
  deleteTicket,
  fetchTicketAttachmentBlob,
  getSessionCapabilities,
  getSessionContext,
  getTicket,
  listCategories,
  listImpacts,
  listRequestTypes,
  listTicketRequestTypes,
  listTicketTypes,
  listTickets,
  listUrgencies,
  listUsers,
  rejectTicketSolution,
  rejectTicketValidation,
  requestTicketApproval,
  searchTicketItems,
  setTicketAssignee,
  submitTicketSatisfaction,
  updateFollowup,
  updateTicketClassification,
  updateTicketDescription,
  uploadTicketAttachment,
  type ClassificationPatch,
  type SessionContext,
  type TicketAttachment,
  type TicketDetail,
  type TicketItemOption,
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
  unassignedTicketAttachments,
  TICKET_STATUS_FILTERS,
  type TicketListFilters,
  viewForTicketLoad,
} from "../presentation/ticketView";
import {
  hasUnresolvedInlineImageRefs,
  listPendingInlineIds,
  normalizeInlineAttachmentSrcs,
  rewritePendingInlineImages,
  stripPendingInlineImages,
} from "../presentation/inlineUpload";
import {
  ATTACHMENT_AUTHOR_NOTICE_TEXT,
  attachmentAuthorDegraded,
  consumeAttachmentAuthorNotice,
  consumeTicketNotice,
  stageAttachmentAuthorNotice,
  stageTicketNotice,
} from "../presentation/attachmentAuthorNotice";
import {
  TICKET_DELETE_UNCONFIRMED_TEXT,
  canShowTicketDelete,
  consumeTicketDeleteNotice,
  stageTicketDeleteNotice,
  ticketDeleteConfirmed,
  ticketDeleteErrorText,
  ticketDeleteSuccessText,
} from "../presentation/ticketDeleteFlow";
import type {
  HelpdeskInlineUploadResult,
  HelpdeskPendingAttachmentItem,
} from "../ui/helpdeskUi";
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
import { TicketApprovalsSurface } from "./TicketApprovalsSurface";
import { TicketContextPanel } from "./TicketContextPanel";
import { TicketDetailsSurface, type ClassificationCatalogs } from "./TicketDetailsSurface";
import { TicketListCards } from "./TicketListCards";
import { ticketActionPresentation } from "../presentation/ticketActionPresentation";
import {
  defaultTicketWorkspaceAction,
  ticketWorkspaceActions,
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
  HelpdeskConfirmModal,
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
  HelpdeskTextArea,
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
  idempotency_in_flight: "Uma tentativa anterior pode ter sido concluída. Verifique o chamado antes de enviar de novo.",
  inline_image_pending: "Não foi possível enviar: uma imagem ainda está sendo anexada. Aguarde e envie de novo.",
  inline_image_unresolved: "Não foi possível enviar: uma imagem da mensagem não pôde ser vinculada a este chamado. Remova-a e anexe de novo.",
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

function formatAttachmentBytes(size: number): string {
  if (!Number.isFinite(size) || size < 0) return "";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(size < 10 * 1024 ? 1 : 0)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function isInlineImageFile(file: File): boolean {
  return (
    file.type.startsWith("image/") || /\.(png|jpe?g|gif|webp|bmp)$/i.test(file.name || "")
  );
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
  const [noticeText] = useState<string | null>(() => consumeTicketDeleteNotice());
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
        {view === "list" && noticeText ? (
          <HelpdeskStateBanner>{noticeText}</HelpdeskStateBanner>
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
      </div>
    </HelpdeskPageStack>
  );
}

/**
 * Etapa 1 — "Itens" + "Objetos de assistência relacionados" do GLPI.
 * Collapsible section: authorized asset search (profile-gated scope) and
 * related-ticket linking (Ticket_Ticket "link to" only — the canonical
 * proven relation type). All selections persist via POST /tickets.
 */
export function CreateItemsSection({
  sessionCtx,
  disabled,
  open,
  onToggle,
  scope,
  onScopeChange,
  typeFilter,
  onTypeFilterChange,
  query,
  onQueryChange,
  results,
  searching,
  searched,
  searchError,
  selections,
  related,
  relatedInput,
  onRelatedInputChange,
  onSearchItems,
  onAddItem,
  onRemoveItem,
  onAddRelated,
  onRemoveRelated,
}: {
  sessionCtx: SessionContext | null;
  disabled: boolean;
  open: boolean;
  onToggle: (open: boolean) => void;
  scope: "mine" | "all";
  onScopeChange: (scope: "mine" | "all") => void;
  typeFilter: string;
  onTypeFilterChange: (value: string) => void;
  query: string;
  onQueryChange: (value: string) => void;
  results: TicketItemOption[];
  searching: boolean;
  searched: boolean;
  searchError: string | null;
  selections: TicketItemOption[];
  related: { id: number; title: string }[];
  relatedInput: string;
  onRelatedInputChange: (value: string) => void;
  onSearchItems: () => void;
  onAddItem: (item: TicketItemOption) => void;
  onRemoveItem: (item: TicketItemOption) => void;
  onAddRelated: (row: { id: number; title: string }) => void;
  onRemoveRelated: (id: number) => void;
}) {
  const hardware = sessionCtx?.hardware;
  const itemTypes = hardware?.item_types ?? [];
  const canMine = hardware?.my_devices === true;
  const canAll = hardware?.all_devices === true;
  const itemsAvailable = canMine || canAll;
  const [relatedResults, setRelatedResults] = useState<TicketSummary[]>([]);
  const [relatedSearched, setRelatedSearched] = useState(false);
  const [relatedSearching, setRelatedSearching] = useState(false);
  const [relatedError, setRelatedError] = useState<string | null>(null);

  if (!itemsAvailable && related.length === 0 && selections.length === 0 && !open) {
    // Nothing to offer and nothing selected — keep the form lean.
    return null;
  }

  const searchRelated = () => {
    const q = relatedInput.trim();
    if (!q) return;
    setRelatedSearching(true);
    setRelatedError(null);
    void listTickets({ q, page_size: "8" })
      .then((payload) => {
        setRelatedResults(payload.items ?? []);
        setRelatedSearched(true);
      })
      .catch((error) => {
        setRelatedResults([]);
        setRelatedSearched(true);
        setRelatedError(messageFor(error).text);
      })
      .finally(() => setRelatedSearching(false));
  };

  return (
    <section className="helpdesk-create-items" aria-label="Itens e chamados relacionados">
      <button
        type="button"
        className="helpdesk-create-items__toggle"
        aria-expanded={open}
        onClick={() => onToggle(!open)}
      >
        <Monitor size={15} aria-hidden />
        Itens e chamados relacionados
        {selections.length + related.length > 0 ? (
          <span className="helpdesk-create-items__count">{selections.length + related.length}</span>
        ) : null}
      </button>
      {open ? (
        <div className="helpdesk-create-items__body">
          {itemsAvailable ? (
            <div className="helpdesk-create-items__search">
              <HelpdeskSelect
                label="Origem da busca"
                value={scope}
                onChange={(value) => onScopeChange(value === "all" ? "all" : "mine")}
                options={[
                  ...(canMine ? [{ value: "mine", label: "Meus equipamentos" }] : []),
                  ...(canAll ? [{ value: "all", label: "Todos os equipamentos" }] : []),
                ]}
              />
              <HelpdeskSelect
                label="Tipo de item"
                value={typeFilter}
                onChange={onTypeFilterChange}
                options={[
                  { value: "", label: "Todos os tipos" },
                  ...itemTypes.map(([itemtype, label]) => ({ value: itemtype, label })),
                ]}
              />
              <HelpdeskTextField
                label="Buscar equipamento"
                value={query}
                onChange={onQueryChange}
                ariaLabel="Buscar equipamento por nome, serial ou inventário"
              />
              <ActionButton
                type="button"
                variant="ghost"
                disabled={disabled || searching}
                onClick={onSearchItems}
              >
                {searching ? "Buscando…" : "Buscar"}
              </ActionButton>
            </div>
          ) : null}
          {searchError ? (
            <HelpdeskStateBanner variant="error">{searchError}</HelpdeskStateBanner>
          ) : null}
          {searched && !searching && results.length === 0 && !searchError ? (
            <p className="helpdesk-create-items__empty">Nenhum equipamento encontrado.</p>
          ) : null}
          {results.length > 0 ? (
            <ul className="helpdesk-create-items__results" role="list">
              {results.map((item) => {
                const selected = selections.some(
                  (row) => row.itemtype === item.itemtype && row.items_id === item.items_id,
                );
                return (
                  <li key={`${item.itemtype}-${item.items_id}`}>
                    <span className="helpdesk-create-items__result-label">
                      <strong>{item.name}</strong>
                      <small>
                        {item.type_label || item.itemtype} #{item.items_id}
                        {item.serial ? ` · S/N ${item.serial}` : ""}
                        {item.inventory_number ? ` · Inv. ${item.inventory_number}` : ""}
                        {item.entity ? ` · ${item.entity}` : ""}
                      </small>
                    </span>
                    <ActionButton
                      type="button"
                      variant="ghost"
                      disabled={disabled || selected}
                      aria-label={`Vincular ${item.name}`}
                      onClick={() => onAddItem(item)}
                    >
                      {selected ? "Vinculado" : "Vincular"}
                    </ActionButton>
                  </li>
                );
              })}
            </ul>
          ) : null}
          {selections.length > 0 ? (
            <div className="helpdesk-create-items__chips" aria-label="Equipamentos selecionados">
              {selections.map((item) => (
                <span key={`${item.itemtype}-${item.items_id}`} className="helpdesk-create-items__chip">
                  {item.name}
                  <button
                    type="button"
                    aria-label={`Remover ${item.name}`}
                    disabled={disabled}
                    onClick={() => onRemoveItem(item)}
                  >
                    <X size={13} aria-hidden />
                  </button>
                </span>
              ))}
            </div>
          ) : null}
          <div className="helpdesk-create-items__related">
            <HelpdeskTextField
              label="Chamado relacionado"
              value={relatedInput}
              onChange={onRelatedInputChange}
              ariaLabel="Buscar chamado por número ou título"
            />
            <ActionButton
              type="button"
              variant="ghost"
              disabled={disabled || relatedSearching || !relatedInput.trim()}
              onClick={searchRelated}
            >
              {relatedSearching ? "Buscando…" : "Buscar chamado"}
            </ActionButton>
            {relatedError ? (
              <HelpdeskStateBanner variant="error">{relatedError}</HelpdeskStateBanner>
            ) : null}
            {relatedSearched && !relatedSearching && relatedResults.length === 0 && !relatedError ? (
              <p className="helpdesk-create-items__empty">Nenhum chamado encontrado.</p>
            ) : null}
            {relatedResults.length > 0 ? (
              <ul className="helpdesk-create-items__results" role="list">
                {relatedResults.map((row) => {
                  const selected = related.some((entry) => entry.id === row.id);
                  return (
                    <li key={row.id}>
                      <span className="helpdesk-create-items__result-label">
                        <strong>#{row.id}</strong> {row.title}
                      </span>
                      <ActionButton
                        type="button"
                        variant="ghost"
                        disabled={disabled || selected}
                        aria-label={`Relacionar chamado ${row.id}`}
                        onClick={() => onAddRelated({ id: row.id, title: row.title })}
                      >
                        {selected ? "Relacionado" : "Relacionar"}
                      </ActionButton>
                    </li>
                  );
                })}
              </ul>
            ) : null}
            {related.length > 0 ? (
              <div className="helpdesk-create-items__chips" aria-label="Chamados relacionados">
                {related.map((row) => (
                  <span key={row.id} className="helpdesk-create-items__chip">
                    #{row.id} {row.title}
                    <button
                      type="button"
                      aria-label={`Remover chamado ${row.id}`}
                      disabled={disabled}
                      onClick={() => onRemoveRelated(row.id)}
                    >
                      <X size={13} aria-hidden />
                    </button>
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
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
  const [typeId, setTypeId] = useState(savedDraft?.typeId ?? "");
  const [impactId, setImpactId] = useState(savedDraft?.impactId ?? "");
  const [requestTypeId, setRequestTypeId] = useState(savedDraft?.requestTypeId ?? "");
  const [itemSelections, setItemSelections] = useState<TicketItemOption[]>(
    () =>
      (savedDraft?.itemLinks ?? []).map((row) => ({
        itemtype: row.itemtype,
        items_id: row.itemsId,
        name: row.name,
        type_label: row.typeLabel,
      })),
  );
  const [relatedTickets, setRelatedTickets] = useState<{ id: number; title: string }[]>(
    () => savedDraft?.relatedTickets ?? [],
  );
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const [urgencies, setUrgencies] = useState<{ id: number; name: string }[]>([]);
  const [impacts, setImpacts] = useState<{ id: number; name: string }[]>([]);
  const [ticketTypes, setTicketTypes] = useState<{ id: number; name: string }[]>([]);
  const [ticketRequestTypes, setTicketRequestTypes] = useState<{ id: number; name: string }[]>([]);
  const [sessionCtx, setSessionCtx] = useState<SessionContext | null>(null);
  const [itemScope, setItemScope] = useState<"mine" | "all">("mine");
  const [itemTypeFilter, setItemTypeFilter] = useState("");
  const [itemQuery, setItemQuery] = useState("");
  const [itemResults, setItemResults] = useState<TicketItemOption[]>([]);
  const [itemSearching, setItemSearching] = useState(false);
  const [itemSearched, setItemSearched] = useState(false);
  const [itemSearchError, setItemSearchError] = useState<string | null>(null);
  const [relatedInput, setRelatedInput] = useState("");
  const [itemsOpen, setItemsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [idempotencyKey] = useState(newIdempotencyKey);
  const [pendingHydrated, setPendingHydrated] = useState(0);
  const pendingFilesRef = useRef<Map<string, File>>(new Map());
  const pendingPreviewUrlsRef = useRef<Map<string, string>>(new Map());
  const createComposerRef = useRef<HelpdeskRichTextFieldHandle>(null);
  /** Non-image staged files shown as removable chips (they are not inline imgs). */
  const [pendingAttachments, setPendingAttachments] = useState<HelpdeskPendingAttachmentItem[]>([]);
  const [pendingPreviewId, setPendingPreviewId] = useState<string | null>(null);
  const pendingPreview = useMemo(
    () => pendingAttachments.find((item) => item.id === pendingPreviewId) ?? null,
    [pendingAttachments, pendingPreviewId],
  );

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
      setPendingAttachments(
        rows
          .filter((row) => !isInlineImageFile(row.file))
          .map((row) => ({
            id: row.id,
            fileName: row.file.name || "anexo",
            contentType: row.file.type || null,
          })),
      );
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
      listImpacts(controller.signal),
      listTicketTypes(controller.signal),
      listTicketRequestTypes(),
      getSessionContext(controller.signal),
    ])
      .then(
        ([
          categoryResult,
          urgencyResult,
          capsResult,
          impactResult,
          typeResult,
          requestTypeResult,
          contextResult,
        ]) => {
          if (controller.signal.aborted) return;
          const draft = readCreateDraft();
          if (capsResult.status === "fulfilled") {
            setCanAssign(Boolean(capsResult.value.can_assign));
          } else {
            setCanAssign(false);
          }
          if (contextResult.status === "fulfilled") {
            setSessionCtx(contextResult.value);
          }
          const contextDefaultRequestType =
            contextResult.status === "fulfilled"
              ? contextResult.value.default_request_type_id
              : null;
          const pickOrDefault = (
            items: { id: number; name: string }[],
            draftValue: string | undefined,
            defaultId: number | null,
          ) =>
            (current: string) => {
              if (current && items.some((item) => String(item.id) === current)) return current;
              if (draftValue && items.some((item) => String(item.id) === draftValue)) {
                return draftValue;
              }
              // Canonical GLPI default only (never "first catalog row").
              if (defaultId !== null && items.some((item) => item.id === defaultId)) {
                return String(defaultId);
              }
              return "";
            };
          if (urgencyResult.status === "fulfilled") {
            const items = urgencyResult.value.items;
            setUrgencies(items);
            // GLPI Ticket::getDefaultValues → urgency 3 (proven canonical).
            setUrgencyId(pickOrDefault(items, draft?.urgencyId, 3));
          }
          if (impactResult.status === "fulfilled") {
            const items = impactResult.value.items;
            setImpacts(items);
            setImpactId(pickOrDefault(items, draft?.impactId, 3));
          }
          if (typeResult.status === "fulfilled") {
            const items = typeResult.value.items;
            setTicketTypes(items);
            // Entity config tickettype → Delpi=incident(1); GLPI fallback is
            // incident too (Ticket::getDefaultValues).
            setTypeId(pickOrDefault(items, draft?.typeId, 1));
          }
          if (requestTypeResult.status === "fulfilled") {
            const items = requestTypeResult.value;
            setTicketRequestTypes(items);
            setRequestTypeId(
              pickOrDefault(items, draft?.requestTypeId, contextDefaultRequestType ?? null),
            );
          }
          if (categoryResult.status === "fulfilled") {
            const items = categoryResult.value.items;
            setCategories(items);
            // Category has NO canonical default (GLPI 0 = none) — explicit
            // selection only; draft restore is the only allowed prefill.
            setCategoryId((current) => {
              if (current && items.some((item) => String(item.id) === current)) return current;
              if (draft?.categoryId && items.some((item) => String(item.id) === draft.categoryId)) {
                return draft.categoryId;
              }
              return "";
            });
            return;
          }
          setErrorText(MESSAGES.catalog_unavailable);
        },
      )
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
      typeId,
      impactId,
      requestTypeId,
      itemLinks: itemSelections.map((item) => ({
        itemtype: item.itemtype,
        itemsId: item.items_id,
        name: item.name,
        typeLabel: item.type_label,
      })),
      relatedTickets: relatedTickets.map((row) => ({ id: row.id, title: row.title })),
    });
  }, [
    title,
    description,
    observerIdsInput,
    assignee,
    categoryId,
    urgencyId,
    typeId,
    impactId,
    requestTypeId,
    itemSelections,
    relatedTickets,
  ]);

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

  const removePendingAttachment = useCallback(
    (pendingId: string) => {
      const cached = pendingPreviewUrlsRef.current.get(pendingId);
      if (cached) {
        try {
          URL.revokeObjectURL(cached);
        } catch {
          /* ignore */
        }
        pendingPreviewUrlsRef.current.delete(pendingId);
      }
      pendingFilesRef.current.delete(pendingId);
      setPendingAttachments((current) => current.filter((item) => item.id !== pendingId));
      persistCreatePendingFiles();
    },
    [persistCreatePendingFiles],
  );

  const queuePendingFiles = async (files: File[]): Promise<HelpdeskInlineUploadResult[]> => {
    const results: HelpdeskInlineUploadResult[] = [];
    const staged: HelpdeskPendingAttachmentItem[] = [];
    for (const file of files) {
      const pendingId = newIdempotencyKey();
      pendingFilesRef.current.set(pendingId, file);
      if (isInlineImageFile(file)) {
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
      } else {
        staged.push({
          id: pendingId,
          fileName: file.name || "anexo",
          contentType: file.type || null,
        });
      }
    }
    if (staged.length > 0) {
      setPendingAttachments((current) => [...current, ...staged]);
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
            if (saving || !title.trim() || !hasVisibleRichText(description) || !categoryId) return;
            setSaving(true);
            setErrorText(null);
            void (async () => {
              // Read the live editor DOM — a pasted image can still be in
              // flight between materialize/insert and React state.
              const liveDescription =
                (await createComposerRef.current?.prepareForSubmit()) || description;
              const pendingIds = [
                ...new Set([
                  ...listPendingInlineIds(liveDescription),
                  ...pendingFilesRef.current.keys(),
                ]),
              ];
              const openingHtml =
                persistHelpdeskAttachmentHtml(
                  stripPendingInlineImages(liveDescription),
                ).trim() || "<p>Anexo(s)</p>";
            void createTicket(
              {
                title: title.trim(),
                description: openingHtml,
                category_id: Number(categoryId),
                urgency_id: Number(urgencyId),
                observer_ids: parseObserverIdsInput(observerIdsInput),
                assignee_id: canAssign === true && assignee?.id ? Number(assignee.id) : undefined,
                type_id: typeId ? Number(typeId) : undefined,
                impact_id: impactId ? Number(impactId) : undefined,
                request_type_id: requestTypeId ? Number(requestTypeId) : undefined,
                item_links: itemSelections.map((item) => ({
                  itemtype: item.itemtype,
                  items_id: item.items_id,
                })),
                related_ticket_ids: relatedTickets.map((row) => row.id),
              },
              idempotencyKey,
            )
              .then(async (created) => {
                const ticketId = String(created.id);
                // Typed partial outcome — ticket persisted but one or more
                // post-create links failed. Never presented as integral
                // success; the notice rides to the detail page.
                const failedLinks =
                  (created.failed_items?.length ?? 0) + (created.failed_tickets?.length ?? 0);
                if (failedLinks > 0) {
                  stageTicketNotice(
                    "O chamado foi criado, mas " +
                      `${failedLinks} vínculo${failedLinks > 1 ? "s" : ""} ` +
                      "(equipamento ou chamado relacionado) não pôde ser confirmado no GLPI. " +
                      "Revise os itens vinculados abaixo.",
                  );
                }
                const mapping: Record<string, { documentId: number; ticketId: string }> = {};
                for (const pendingId of pendingIds) {
                  const file = pendingFilesRef.current.get(pendingId);
                  if (!file) continue;
                  try {
                    const uploaded = await uploadTicketAttachment(
                      ticketId,
                      file,
                      `${idempotencyKey}:file:${pendingId}`,
                    );
                    if (attachmentAuthorDegraded(uploaded)) {
                      stageAttachmentAuthorNotice();
                    }
                    if (file.type.startsWith("image/")) {
                      mapping[pendingId] = { documentId: uploaded.document_id, ticketId };
                    }
                    pendingFilesRef.current.delete(pendingId);
                  } catch (error) {
                    // One failed file must not orphan the others — the pending
                    // ref stays in the map and is stripped from the HTML below.
                    setErrorText(messageFor(error).text);
                  }
                }
                // Inline images keep their original position: rewrite the
                // pending placeholders to stable document refs and persist
                // the whole description on the ticket itself (no separate
                // image-only followup).
                if (
                  Object.keys(mapping).length > 0 &&
                  hasUnresolvedInlineImageRefs(liveDescription)
                ) {
                  // Failed uploads keep `attachment:pending:` refs — strip them
                  // so they cannot poison the whole description update (the BFF
                  // rejects unresolved refs; the create itself already went
                  // through without them).
                  const rewritten = persistHelpdeskAttachmentHtml(
                    stripPendingInlineImages(
                      rewritePendingInlineImages(liveDescription, mapping),
                    ),
                    ticketId,
                  );
                  if (rewritten.trim() && !hasUnresolvedInlineImageRefs(rewritten)) {
                    await updateTicketDescription(
                      ticketId,
                      { content: rewritten },
                      `${idempotencyKey}:description`,
                    );
                  }
                }
                clearCreateDraft();
                setPendingAttachments([]);
                setPendingPreviewId(null);
                void clearHelpdeskDraftPendingFiles(HELPDESK_CREATE_DRAFT_SCOPE);
                navigateHelpdesk(`/apps/helpdesk/tickets/${created.id}`);
              })
              .catch((error) => {
                setErrorText(messageFor(error).text);
                setSaving(false);
              });
            })();
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
                pendingAttachments={pendingAttachments}
                onPendingAttachmentOpen={(id) => setPendingPreviewId(id)}
                onPendingAttachmentRemove={removePendingAttachment}
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
              {ticketTypes.length > 0 ? (
                <HelpdeskSelect
                  label="Tipo de chamado"
                  hint={helpTooltips.createUi.ticketType}
                  value={typeId}
                  onChange={setTypeId}
                  options={ticketTypes.map((item) => ({ value: String(item.id), label: item.name }))}
                  icon={<TicketPlus size={14} aria-hidden />}
                />
              ) : null}
              <HelpdeskSelect
                label="Urgência"
                hint={helpTooltips.createUi.urgency}
                value={urgencyId}
                onChange={setUrgencyId}
                required
                options={urgencies.map((item) => ({ value: String(item.id), label: item.name }))}
                icon={<Gauge size={14} aria-hidden />}
              />
              {impacts.length > 0 ? (
                <HelpdeskSelect
                  label="Impacto"
                  hint={helpTooltips.createUi.impact}
                  value={impactId}
                  onChange={setImpactId}
                  options={impacts.map((item) => ({ value: String(item.id), label: item.name }))}
                  icon={<Gauge size={14} aria-hidden />}
                />
              ) : null}
              {ticketRequestTypes.length > 0 ? (
                <HelpdeskSelect
                  label="Origem"
                  hint={helpTooltips.createUi.requestType}
                  value={requestTypeId}
                  onChange={setRequestTypeId}
                  options={ticketRequestTypes.map((item) => ({
                    value: String(item.id),
                    label: item.name,
                  }))}
                  icon={<Link2 size={14} aria-hidden />}
                />
              ) : null}
              <div className="helpdesk-create-entity" aria-label="Entidade do chamado">
                <span className="helpdesk-create-entity__label">
                  <Building2 size={14} aria-hidden />
                  Entidade
                </span>
                <span className="helpdesk-create-entity__value">
                  {sessionCtx?.entity?.name || "Carregando…"}
                </span>
              </div>
              {canAssign === true ? (
                <HelpdeskAssigneePicker
                  label="Técnico atribuído"
                  hint={helpTooltips.createUi.assignee}
                  value={assignee}
                  onChange={setAssignee}
                  emptyLabel="Sem técnico"
                  disabled={saving || loading}
                />
              ) : null}
              <HelpdeskTextField
                label="Observadores"
                hint={helpTooltips.createUi.observers}
                value={observerIdsInput}
                onChange={setObserverIdsInput}
                icon={<Users size={14} aria-hidden />}
              />
            </aside>
          </div>
          <div className="helpdesk-create-files">
            <div className="helpdesk-create-files__actions">
              <ActionButton
                type="button"
                variant="ghost"
                className="helpdesk-compose-attach"
                aria-label="Inserir imagem no texto"
                disabled={saving || loading}
                onClick={() => createComposerRef.current?.openAttachPicker("image/*")}
              >
                <ImageIcon size={16} aria-hidden />
                Inserir imagem no texto
              </ActionButton>
              <HintAction hint={helpTooltips.createUi.attach} ariaLabel="Ajuda: Anexar arquivo">
                <ActionButton
                  type="button"
                  variant="ghost"
                  className="helpdesk-compose-attach"
                  aria-label="Anexar arquivo ao chamado"
                  disabled={saving || loading}
                  onClick={() => createComposerRef.current?.openAttachPicker()}
                >
                  <Paperclip size={16} aria-hidden />
                  Anexar arquivo ao chamado
                </ActionButton>
              </HintAction>
              <HintAction hint={helpTooltips.createUi.send} ariaLabel="Ajuda: Enviar chamado">
                <ActionButton
                  variant="primary"
                  type="submit"
                  className="helpdesk-create-send"
                  aria-label={saving ? "Enviando" : "Enviar chamado"}
                  disabled={
                    saving || loading || !title.trim() || !hasVisibleRichText(description) || !categoryId
                  }
                >
                  <Send size={18} aria-hidden />
                  {saving ? "Enviando…" : "Enviar"}
                </ActionButton>
              </HintAction>
            </div>
            <p className="helpdesk-create-files__hint">
              Imagens inseridas aparecem dentro da descrição. Arquivos anexados ficam
              disponíveis nos documentos do chamado.
            </p>
          </div>
          <CreateItemsSection
            sessionCtx={sessionCtx}
            disabled={saving || loading}
            open={itemsOpen}
            onToggle={setItemsOpen}
            scope={itemScope}
            onScopeChange={setItemScope}
            typeFilter={itemTypeFilter}
            onTypeFilterChange={setItemTypeFilter}
            query={itemQuery}
            onQueryChange={setItemQuery}
            results={itemResults}
            searching={itemSearching}
            searched={itemSearched}
            searchError={itemSearchError}
            selections={itemSelections}
            related={relatedTickets}
            relatedInput={relatedInput}
            onRelatedInputChange={setRelatedInput}
            onSearchItems={() => {
              setItemSearching(true);
              setItemSearchError(null);
              void searchTicketItems(
                {
                  scope: itemScope,
                  itemtype: itemTypeFilter || undefined,
                  q: itemQuery.trim(),
                  limit: 25,
                },
              )
                .then((payload) => {
                  setItemResults(payload.items ?? []);
                  setItemSearched(true);
                })
                .catch((error) => {
                  setItemResults([]);
                  setItemSearched(true);
                  setItemSearchError(messageFor(error).text);
                })
                .finally(() => setItemSearching(false));
            }}
            onAddItem={(item) => {
              setItemSelections((current) =>
                current.some(
                  (row) => row.itemtype === item.itemtype && row.items_id === item.items_id,
                )
                  ? current
                  : [...current, item],
              );
            }}
            onRemoveItem={(item) => {
              setItemSelections((current) =>
                current.filter(
                  (row) => !(row.itemtype === item.itemtype && row.items_id === item.items_id),
                ),
              );
            }}
            onAddRelated={(row) => {
              setRelatedTickets((current) =>
                current.some((entry) => entry.id === row.id) ? current : [...current, row],
              );
              setRelatedInput("");
            }}
            onRemoveRelated={(id) => {
              setRelatedTickets((current) => current.filter((row) => row.id !== id));
            }}
          />
        </form>
      </HelpdeskSectionCard>
      <FilePreviewModal
        open={pendingPreviewId !== null}
        title="Anexo"
        fileName={pendingPreview?.fileName || "anexo"}
        mimeType={pendingPreview?.contentType || "application/octet-stream"}
        source={
          pendingPreviewId
            ? () => Promise.resolve(pendingFilesRef.current.get(pendingPreviewId) as Blob)
            : null
        }
        portalScopeClassName="dashboard-helpdesk"
        onClose={() => setPendingPreviewId(null)}
      />
    </HelpdeskPageStack>
  );
}

function TicketDetailPage({ ticketId }: { ticketId: string }) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [noticeText, setNoticeText] = useState<string | null>(
    () => consumeAttachmentAuthorNotice() ?? consumeTicketNotice(),
  );
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
  /** In-flight uploads keyed by pendingId — submit awaits these, never re-uploads. */
  const inlineUploadsRef = useRef<Map<string, Promise<number | null>>>(new Map());
  const replyComposerRef = useRef<HelpdeskRichTextFieldHandle>(null);
  /** Non-image files staged in the reply composer — removable chips below the editor. */
  const [pendingAttachments, setPendingAttachments] = useState<HelpdeskPendingAttachmentItem[]>([]);
  const [pendingPreviewId, setPendingPreviewId] = useState<string | null>(null);
  const pendingPreview = useMemo(
    () => pendingAttachments.find((item) => item.id === pendingPreviewId) ?? null,
    [pendingAttachments, pendingPreviewId],
  );
  /** In-place follow-up editing — `editingId`/`renderEditSlot` contract. */
  const [followupEditingId, setFollowupEditingId] = useState<string | null>(null);
  const [followupEditContent, setFollowupEditContent] = useState("");
  const [followupEditSaving, setFollowupEditSaving] = useState(false);
  const [followupEditError, setFollowupEditError] = useState<string | null>(null);
  const [followupEditKey, setFollowupEditKey] = useState(newIdempotencyKey);
  /** Governed classification edit — catalogs load lazily on first edit. */
  const [classificationEditing, setClassificationEditing] = useState(false);
  const [classificationSaving, setClassificationSaving] = useState(false);
  const [classificationCatalogs, setClassificationCatalogs] =
    useState<ClassificationCatalogs | null>(null);
  const [classificationCatalogsLoading, setClassificationCatalogsLoading] = useState(false);
  const [classificationKey, setClassificationKey] = useState(newIdempotencyKey);
  /** Move-to-trash intent — key generated per confirmation open (one intent). */
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteKey, setDeleteKey] = useState(newIdempotencyKey);
  const [deleting, setDeleting] = useState(false);
  const [deleteChecking, setDeleteChecking] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

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

  /**
   * One upload per pendingId — the stable key makes F5/retry the same
   * intent at the BFF instead of a new blind write. Resolves the
   * document_id (or null on failure); the promise is memoized so the
   * submit path can await it without duplicating the request.
   */
  const startInlineUpload = useCallback(
    (pendingId: string, file: File): Promise<number | null> => {
      const existing = inlineUploadsRef.current.get(pendingId);
      if (existing) return existing;
      const promise = uploadTicketAttachment(ticketId, file, `file:${pendingId}`)
        .then((uploaded) => {
          if (attachmentAuthorDegraded(uploaded)) {
            setNoticeText(ATTACHMENT_AUTHOR_NOTICE_TEXT);
          }
          attachmentPreview.transferPendingSeed(pendingId, uploaded.document_id);
          rekeyDraftFileToDocument(
            pendingFilesRef.current,
            pendingId,
            uploaded.document_id,
          );
          void persistReplyPendingFiles();
          return uploaded.document_id;
        })
        .catch((error) => {
          setErrorText(messageFor(error).text);
          return null;
        });
      inlineUploadsRef.current.set(pendingId, promise);
      return promise;
    },
    [
      ticketId,
      attachmentPreview.transferPendingSeed,
      persistReplyPendingFiles,
    ],
  );

  /** Resolve every pending inline ref: await in-flight uploads, start the ones
   * restored from draft. Returns the rewritten HTML or a typed failure so the
   * caller can distinguish an upload that failed from a reference that has no
   * file backing it — the send is blocked either way, never stripped. */
  const resolveInlineUploadsForSubmit = useCallback(
    async (
      html: string,
    ): Promise<
      { ok: true; html: string } | { ok: false; reason: "upload_failed" | "unresolved" }
    > => {
      const pendingIds = listPendingInlineIds(html);
      if (pendingIds.length === 0) {
        const normalized = attachmentPreview.persistHtml(html);
        return hasUnresolvedInlineImageRefs(normalized)
          ? { ok: false, reason: "unresolved" }
          : { ok: true, html: normalized };
      }
      const mapping: Record<string, { documentId: number; ticketId: string }> = {};
      let failed = false;
      for (const pendingId of pendingIds) {
        let promise = inlineUploadsRef.current.get(pendingId);
        if (!promise) {
          const file = pendingFilesRef.current.get(pendingId);
          if (file) promise = startInlineUpload(pendingId, file);
        }
        const documentId = promise ? await promise : null;
        if (documentId != null) {
          mapping[pendingId] = { documentId, ticketId };
        } else {
          failed = true;
        }
      }
      const rewritten = attachmentPreview.persistHtml(
        rewritePendingInlineImages(html, mapping),
      );
      if (hasUnresolvedInlineImageRefs(rewritten)) {
        return { ok: false, reason: failed ? "upload_failed" : "unresolved" };
      }
      return { ok: true, html: rewritten };
    },
    [ticketId, startInlineUpload, attachmentPreview.persistHtml],
  );

  const removePendingAttachment = useCallback(
    (pendingId: string) => {
      pendingFilesRef.current.delete(pendingId);
      setPendingAttachments((current) => current.filter((item) => item.id !== pendingId));
      void persistReplyPendingFiles();
    },
    [persistReplyPendingFiles],
  );

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
      setPendingAttachments(
        rows
          .filter((row) => !isInlineImageFile(row.file))
          .map((row) => ({
            id: row.id,
            fileName: row.file.name || "anexo",
            contentType: row.file.type || null,
          })),
      );
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

  function beginClassificationEdit() {
    if (!ticket?.can_update_classification) return;
    setClassificationEditing(true);
    setErrorText(null);
    setClassificationKey(newIdempotencyKey());
    if (classificationCatalogs || classificationCatalogsLoading) return;
    setClassificationCatalogsLoading(true);
    void Promise.allSettled([
      listCategories(),
      listUrgencies(),
      listImpacts(),
      listTicketTypes(),
      listRequestTypes(),
    ])
      .then(([categories, urgencies, impacts, ticketTypes, requestTypes]) => {
        const items = (
          result: PromiseSettledResult<
            { items: { id: number; name: string }[] } | { id: number; name: string }[]
          >,
        ) => {
          if (result.status !== "fulfilled") return [];
          const value = result.value;
          return Array.isArray(value) ? value : value.items;
        };
        setClassificationCatalogs({
          categories: items(categories),
          urgencies: items(urgencies),
          impacts: items(impacts),
          ticketTypes: items(ticketTypes),
          requestTypes: items(requestTypes),
        });
      })
      .finally(() => setClassificationCatalogsLoading(false));
  }

  function cancelClassificationEdit() {
    setClassificationEditing(false);
  }

  function saveClassification(patch: ClassificationPatch) {
    if (!ticket?.can_update_classification || classificationSaving) return;
    if (!patch || Object.keys(patch).length === 0) {
      setClassificationEditing(false);
      return;
    }
    setClassificationSaving(true);
    setErrorText(null);
    void updateTicketClassification(ticketId, patch, classificationKey)
      .then(async () => {
        // Authoritative read-back — the UI never trusts the write
        // response alone; GLPI owns the final classification state
        // (priority may be recomputed by the urgency×impact matrix).
        setClassificationEditing(false);
        setClassificationKey(newIdempotencyKey());
        await load();
      })
      .catch((error) => setErrorText(messageFor(error).text))
      .finally(() => setClassificationSaving(false));
  }

  function beginFollowupEdit(message: { id: string; bodyText: string; bodyHtml?: string | null }) {
    setFollowupEditingId(message.id);
    // bodyHtml keeps inline images (`data-attachment-id`) resolvable in the editor.
    setFollowupEditContent(message.bodyHtml || message.bodyText);
    setFollowupEditError(null);
    setFollowupEditKey(newIdempotencyKey());
  }

  function cancelFollowupEdit() {
    setFollowupEditingId(null);
    setFollowupEditContent("");
    setFollowupEditError(null);
  }

  function saveFollowupEdit() {
    if (!ticket || !followupEditingId || followupEditSaving) return;
    if (!hasVisibleRichText(followupEditContent)) {
      setFollowupEditError("Escreva o novo texto do acompanhamento antes de salvar.");
      return;
    }
    if (hasUnresolvedInlineImageRefs(attachmentPreview.persistHtml(followupEditContent))) {
      setFollowupEditError(
        "Não foi possível salvar: a imagem ainda não foi anexada. Remova-a ou aguarde o envio.",
      );
      return;
    }
    setFollowupEditSaving(true);
    setFollowupEditError(null);
    void updateFollowup(
      ticketId,
      followupEditingId,
      { content: attachmentPreview.persistHtml(followupEditContent.trim()) },
      followupEditKey,
    )
      .then(() => {
        cancelFollowupEdit();
        // Authoritative re-read — only the persisted GLPI content reaches the timeline.
        load();
      })
      .catch((error) => {
        // Draft survives a recoverable failure; same idempotency key covers the retry.
        setFollowupEditError(
          messageFor(error).text || "Não foi possível salvar a edição do acompanhamento.",
        );
      })
      .finally(() => setFollowupEditSaving(false));
  }

  function runCycle(action: "accept" | "reject") {
    setCycleSaving(true);
    setErrorText(null);
    const runner =
      action === "accept"
        ? acceptTicketSolution(ticketId, cycleNote, cycleKey)
        : rejectTicketSolution(ticketId, cycleNote, cycleKey);
    void runner
      .then((result) => {
        setCycleNote("");
        setCycleKey(newIdempotencyKey());
        closeActionAfterSuccess();
        load();
        if (result.outcome !== "verified") {
          setErrorText(
            result.outcome === "status_unverified"
              ? "Ação registrada no helpdesk, mas a situação do chamado não pôde ser confirmada. Verifique o chamado antes de tentar novamente."
              : "Ação registrada no helpdesk, mas a autoria não pôde ser confirmada. Não repita a ação — o chamado já foi atualizado.",
          );
        }
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
    if (
      activeAction === "accept_solution" ||
      activeAction === "reject_solution" ||
      activeAction === "decide_validation"
    ) {
      return hasVisibleRichText(cycleNote);
    }
    if (activeAction === "submit_satisfaction") {
      return satisfactionScore !== 5 || satisfactionComment.trim().length > 0;
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

  /** Approvals surface CTA → Conversation + existing Approval Action Card host (OPS-006A). */
  function openRequestApproval() {
    setWorkspaceSurface("conversation");
    selectWorkspaceAction("request_approval");
    if (typeof window === "undefined") return;
    window.requestAnimationFrame(() => {
      const card = document.querySelector<HTMLElement>(
        '.helpdesk-action-card[data-action-variant="approval"]',
      );
      card?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      const closeOrTitle =
        card?.querySelector<HTMLElement>(".helpdesk-action-card__close") ??
        card?.querySelector<HTMLElement>(".helpdesk-action-card__title");
      closeOrTitle?.focus?.();
    });
  }

  function runValidationDecision(validationId: number, action: "accept" | "reject") {
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
  }

  const pendingValidations = (ticket?.validations ?? []).filter(
    (item) => item.mine_to_decide,
  );
  const showSatisfactionComment =
    satisfactionCommentOpen || satisfactionComment.trim().length > 0;

  function runSatisfaction() {
    setCycleSaving(true);
    setErrorText(null);
    void submitTicketSatisfaction(
      ticketId,
      { satisfaction: satisfactionScore, comment: satisfactionComment },
      cycleKey,
    )
      .then(() => {
        setSatisfactionScore(5);
        setSatisfactionComment("");
        setSatisfactionCommentOpen(false);
        setCycleKey(newIdempotencyKey());
        setActiveAction(null);
        load();
      })
      .catch((error) => setErrorText(messageFor(error).text))
      .finally(() => setCycleSaving(false));
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
    if (
      activeAction === "accept_solution" ||
      activeAction === "reject_solution" ||
      activeAction === "decide_validation"
    ) {
      setCycleNote("");
    }
    if (activeAction === "submit_satisfaction") {
      setSatisfactionScore(5);
      setSatisfactionComment("");
      setSatisfactionCommentOpen(false);
    }
    setActiveAction(null);
  }

  function closeActionAfterSuccess() {
    setActiveAction(null);
  }

  const workspaceActions = ticket ? ticketWorkspaceActions(ticket) : [];
  const selectorActions = ticketWorkspaceSelectorActions(workspaceActions);

  /**
   * Move-to-trash intent: READ → CONFIRM → DELETE → the BFF's own
   * read-back decides `deleted` — never trusting 2xx alone.
   * The ticket is re-fetched at dialog open so a state change between
   * read and confirm is re-presented before any write.
   */
  function openDeleteDialog() {
    if (!ticket || deleting || deleteChecking) return;
    setDeleteError(null);
    setDeleteChecking(true);
    void getTicket(ticketId)
      .then((fresh) => {
        setTicket(fresh);
        if (!canShowTicketDelete(fresh)) {
          setErrorText("O chamado mudou e não pode mais ser movido para a lixeira.");
          return;
        }
        setDeleteKey(newIdempotencyKey());
        setDeleteDialogOpen(true);
      })
      .catch((error) => setErrorText(messageFor(error).text))
      .finally(() => setDeleteChecking(false));
  }

  function cancelDelete() {
    if (deleting) return;
    setDeleteDialogOpen(false);
    setDeleteError(null);
  }

  function confirmDelete() {
    if (!ticket || deleting) return;
    setDeleting(true);
    setDeleteError(null);
    void deleteTicket(ticketId, deleteKey)
      .then((result) => {
        if (!ticketDeleteConfirmed(result)) {
          // 2xx without confirmed trash semantics — never claim success.
          setDeleteError(TICKET_DELETE_UNCONFIRMED_TEXT);
          return;
        }
        stageTicketDeleteNotice(ticketDeleteSuccessText(result.id || ticket.id));
        navigateHelpdesk(lastHelpdeskListPath());
      })
      .catch((error) => setDeleteError(ticketDeleteErrorText(error)))
      .finally(() => setDeleting(false));
  }
  const visibleMessages = ticket
    ? conversationMessages(ticket, new Date()).filter((message) =>
        conversationMessageVisible(message.kind, timelineVisibility),
      )
    : [];
  const unassignedDocs = useMemo(
    () =>
      ticket
        ? unassignedTicketAttachments(ticket, conversationMessages(ticket, new Date()))
        : [],
    [ticket],
  );
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
        {noticeText ? <HelpdeskStateBanner>{noticeText}</HelpdeskStateBanner> : null}
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
                  {canShowTicketDelete(ticket) ? (
                    <span className="helpdesk-ticket-summary-rail__item helpdesk-ticket-summary-rail__delete">
                      <HintAction
                        hint={helpTooltips.detailUi.deleteTicket}
                        ariaLabel="Ajuda: Excluir chamado"
                      >
                        <ActionButton
                          type="button"
                          variant="ghost"
                          className="helpdesk-ticket-delete"
                          aria-label="Excluir chamado"
                          disabled={saving || deleting || deleteChecking}
                          onClick={openDeleteDialog}
                        >
                          <Trash2 size={16} aria-hidden />
                          {deleteChecking ? "Verificando…" : "Excluir chamado"}
                        </ActionButton>
                      </HintAction>
                    </span>
                  ) : null}
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
                      <p className="helpdesk-lifecycle-cue__hint">
                        Use o menu de ações abaixo para aceitar ou recusar a solução.
                      </p>
                    ) : null}
                    {cue.showValidationActions ? (
                      <p className="helpdesk-lifecycle-cue__hint">
                        Use o menu de ações abaixo para decidir a aprovação pendente.
                      </p>
                    ) : null}
                    {cue.showSatisfactionForm ? (
                      <p className="helpdesk-lifecycle-cue__hint">
                        Use o menu de ações abaixo para avaliar o atendimento.
                      </p>
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
                  if (value === "conversation" || value === "details" || value === "approvals") {
                    setWorkspaceSurface(value);
                  }
                }}
                options={TICKET_WORKSPACE_SURFACES.map((item) => ({
                  value: item.id,
                  label: item.label,
                }))}
              />
            </div>
            <div
              className={[
                "helpdesk-ticket-workspace__body",
                workspaceSurface !== "conversation"
                  ? "helpdesk-ticket-workspace__body--no-aside"
                  : null,
              ]
                .filter(Boolean)
                .join(" ")}
            >
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
                  <TicketDetailsSurface
                    ticket={ticket}
                    assigneePick={assigneePick}
                    onAssigneeChange={setAssigneePick}
                    onAssignConfirm={assignTechnician}
                    assignSaving={assignSaving}
                    onOpenApprovals={() => setWorkspaceSurface("approvals")}
                    classificationCatalogs={classificationCatalogs}
                    classificationEditing={classificationEditing}
                    classificationSaving={
                      classificationSaving || classificationCatalogsLoading
                    }
                    onClassificationEditStart={beginClassificationEdit}
                    onClassificationEditCancel={cancelClassificationEdit}
                    onClassificationSave={saveClassification}
                  />
                ) : workspaceSurface === "approvals" ? (
                  <TicketApprovalsSurface
                    ticket={ticket}
                    cycleNote={cycleNote}
                    onCycleNoteChange={setCycleNote}
                    cycleSaving={cycleSaving}
                    onAccept={(validationId) => runValidationDecision(validationId, "accept")}
                    onReject={(validationId) => runValidationDecision(validationId, "reject")}
                    onRequestApproval={openRequestApproval}
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
                        editingId={followupEditingId}
                        renderEditSlot={() => (
                          <form
                            className="helpdesk-followup-edit"
                            aria-label="Editar acompanhamento"
                            onSubmit={(event) => {
                              event.preventDefault();
                              saveFollowupEdit();
                            }}
                          >
                            <HelpdeskRichTextField
                              label="Texto do acompanhamento"
                              value={followupEditContent}
                              onChange={setFollowupEditContent}
                              minHeight={96}
                              required
                              disabled={followupEditSaving}
                              resolveAttachmentImageSrc={resolveReplyAttachmentImageSrc}
                              persistAttachmentImageSrc={
                                attachmentPreview.persistAttachmentImageSrc
                              }
                            />
                            {followupEditError ? (
                              <p className="helpdesk-followup-edit__error" role="alert">
                                {followupEditError}
                              </p>
                            ) : null}
                            <HelpdeskFormActions>
                              <ActionButton
                                variant="primary"
                                type="submit"
                                disabled={
                                  followupEditSaving ||
                                  !hasVisibleRichText(followupEditContent)
                                }
                              >
                                {followupEditSaving ? "Salvando…" : "Salvar"}
                              </ActionButton>
                              <ActionButton
                                variant="ghost"
                                type="button"
                                disabled={followupEditSaving}
                                onClick={cancelFollowupEdit}
                              >
                                Cancelar
                              </ActionButton>
                            </HelpdeskFormActions>
                          </form>
                        )}
                        resolveActions={(message) => {
                          if (followupEditingId) return [];
                          // Follow-ups de outros autores / outros tipos de entrada
                          // não oferecem edição; a BFF segue fail-closed no GLPI.
                          if (message.kind !== "followup" || message.mine !== true) {
                            return [];
                          }
                          return [
                            {
                              id: "edit",
                              label: "Editar",
                              icon: <Pencil size={14} aria-hidden />,
                              onClick: () => beginFollowupEdit(message),
                            },
                          ];
                        }}
                      />
                      {(timelineVisibility.documents || timelineVisibility.approvals) &&
                      ((timelineVisibility.documents && unassignedDocs.length > 0) ||
                        (timelineVisibility.approvals && (ticket.validations?.length ?? 0) > 0)) ? (
                        <div className="helpdesk-timeline-extras">
                          {timelineVisibility.documents && unassignedDocs.length > 0 ? (
                            <section
                              className="helpdesk-timeline-extras__block"
                              data-action-variant="attachment"
                              aria-label="Documentos do chamado"
                            >
                              <h3 className="helpdesk-timeline-extras__title">Documentos</h3>
                              <TicketAttachmentPreview
                                ticketId={ticketId}
                                attachments={unassignedDocs}
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
                              idleLabel="Ações do chamado"
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
                                void (async () => {
                                  for (const item of pendingAttachments) {
                                    const file = pendingFilesRef.current.get(item.id);
                                    if (!file) continue;
                                    const uploaded = await uploadTicketAttachment(
                                      ticketId,
                                      file,
                                      newIdempotencyKey(),
                                    );
                                    if (attachmentAuthorDegraded(uploaded)) {
                                      setNoticeText(ATTACHMENT_AUTHOR_NOTICE_TEXT);
                                    }
                                    pendingFilesRef.current.delete(item.id);
                                  }
                                  // Inline images must resolve to persisted
                                  // document refs before the write — sending
                                  // `attachment:pending:` would lose the image.
                                  // Read the live editor DOM (paste → insert
                                  // → React state can lag one frame behind).
                                  const liveHtml =
                                    (await replyComposerRef.current?.prepareForSubmit()) ||
                                    content;
                                  const resolved = await resolveInlineUploadsForSubmit(
                                    liveHtml.trim(),
                                  );
                                  if (!resolved.ok) {
                                    throw new Error(
                                      resolved.reason === "upload_failed"
                                        ? "Não foi possível anexar uma imagem da mensagem: o envio do arquivo falhou. Remova a imagem ou tente de novo."
                                        : "Não foi possível resolver uma imagem da mensagem. Remova-a e anexe de novo.",
                                    );
                                  }
                                  const payload = attachmentPreview.persistHtml(resolved.html);
                                  return await createFollowup(
                                    ticketId,
                                    {
                                      content: payload,
                                      ...(replyMeta.requestTypeId != null
                                        ? { request_type_id: replyMeta.requestTypeId }
                                        : null),
                                    },
                                    idempotencyKey,
                                  );
                                })()
                                  .then((result) => {
                                    if (result?.outcome === "verification_failed") {
                                      // Persisted but postcondition unconfirmed —
                                      // the draft can go (a retry would only
                                      // duplicate), the warning cannot.
                                      setNoticeText(
                                        "A mensagem foi registrada, mas uma imagem não pôde ser confirmada no chamado. Verifique o acompanhamento antes de enviar de novo.",
                                      );
                                    }
                                    setContent("");
                                    setReplyMeta(EMPTY_TICKET_REPLY_META);
                                    clearReplyDraft(ticketId);
                                    pendingFilesRef.current.clear();
                                    setPendingAttachments([]);
                                    setPendingPreviewId(null);
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
                                label="Mensagem"
                                hint={helpTooltips.detailUi.actionFields.reply.message}
                                required
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
                                  const staged: HelpdeskPendingAttachmentItem[] = [];
                                  for (const file of files) {
                                    if (!isInlineImageFile(file)) {
                                      const pendingId = newIdempotencyKey();
                                      pendingFilesRef.current.set(pendingId, file);
                                      staged.push({
                                        id: pendingId,
                                        fileName: file.name || "anexo",
                                        contentType: file.type || null,
                                      });
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
                                  if (staged.length > 0) {
                                    setPendingAttachments((current) => [...current, ...staged]);
                                  }
                                  void persistReplyPendingFiles();
                                  if (pendingUploads.length > 0) {
                                    void (async () => {
                                      const mapping: Record<
                                        string,
                                        { documentId: number; ticketId: string }
                                      > = {};
                                      for (const item of pendingUploads) {
                                        const documentId = await startInlineUpload(
                                          item.pendingId,
                                          item.file,
                                        );
                                        if (documentId != null) {
                                          mapping[item.pendingId] = {
                                            documentId,
                                            ticketId,
                                          };
                                        }
                                      }
                                      if (Object.keys(mapping).length === 0) return;
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
                                    })();
                                  }
                                  return results;
                                }}
                                onUploadError={(error) => setErrorText(messageFor(error).text)}
                                pendingAttachments={pendingAttachments}
                                onPendingAttachmentOpen={(id) => setPendingPreviewId(id)}
                                onPendingAttachmentRemove={removePendingAttachment}
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
                              <HelpdeskRichTextField
                                label="Comentário (opcional)"
                                value={cycleNote}
                                onChange={setCycleNote}
                                disabled={cycleSaving}
                                minHeight={120}
                              />
                            </TicketActionCard>
                          ) : null}
                          {activeAction === "decide_validation" ? (
                            <TicketActionCard
                              actionId="decide_validation"
                              disabled={cycleSaving}
                              onCancel={cancelActiveActionForm}
                            >
                              {pendingValidations.length === 0 ? (
                                <p className="helpdesk-action-fields__hint">
                                  Nenhuma aprovação pendente para você neste chamado.
                                </p>
                              ) : (
                                <div className="helpdesk-lifecycle-actions">
                                  <HelpdeskRichTextField
                                    label="Comentário (opcional)"
                                    value={cycleNote}
                                    onChange={setCycleNote}
                                    disabled={cycleSaving}
                                    minHeight={96}
                                  />
                                  {pendingValidations.map((item) => (
                                    <div
                                      key={item.id}
                                      className="helpdesk-lifecycle-validation"
                                    >
                                      {item.submission_comment ? (
                                        <p className="helpdesk-lifecycle-cue__text">
                                          {item.submission_comment}
                                        </p>
                                      ) : null}
                                      <div className="helpdesk-lifecycle-actions__buttons">
                                        <HintAction
                                          hint={helpTooltips.detailUi.acceptValidation}
                                          ariaLabel="Ajuda: Aceitar aprovação"
                                        >
                                          <ActionButton
                                            variant="primary"
                                            type="button"
                                            disabled={cycleSaving}
                                            onClick={() =>
                                              runValidationDecision(item.id, "accept")
                                            }
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
                                            onClick={() =>
                                              runValidationDecision(item.id, "reject")
                                            }
                                          >
                                            Recusar aprovação
                                          </ActionButton>
                                        </HintAction>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </TicketActionCard>
                          ) : null}
                          {activeAction === "submit_satisfaction" ? (
                            <TicketActionCard
                              actionId="submit_satisfaction"
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
                                      {cycleSaving
                                        ? ticketActionPresentation("submit_satisfaction")
                                            .submittingLabel
                                        : ticketActionPresentation("submit_satisfaction")
                                            .submitLabel}
                                    </ActionButton>
                                  </HintAction>
                                </HelpdeskFormActions>
                              }
                            >
                              <div
                                className="helpdesk-satisfaction"
                                role="group"
                                aria-label="Avaliação do atendimento"
                              >
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
                                          selected
                                            ? "helpdesk-satisfaction__score--selected"
                                            : null,
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
                                    <HelpdeskTextArea
                                      className="helpdesk-satisfaction__comment"
                                      label="Comentário (opcional)"
                                      value={satisfactionComment}
                                      onChange={setSatisfactionComment}
                                      disabled={cycleSaving}
                                      maxLength={2000}
                                      rows={2}
                                    />
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
                                </div>
                              </div>
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
                                  label="Descrição da solução"
                                  hint={helpTooltips.detailUi.actionFields.solution.description}
                                  required
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
                                  label="Descrição da tarefa"
                                  hint={helpTooltips.detailUi.actionFields.task.description}
                                  required
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
                                groupRequiredHint={
                                  approvalApproverType === "group" &&
                                  (approvalGroupId == null || approvalGroupId <= 0)
                                    ? "Selecione um grupo para continuar."
                                    : null
                                }
                              />
                              {approvalApproverType === "user" ? (
                                <div className="helpdesk-ticket-workspace__approval-approver">
                                  <HelpdeskAssigneePicker
                                    label="Aprovador"
                                    hint={helpTooltips.detailUi.actionFields.approval.approver}
                                    value={approverPick}
                                    onChange={setApproverPick}
                                    disabled={saving}
                                    purpose="mention"
                                    placeholder="Buscar usuário…"
                                    emptyLabel="Nenhum usuário selecionado"
                                  />
                                  {!approverPick?.id ? (
                                    <p className="helpdesk-action-fields__hint" role="status">
                                      Selecione um usuário para continuar.
                                    </p>
                                  ) : null}
                                </div>
                              ) : null}
                              <HelpdeskRichTextField
                                label="Comentário para aprovação (opcional)"
                                hint={helpTooltips.detailUi.actionFields.approval.message}
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
                                    setDocumentFiles((current) => [
                                      ...current,
                                      ...Array.from(event.target.files || []),
                                    ]);
                                    event.target.value = "";
                                  }}
                                />
                                <label className="helpdesk-action-fields__field">
                                  <FieldLabel
                                    label="Título (opcional)"
                                    hint={helpTooltips.detailUi.actionFields.attachment.title}
                                  />
                                  <input
                                    type="text"
                                    value={documentTitle}
                                    disabled={saving}
                                    placeholder="Deixe vazio para usar o nome do arquivo"
                                    onChange={(event) => setDocumentTitle(event.target.value)}
                                  />
                                </label>
                                <div className="helpdesk-action-fields__field">
                                  <span className="helpdesk-field__label-row">
                                    <FieldLabel
                                      label="Arquivos"
                                      hint={helpTooltips.detailUi.actionFields.attachment.files}
                                    />
                                    <span className="helpdesk-field__required"> *</span>
                                  </span>
                                  {documentFiles.length > 0 ? (
                                    <ul className="helpdesk-ticket-workspace__document-list">
                                      {documentFiles.map((file, index) => (
                                        <li key={`${file.name}-${file.size}-${file.lastModified}-${index}`}>
                                          <span>
                                            {file.name}
                                            {file.size > 0
                                              ? ` (${formatAttachmentBytes(file.size)})`
                                              : ""}
                                          </span>
                                          <button
                                            type="button"
                                            className="helpdesk-ticket-workspace__document-remove"
                                            disabled={saving}
                                            aria-label={`Remover ${file.name}`}
                                            onClick={() =>
                                              setDocumentFiles((current) =>
                                                current.filter((_, itemIndex) => itemIndex !== index),
                                              )
                                            }
                                          >
                                            Remover
                                          </button>
                                        </li>
                                      ))}
                                    </ul>
                                  ) : (
                                    <p className="helpdesk-action-fields__hint" role="status">
                                      Nenhum arquivo selecionado. Selecione ao menos um arquivo.
                                    </p>
                                  )}
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
                                            const uploaded = await uploadTicketAttachment(
                                              ticketId,
                                              file,
                                              newIdempotencyKey(),
                                              title ? { title } : undefined,
                                            );
                                            if (attachmentAuthorDegraded(uploaded)) {
                                              setNoticeText(ATTACHMENT_AUTHOR_NOTICE_TEXT);
                                            }
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
              {workspaceSurface === "conversation" ? (
                <div className="helpdesk-ticket-workspace__aside">
                  <TicketContextPanel
                    ticket={ticket}
                    assigneePick={assigneePick}
                    onAssigneeChange={setAssigneePick}
                    onAssignConfirm={assignTechnician}
                    assignSaving={assignSaving}
                  />
                </div>
              ) : null}
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
            <FilePreviewModal
              open={pendingPreviewId !== null}
              title="Anexo"
              fileName={pendingPreview?.fileName || "anexo"}
              mimeType={pendingPreview?.contentType || "application/octet-stream"}
              source={
                pendingPreviewId
                  ? () =>
                      Promise.resolve(
                        pendingFilesRef.current.get(pendingPreviewId) as Blob,
                      )
                  : null
              }
              portalScopeClassName="dashboard-helpdesk"
              onClose={() => setPendingPreviewId(null)}
            />
            <HelpdeskConfirmModal
              open={deleteDialogOpen && Boolean(ticket)}
              title={`Excluir chamado #${ticket?.id ?? ticketId}`}
              message={
                <span className="helpdesk-ticket-delete-modal">
                  <span className="helpdesk-ticket-delete-modal__summary">
                    <strong>{ticket?.title || "Chamado"}</strong>
                    {ticket?.status ? <span> · {ticket.status}</span> : null}
                  </span>
                  <span className="helpdesk-ticket-delete-modal__hint">
                    O chamado será movido para a lixeira do helpdesk e sairá da sua
                    lista ativa. Isso não é uma exclusão permanente — ele continua
                    recuperável dentro do GLPI.
                  </span>
                  {deleteError ? (
                    <span className="helpdesk-ticket-delete-modal__error" role="alert">
                      {deleteError}
                    </span>
                  ) : null}
                </span>
              }
              confirmLabel="Mover para a lixeira"
              busy={deleting}
              busyLabel="Movendo…"
              variant="danger"
              onConfirm={confirmDelete}
              onCancel={cancelDelete}
            />
          </>
        ) : null}
      </div>
    </HelpdeskPageStack>
  );
}
