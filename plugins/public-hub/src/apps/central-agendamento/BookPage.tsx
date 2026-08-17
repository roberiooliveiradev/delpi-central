import { useEffect, useMemo, useState } from "react";

import {
  fetchPublicAvailability,
  submitPublicBooking,
  type BusySlot,
  type PublicSchedulingResource,
} from "./api";
import "./book.css";

type Phase = "form" | "submitting" | "done" | "error";

type Props = {
  token: string;
  resource: PublicSchedulingResource;
};

function toLocalInputValue(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function startOfTodayLocal(): Date {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

function formatSlot(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function branchLabel(code: string): string {
  return code === "SC" ? "Santa Catarina" : code === "ES" ? "Espírito Santo" : code;
}

export function PublicBookingForm({ token, resource }: Props) {
  const defaultStart = useMemo(() => {
    const d = new Date();
    d.setMinutes(0, 0, 0);
    d.setHours(d.getHours() + 1);
    return d;
  }, []);
  const defaultEnd = useMemo(() => {
    const d = new Date(defaultStart);
    d.setHours(d.getHours() + 1);
    return d;
  }, [defaultStart]);

  const [requesterName, setRequesterName] = useState("");
  const [requesterEmail, setRequesterEmail] = useState("");
  const [requesterPhone, setRequesterPhone] = useState("");
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [startLocal, setStartLocal] = useState(toLocalInputValue(defaultStart));
  const [endLocal, setEndLocal] = useState(toLocalInputValue(defaultEnd));
  const [honeypot, setHoneypot] = useState("");
  const [busy, setBusy] = useState<BusySlot[]>([]);
  const [phase, setPhase] = useState<Phase>("form");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const from = startOfTodayLocal();
    const to = new Date(from);
    to.setDate(to.getDate() + 45);
    void (async () => {
      try {
        const slots = await fetchPublicAvailability(token, from, to);
        if (!cancelled) setBusy(slots);
      } catch {
        if (!cancelled) setBusy([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const upcomingBusy = useMemo(
    () =>
      busy
        .filter((slot) => new Date(slot.end_at).getTime() >= Date.now())
        .slice(0, 12),
    [busy],
  );

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    const start = new Date(startLocal);
    const end = new Date(endLocal);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      setError("Informe data e horário válidos.");
      return;
    }
    if (end <= start) {
      setError("O término deve ser posterior ao início.");
      return;
    }
    if (!requesterName.trim() || !requesterEmail.trim() || !title.trim()) {
      setError("Preencha nome, e-mail e motivo do agendamento.");
      return;
    }

    setPhase("submitting");
    try {
      await submitPublicBooking(token, {
        requester_name: requesterName.trim(),
        requester_email: requesterEmail.trim(),
        requester_phone: requesterPhone.trim() || undefined,
        title: title.trim(),
        notes: notes.trim() || undefined,
        start_at: start.toISOString(),
        end_at: end.toISOString(),
        website: honeypot || undefined,
      });
      setPhase("done");
    } catch (err) {
      setPhase("form");
      setError(err instanceof Error ? err.message : "Não foi possível enviar a solicitação.");
    }
  }

  if (phase === "done") {
    return (
      <div className="ca-pub">
        <header className="ca-pub__header">
          <p className="ca-pub__eyebrow">Central de Agendamento</p>
          <h1>Solicitação enviada</h1>
          <p className="ca-pub__lead">
            Sua reserva de <strong>{resource.name}</strong> foi registrada e aguarda
            aprovação. Você será contatado pelo e-mail informado se necessário.
          </p>
        </header>
        <p className="ca-pub__success">Obrigado. Pode fechar esta página.</p>
      </div>
    );
  }

  return (
    <div className="ca-pub">
      <header className="ca-pub__header">
        <p className="ca-pub__eyebrow">Central de Agendamento · {branchLabel(resource.branch_code)}</p>
        <h1>{resource.name}</h1>
        <p className="ca-pub__lead">
          {resource.description?.trim() ||
            "Solicite um horário. A reserva fica pendente até a aprovação da equipe."}
        </p>
        {resource.capacity ? (
          <p className="ca-pub__meta">Capacidade: {resource.capacity}</p>
        ) : null}
      </header>

      {upcomingBusy.length > 0 ? (
        <section className="ca-pub__busy" aria-label="Horários ocupados">
          <h2>Horários já reservados ou pendentes</h2>
          <ul>
            {upcomingBusy.map((slot) => (
              <li key={`${slot.start_at}-${slot.end_at}`}>
                {formatSlot(slot.start_at)} — {formatSlot(slot.end_at)}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <form className="ca-pub__form" onSubmit={(event) => void handleSubmit(event)}>
        <label className="ca-pub__label" htmlFor="ca-pub-name">
          Seu nome
        </label>
        <input
          id="ca-pub-name"
          className="ca-pub__input"
          value={requesterName}
          onChange={(e) => setRequesterName(e.target.value)}
          required
          autoComplete="name"
        />

        <label className="ca-pub__label" htmlFor="ca-pub-email">
          E-mail
        </label>
        <input
          id="ca-pub-email"
          type="email"
          className="ca-pub__input"
          value={requesterEmail}
          onChange={(e) => setRequesterEmail(e.target.value)}
          required
          autoComplete="email"
        />

        <label className="ca-pub__label" htmlFor="ca-pub-phone">
          Telefone (opcional)
        </label>
        <input
          id="ca-pub-phone"
          className="ca-pub__input"
          value={requesterPhone}
          onChange={(e) => setRequesterPhone(e.target.value)}
          autoComplete="tel"
        />

        <label className="ca-pub__label" htmlFor="ca-pub-title">
          Motivo / título
        </label>
        <input
          id="ca-pub-title"
          className="ca-pub__input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          placeholder="Ex.: Reunião de equipe"
        />

        <div className="ca-pub__row">
          <div>
            <label className="ca-pub__label" htmlFor="ca-pub-start">
              Início
            </label>
            <input
              id="ca-pub-start"
              type="datetime-local"
              className="ca-pub__input"
              value={startLocal}
              onChange={(e) => setStartLocal(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="ca-pub__label" htmlFor="ca-pub-end">
              Término
            </label>
            <input
              id="ca-pub-end"
              type="datetime-local"
              className="ca-pub__input"
              value={endLocal}
              onChange={(e) => setEndLocal(e.target.value)}
              required
            />
          </div>
        </div>

        <label className="ca-pub__label" htmlFor="ca-pub-notes">
          Observações (opcional)
        </label>
        <textarea
          id="ca-pub-notes"
          className="ca-pub__textarea"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
        />

        <div className="ca-pub__hp" aria-hidden="true">
          <label htmlFor="ca-pub-website">Website</label>
          <input
            id="ca-pub-website"
            tabIndex={-1}
            autoComplete="off"
            value={honeypot}
            onChange={(e) => setHoneypot(e.target.value)}
          />
        </div>

        {error ? <p className="ca-pub__error">{error}</p> : null}

        <button
          type="submit"
          className="ca-pub__submit"
          disabled={phase === "submitting"}
        >
          {phase === "submitting" ? "Enviando..." : "Solicitar agendamento"}
        </button>
      </form>
    </div>
  );
}
