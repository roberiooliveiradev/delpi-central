import { useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

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
import { newIdempotencyKey, viewForTicketLoad } from "../presentation/ticketView";
import { navigateHelpdesk, type HelpdeskRoute } from "../routing/helpdeskRoute";
import {
  HelpdeskEmptyState,
  HelpdeskFormActions,
  HelpdeskLoadingState,
  HelpdeskPageHeader,
  HelpdeskSectionCard,
  HelpdeskStateBanner,
  HelpdeskTimeline,
} from "../ui/helpdeskUi";

const MESSAGES: Record<string, string> = {
  forbidden: "Você não tem permissão para Meus Chamados de TI.",
  glpi_forbidden: "O helpdesk recusou este chamado para o seu usuário.",
  glpi_unavailable: "O helpdesk está indisponível. Tente novamente em instantes.",
  not_found: "Este chamado não está disponível para você.",
  validation_error: "Revise os campos e envie de novo.",
  idempotency_key_required: "Não foi possível confirmar o envio. Atualize a página e tente outra vez.",
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

function TicketListPage() {
  const [items, setItems] = useState<TicketSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [linking, setLinking] = useState(false);

  async function load() {
    setLoading(true);
    setErrorCode(null);
    setErrorText(null);
    try {
      const body = await listTickets();
      setItems(body.items);
    } catch (error) {
      const mapped = messageFor(error);
      setItems([]);
      setErrorCode(mapped.code);
      setErrorText(mapped.text);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const view = viewForTicketLoad({ loading, errorCode, itemCount: items.length });

  return (
    <>
      <HelpdeskPageHeader title="Meus Chamados de TI" subtitle="Chamados abertos no seu nome" onRefresh={() => void load()} refreshing={loading} />
      <HelpdeskSectionCard title="Meus chamados" hint={helpTooltips.list} actions={<ActionButton variant="primary" onClick={() => navigateHelpdesk("/apps/helpdesk/tickets/new")}>Abrir chamado</ActionButton>}>
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
        {view === "empty" ? <HelpdeskEmptyState /> : null}
        {view === "list" ? (
          <ul className="helpdesk-list">
            {items.map((item) => (
              <li key={item.id}>
                <button type="button" onClick={() => navigateHelpdesk(`/apps/helpdesk/tickets/${item.id}`)}>
                  <strong>{item.title}</strong>
                  <div className="helpdesk-meta">
                    {item.status} · {item.category} · {item.urgency}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </HelpdeskSectionCard>
    </>
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
    void Promise.all([listCategories(controller.signal), listUrgencies(controller.signal)])
      .then(([categoryBody, urgencyBody]) => {
        setCategories(categoryBody.items);
        setUrgencies(urgencyBody.items);
        setCategoryId(categoryBody.items[0] ? String(categoryBody.items[0].id) : "");
        setUrgencyId(urgencyBody.items[0] ? String(urgencyBody.items[0].id) : "");
      })
      .catch((error) => {
        if (!controller.signal.aborted) setErrorText(messageFor(error).text);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  return (
    <HelpdeskSectionCard title="Abrir chamado" hint={helpTooltips.create}>
      {loading ? <HelpdeskLoadingState message="Carregando categorias…" /> : null}
      {errorText ? <HelpdeskStateBanner variant="error">{errorText}</HelpdeskStateBanner> : null}
      <form
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
        <label>
          Título
          <input value={title} onChange={(event) => setTitle(event.target.value)} required />
        </label>
        <label>
          Descrição
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} required />
        </label>
        <label>
          Categoria
          <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)} required>
            {categories.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Urgência
          <select value={urgencyId} onChange={(event) => setUrgencyId(event.target.value)} required>
            {urgencies.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <HelpdeskFormActions>
          <ActionButton type="button" onClick={() => navigateHelpdesk("/apps/helpdesk")}>
            Voltar
          </ActionButton>
          <ActionButton variant="primary" type="submit" disabled={saving || loading}>
            {saving ? "Enviando…" : "Enviar chamado"}
          </ActionButton>
        </HelpdeskFormActions>
      </form>
    </HelpdeskSectionCard>
  );
}

function TicketDetailPage({ ticketId }: { ticketId: string }) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);

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
    <>
      <HelpdeskPageHeader title={ticket?.title || "Chamado"} onRefresh={load} refreshing={loading} />
      <HelpdeskSectionCard title="Detalhe" hint={helpTooltips.detail}>
        {loading ? <HelpdeskLoadingState message="Carregando chamado…" /> : null}
        {errorText ? <HelpdeskStateBanner variant="error">{errorText}</HelpdeskStateBanner> : null}
        {ticket ? (
          <>
            <p className="helpdesk-meta">
              {ticket.status} · {ticket.category} · {ticket.urgency}
            </p>
            <p>{ticket.description}</p>
            <HelpdeskTimeline
              items={ticket.timeline.map((entry) => ({
                id: String(entry.id),
                title: entry.author_display_name || "Acompanhamento",
                timeLabel: entry.created_at,
                detail: entry.content,
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
              <label>
                Acompanhamento
                <textarea value={content} onChange={(event) => setContent(event.target.value)} required />
              </label>
              <HelpdeskFormActions>
                <ActionButton type="button" onClick={() => navigateHelpdesk("/apps/helpdesk")}>
                  Voltar
                </ActionButton>
                <ActionButton variant="primary" type="submit" disabled={saving}>
                  {saving ? "Enviando…" : "Registrar acompanhamento"}
                </ActionButton>
              </HelpdeskFormActions>
            </form>
          </>
        ) : null}
      </HelpdeskSectionCard>
    </>
  );
}
