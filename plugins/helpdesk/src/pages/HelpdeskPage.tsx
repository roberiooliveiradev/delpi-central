import { useEffect, useState, type ReactNode } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";
import { ChevronLeft, ChevronRight, FilterX, Plus, Send } from "lucide-react";

import {
  HelpdeskApiError,
  beginGlpiLink,
  createFollowup,
  createTicket,
  getTicket,
  listCategories,
  listTickets,
  listUrgencies,
  type TicketDetail,
  type TicketSummary,
} from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
import {
  conversationAuthorSrc,
  conversationMessages,
  detailRecordHeading,
  isTicketFilterActive,
  newIdempotencyKey,
  parseTicketListFilters,
  statusBadgeVariant,
  nextTicketSort,
  parseTicketSort,
  ticketListSearch,
  TICKET_STATUS_FILTERS,
  type TicketListFilters,
  viewForTicketLoad,
} from "../presentation/ticketView";
import { navigateHelpdesk, type HelpdeskRoute } from "../routing/helpdeskRoute";
import { useMyPersonProfilePhoto } from "../presentation/useMyPersonProfilePhoto";
import { TicketAttachmentPreview } from "./TicketAttachmentPreview";
import { TicketListTable } from "./TicketListTable";
import {
  HelpdeskEmptyState,
  HelpdeskFilterInput,
  HelpdeskFilterSelect,
  HelpdeskFiltersRow,
  HelpdeskFormActions,
  HelpdeskIconButton,
  HelpdeskLoadingState,
  HelpdeskMessageThread,
  HelpdeskPageHeader,
  HelpdeskRecordCard,
  HelpdeskSectionCard,
  HelpdeskSelect,
  HelpdeskStateBanner,
  HelpdeskStatusBadge,
  HelpdeskTextArea,
  HelpdeskTextField,
} from "../ui/helpdeskUi";

const MESSAGES: Record<string, string> = {
  forbidden: "Você não tem permissão para Meus Chamados de TI.",
  glpi_forbidden: "O helpdesk recusou este chamado para o seu usuário.",
  glpi_unavailable: "O helpdesk está indisponível. Tente novamente em instantes.",
  not_found: "Este chamado não está disponível para você.",
  validation_error: "Revise os campos e envie de novo.",
  idempotency_key_required: "Não foi possível confirmar o envio. Atualize a página e tente outra vez.",
  catalog_unavailable: "Não foi possível carregar as categorias do helpdesk.",
};

function messageFor(error: unknown): { code: string; text: string } {
  if (error instanceof HelpdeskApiError) {
    return { code: error.code, text: MESSAGES[error.code] || "Não foi possível concluir a operação." };
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

function HelpdeskBackButton() {
  return (
    <HelpdeskIconButton aria-label="Voltar" onClick={() => navigateHelpdesk("/apps/helpdesk")}>
      <ChevronLeft size={16} aria-hidden />
    </HelpdeskIconButton>
  );
}

function currentListFilters(): TicketListFilters {
  return parseTicketListFilters(typeof window === "undefined" ? "" : window.location.search);
}

function writeListFilters(filters: TicketListFilters) {
  window.history.replaceState({}, "", `/apps/helpdesk${ticketListSearch(filters)}`);
}

function TicketListPage() {
  const [filters, setFilters] = useState(currentListFilters);
  const [qDraft, setQDraft] = useState(filters.q);
  const [items, setItems] = useState<TicketSummary[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const [urgencies, setUrgencies] = useState<{ id: number; name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [linking, setLinking] = useState(false);

  function commitFilters(next: TicketListFilters) {
    setFilters(next);
    writeListFilters(next);
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
        sort: next.sort || undefined,
        page: next.page,
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
    const timer = window.setTimeout(() => {
      if (qDraft === filters.q) return;
      commitFilters({ ...filters, q: qDraft, page: 1 });
    }, 400);
    return () => window.clearTimeout(timer);
  }, [filters, qDraft]);

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
      const next = currentListFilters();
      setFilters(next);
      setQDraft(next.q);
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

  return (
    <HelpdeskPageStack>
      <HelpdeskPageHeader
        title="Meus Chamados de TI"
        subtitle="Chamados no seu nome"
        compact
        onRefresh={() => void load(filters)}
        refreshing={loading}
      />
      <HelpdeskSectionCard
        title="Meus chamados"
        hint={helpTooltips.list}
        fill
        actions={
          <HelpdeskIconButton
            tone="primary"
            aria-label="Abrir chamado"
            onClick={() => navigateHelpdesk("/apps/helpdesk/tickets/new")}
          >
            <Plus size={16} aria-hidden />
          </HelpdeskIconButton>
        }
      >
        {view === "link" ? null : (
          <HelpdeskFiltersRow compact variant="extended" trailing={
            filterActive ? (
              <HelpdeskIconButton
                aria-label="Limpar filtros"
                onClick={() => {
                  const next = { ...currentListFilters(), q: "", status: "", urgency_id: "", category_id: "", updated_from: "", updated_to: "", page: 1, sort: filters.sort };
                  setQDraft("");
                  commitFilters(next);
                }}
              >
                <FilterX size={16} aria-hidden />
              </HelpdeskIconButton>
            ) : null
          }>
            <HelpdeskFilterInput
              label="Buscar"
              type="search"
              value={qDraft}
              onChange={setQDraft}
              placeholder="Título do chamado"
            />
            <HelpdeskFilterSelect
              label="Status"
              value={filters.status}
              onChange={(status) => commitFilters({ ...filters, status, page: 1 })}
              options={[...TICKET_STATUS_FILTERS]}
            />
            <HelpdeskFilterSelect
              label="Urgência"
              value={filters.urgency_id}
              onChange={(urgency_id) => commitFilters({ ...filters, urgency_id, page: 1 })}
              options={[{ value: "", label: "Todas" }, ...urgencies.map((item) => ({ value: String(item.id), label: item.name }))]}
            />
            <HelpdeskFilterSelect
              label="Categoria"
              value={filters.category_id}
              onChange={(category_id) => commitFilters({ ...filters, category_id, page: 1 })}
              options={[{ value: "", label: "Todas" }, ...categories.map((item) => ({ value: String(item.id), label: item.name }))]}
            />
            <HelpdeskFilterInput
              label="Atualizado de"
              type="date"
              value={filters.updated_from}
              onChange={(updated_from) => commitFilters({ ...filters, updated_from, page: 1 })}
            />
            <HelpdeskFilterInput
              label="Atualizado até"
              type="date"
              value={filters.updated_to}
              onChange={(updated_to) => commitFilters({ ...filters, updated_to, page: 1 })}
            />
          </HelpdeskFiltersRow>
        )}
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
          <TicketListTable
            items={items}
            loading={loading}
            sort={parseTicketSort(filters.sort)}
            onSortChange={(columnKey) =>
              commitFilters({ ...filters, sort: nextTicketSort(filters.sort, columnKey), page: 1 })
            }
            onOpen={(ticketId) => navigateHelpdesk(`/apps/helpdesk/tickets/${ticketId}`)}
          />
        ) : null}
        {view === "list" || (view === "empty" && filters.page > 1) ? (
          <HelpdeskFormActions>
            <HelpdeskIconButton
              aria-label="Página anterior"
              disabled={filters.page <= 1 || loading}
              onClick={() => commitFilters({ ...filters, page: Math.max(1, filters.page - 1) })}
            >
              <ChevronLeft size={16} aria-hidden />
            </HelpdeskIconButton>
            <span>{filters.page}</span>
            <HelpdeskIconButton
              aria-label="Próxima página"
              disabled={!hasMore || loading}
              onClick={() => commitFilters({ ...filters, page: filters.page + 1 })}
            >
              <ChevronRight size={16} aria-hidden />
            </HelpdeskIconButton>
          </HelpdeskFormActions>
        ) : null}
      </HelpdeskSectionCard>
    </HelpdeskPageStack>
  );
}

function CreateTicketPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [urgencyId, setUrgencyId] = useState("");
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const [urgencies, setUrgencies] = useState<{ id: number; name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [idempotencyKey] = useState(newIdempotencyKey);

  useEffect(() => {
    const controller = new AbortController();
    void Promise.allSettled([listCategories(controller.signal), listUrgencies(controller.signal)])
      .then(([categoryResult, urgencyResult]) => {
        if (controller.signal.aborted) return;
        if (urgencyResult.status === "fulfilled") {
          setUrgencies(urgencyResult.value.items);
          setUrgencyId(urgencyResult.value.items[0] ? String(urgencyResult.value.items[0].id) : "");
        }
        if (categoryResult.status === "fulfilled") {
          setCategories(categoryResult.value.items);
          setCategoryId(categoryResult.value.items[0] ? String(categoryResult.value.items[0].id) : "");
          return;
        }
        setErrorText(MESSAGES.catalog_unavailable);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  return (
    <HelpdeskPageStack>
    <HelpdeskPageHeader title="Abrir chamado" compact nav={<HelpdeskBackButton />} />
    <HelpdeskSectionCard title="Abrir chamado" hint={helpTooltips.create} fill>
      {loading ? <HelpdeskLoadingState message="Carregando categorias…" /> : null}
      {errorText ? <HelpdeskStateBanner variant="error">{errorText}</HelpdeskStateBanner> : null}
      <form
        className="helpdesk-create-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (saving) return;
          setSaving(true);
          setErrorText(null);
          void createTicket(
            {
              title: title.trim(),
              description: description.trim(),
              category_id: Number(categoryId),
              urgency_id: Number(urgencyId),
            },
            idempotencyKey,
          )
            .then((created) => navigateHelpdesk(`/apps/helpdesk/tickets/${created.id}`))
            .catch((error) => {
              setErrorText(messageFor(error).text);
              setSaving(false);
            });
        }}
      >
        <div className="helpdesk-create-layout">
          <div className="helpdesk-create-layout__main">
            <HelpdeskTextField label="Título" hint={helpTooltips.create} value={title} onChange={setTitle} required />
            <HelpdeskTextArea
              label="Descrição"
              value={description}
              onChange={setDescription}
              required
              rows={12}
            />
          </div>
          <aside className="helpdesk-create-layout__aside" aria-label="Classificação do chamado">
            <HelpdeskSelect
              label="Categoria"
              value={categoryId}
              onChange={setCategoryId}
              required
              searchable
              options={categories.map((item) => ({ value: String(item.id), label: item.name }))}
            />
            <HelpdeskSelect
              label="Urgência"
              value={urgencyId}
              onChange={setUrgencyId}
              required
              options={urgencies.map((item) => ({ value: String(item.id), label: item.name }))}
            />
          </aside>
        </div>
        <HelpdeskFormActions>
          <HelpdeskIconButton
            tone="primary"
            type="submit"
            aria-label={saving ? "Enviando" : "Enviar chamado"}
            disabled={saving || loading}
          >
            <Send size={16} aria-hidden />
          </HelpdeskIconButton>
        </HelpdeskFormActions>
      </form>
    </HelpdeskSectionCard>
    </HelpdeskPageStack>
  );
}

function TicketDetailPage({ ticketId }: { ticketId: string }) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const myPhotoUrl = useMyPersonProfilePhoto();

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
        nav={<HelpdeskBackButton />}
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
              subtitle={[`#${ticket.id}`, ticket.assigned_display_name].filter(Boolean).join(" · ")}
              status={<HelpdeskStatusBadge label={ticket.status} variant={statusBadgeVariant(ticket.status)} />}
            />
            <HelpdeskMessageThread
              listAriaLabel="Conversa do chamado"
              emptyLabel="Nenhuma mensagem"
              messages={conversationMessages(ticket, new Date()).map((message) => ({
                id: message.id,
                kind: message.kind,
                headingText: message.headingText || undefined,
                bodyText: message.bodyText,
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
            <form
              onSubmit={(event) => {
                event.preventDefault();
                if (saving || !content.trim()) return;
                setSaving(true);
                void createFollowup(ticketId, content.trim(), idempotencyKey)
                  .then(() => {
                    setContent("");
                    setIdempotencyKey(newIdempotencyKey());
                    load();
                  })
                  .catch((error) => setErrorText(messageFor(error).text))
                  .finally(() => setSaving(false));
              }}
            >
              <HelpdeskTextArea
                label="Responder"
                value={content}
                onChange={setContent}
                rows={3}
                required
              />
              <HelpdeskFormActions>
                <HelpdeskIconButton
                  tone="primary"
                  type="submit"
                  aria-label={saving ? "Enviando" : "Enviar"}
                  disabled={saving}
                >
                  <Send size={16} aria-hidden />
                </HelpdeskIconButton>
              </HelpdeskFormActions>
            </form>
          </>
        ) : null}
      </HelpdeskSectionCard>
    </HelpdeskPageStack>
  );
}
