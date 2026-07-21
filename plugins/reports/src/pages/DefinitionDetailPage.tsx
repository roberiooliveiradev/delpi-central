import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  CalendarClock,
  History,
  Mail,
  RefreshCw,
  Save,
  Send,
  Settings2,
  Users,
} from "lucide-react";
import { UserDirectoryPicker } from "@delpi/plugin-ui/index";

import {
  getReportDefinition,
  getReportSchedule,
  listReportRecipients,
  listReportRuns,
  replaceReportRecipients,
  runReportDefinition,
  searchDirectoryUsers,
  updateReportDefinition,
  upsertReportSchedule,
} from "../api/reportsApi";
import type {
  DirectoryUser,
  ReportDefinition,
  ReportRun,
  ReportSchedule,
} from "../types/reports";
import {
  formatBranchUnitLabel,
  formatDateTimeBr,
  formatRunStatusLabel,
  formatTriggerLabel,
} from "../utils/format";
import { REPORTS_LIST_PATH } from "../utils/route";

type Props = {
  definitionId: string;
};

const WEEKDAY_OPTIONS = [
  { value: 0, label: "Segunda" },
  { value: 1, label: "Terça" },
  { value: 2, label: "Quarta" },
  { value: 3, label: "Quinta" },
  { value: 4, label: "Sexta" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
];

function runStatusClass(status: string): string {
  if (status === "succeeded") return "rp-pill rp-pill--success";
  if (status === "failed") return "rp-pill rp-pill--danger";
  if (status === "running") return "rp-pill rp-pill--info";
  return "rp-pill rp-pill--muted";
}

export function DefinitionDetailPage({ definitionId }: Props) {
  const [item, setItem] = useState<ReportDefinition | null>(null);
  const [recipients, setRecipients] = useState<DirectoryUser[]>([]);
  const [schedule, setSchedule] = useState<ReportSchedule | null>(null);
  const [runs, setRuns] = useState<ReportRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [name, setName] = useState("");
  const [branch, setBranch] = useState("01");
  const [horizonDays, setHorizonDays] = useState(30);
  const [active, setActive] = useState(true);

  const [scheduleKind, setScheduleKind] = useState<"daily" | "weekly">("daily");
  const [hour, setHour] = useState(8);
  const [minute, setMinute] = useState(0);
  const [weekday, setWeekday] = useState(0);
  const [scheduleEnabled, setScheduleEnabled] = useState(true);

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const [definition, recipientsPayload, schedulePayload, runsPayload] =
          await Promise.all([
            getReportDefinition(definitionId, signal),
            listReportRecipients(definitionId, signal),
            getReportSchedule(definitionId, signal),
            listReportRuns(definitionId, signal),
          ]);
        if (signal?.aborted) return;
        setItem(definition);
        setName(definition.name);
        setBranch(String(definition.params.branch ?? "01"));
        setHorizonDays(Number(definition.params.horizonDays ?? 30));
        setActive(definition.active);
        setRecipients(
          recipientsPayload.items.map((r) => ({
            id: r.userId,
            name: r.email,
            email: r.email,
          })),
        );
        setSchedule(schedulePayload);
        if (schedulePayload) {
          setScheduleKind(
            schedulePayload.scheduleKind === "weekly" ? "weekly" : "daily",
          );
          setHour(schedulePayload.hour ?? 8);
          setMinute(schedulePayload.minute ?? 0);
          setWeekday(schedulePayload.weekday ?? 0);
          setScheduleEnabled(schedulePayload.enabled);
        }
        setRuns(runsPayload.items);
      } catch (err) {
        if (signal?.aborted) return;
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar a definição.",
        );
        setItem(null);
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [definitionId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);

  async function saveDefinition() {
    setBusy(true);
    setStatusMsg(null);
    setError(null);
    try {
      const updated = await updateReportDefinition(definitionId, {
        name: name.trim(),
        params: { branch, horizonDays },
        active,
      });
      setItem(updated);
      setStatusMsg("Definição salva.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  }

  async function saveRecipients() {
    setBusy(true);
    setStatusMsg(null);
    setError(null);
    try {
      await replaceReportRecipients(
        definitionId,
        recipients.map((u) => ({ userId: u.id, email: u.email })),
      );
      setStatusMsg("Destinatários salvos.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao salvar destinatários.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function saveSchedule() {
    setBusy(true);
    setStatusMsg(null);
    setError(null);
    try {
      const saved = await upsertReportSchedule(definitionId, {
        scheduleKind,
        hour,
        minute,
        weekday: scheduleKind === "weekly" ? weekday : null,
        enabled: scheduleEnabled,
      });
      setSchedule(saved);
      setStatusMsg("Agenda salva.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar agenda.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRunNow() {
    setBusy(true);
    setStatusMsg(null);
    setError(null);
    try {
      if (recipients.length === 0) {
        setError(
          "Inclua ao menos um destinatário com e-mail antes de enviar.",
        );
        return;
      }
      await replaceReportRecipients(
        definitionId,
        recipients.map((u) => ({ userId: u.id, email: u.email })),
      );
      const run = await runReportDefinition(definitionId);
      setStatusMsg(
        run.status === "succeeded"
          ? "E-mail enviado com sucesso."
          : `Execução finalizada: ${run.status}${run.error ? ` — ${run.error}` : ""}`,
      );
      const runsPayload = await listReportRuns(definitionId);
      setRuns(runsPayload.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar agora.");
    } finally {
      setBusy(false);
    }
  }

  const displayTitle = name.trim() || item?.name || "Definição";

  return (
    <div className="rp-page-content">
        <header className="rp-page-header">
          <div className="rp-page-header__shell">
            <div className="rp-page-header__main">
              <div className="rp-page-header__brand">
                <div className="rp-page-header__titles">
                  <p className="rp-page-header__eyebrow">Delpi Reports</p>
                  <div className="rp-page-header__title-row">
                    <h1>{loading ? "Carregando…" : displayTitle}</h1>
                    {item ? (
                      <span
                        className={
                          active
                            ? "rp-pill rp-pill--success"
                            : "rp-pill rp-pill--muted"
                        }
                      >
                        {active ? "Ativa" : "Inativa"}
                      </span>
                    ) : null}
                  </div>
                  <p className="rp-page-header__subtitle">
                    Parâmetros, destinatários, agenda e envio por e-mail
                  </p>
                </div>
              </div>

              <div className="rp-page-header__actions">
                <a className="rp-btn rp-btn--ghost" href={REPORTS_LIST_PATH}>
                  <ArrowLeft size={16} aria-hidden />
                  Voltar
                </a>
                <button
                  type="button"
                  className="rp-btn rp-btn--ghost"
                  disabled={loading || busy}
                  onClick={() => void reload()}
                >
                  <RefreshCw
                    size={16}
                    aria-hidden
                    className={loading ? "rp-spin" : undefined}
                  />
                  Atualizar
                </button>
                <button
                  type="button"
                  className="rp-btn rp-btn--primary"
                  disabled={!item || busy}
                  onClick={() => void handleRunNow()}
                >
                  <Send size={16} aria-hidden />
                  Enviar agora
                </button>
              </div>
            </div>

            {item ? (
              <div className="rp-meta-strip" aria-label="Resumo da definição">
                <div className="rp-meta-chip">
                  <Mail size={14} aria-hidden />
                  <span>
                    <strong>Provider</strong>
                    <em>{item.providerKey}</em>
                  </span>
                </div>
                <div className="rp-meta-chip">
                  <Settings2 size={14} aria-hidden />
                  <span>
                    <strong>Unidade</strong>
                    <em>{formatBranchUnitLabel(branch)}</em>
                  </span>
                </div>
                <div className="rp-meta-chip">
                  <Users size={14} aria-hidden />
                  <span>
                    <strong>Destinatários</strong>
                    <em>{recipients.length}</em>
                  </span>
                </div>
                <div className="rp-meta-chip">
                  <CalendarClock size={14} aria-hidden />
                  <span>
                    <strong>Próximo disparo</strong>
                    <em>
                      {scheduleEnabled && schedule?.nextRunAt
                        ? formatDateTimeBr(schedule.nextRunAt)
                        : "Agenda desligada"}
                    </em>
                  </span>
                </div>
              </div>
            ) : null}

            <div className="rp-page-header__brand-bar" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </div>
          </div>
        </header>

        {error ? (
          <p className="rp-banner rp-banner--error" role="alert">
            {error}
          </p>
        ) : null}
        {statusMsg ? (
          <p className="rp-banner rp-banner--ok" role="status">
            {statusMsg}
          </p>
        ) : null}

        {loading && !item ? (
          <p className="rp-banner">Carregando definição…</p>
        ) : null}

        {item ? (
          <div className="rp-detail-stack">
            <div className="rp-detail-grid">
              <section className="rp-card">
                <div className="rp-card__header">
                  <div>
                    <h2 className="rp-card__title">
                      <Settings2 size={18} aria-hidden />
                      Parâmetros
                    </h2>
                    <p className="rp-card__hint">
                      Nome amigável, unidade e horizonte do relatório.
                    </p>
                  </div>
                  <button
                    type="button"
                    className="rp-btn rp-btn--secondary"
                    disabled={busy}
                    onClick={() => void saveDefinition()}
                  >
                    <Save size={16} aria-hidden />
                    Salvar
                  </button>
                </div>
                <div className="rp-form-grid">
                  <label className="rp-field rp-field--full">
                    <span>Nome</span>
                    <input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      maxLength={200}
                    />
                  </label>
                  <label className="rp-field">
                    <span>Unidade</span>
                    <select
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                    >
                      <option value="01">Jaraguá do Sul/SC</option>
                      <option value="02">Rio Bananal/ES</option>
                    </select>
                  </label>
                  <label className="rp-field">
                    <span>Horizonte (dias)</span>
                    <input
                      type="number"
                      min={1}
                      max={365}
                      value={horizonDays}
                      onChange={(e) =>
                        setHorizonDays(Number(e.target.value) || 30)
                      }
                    />
                  </label>
                  <label className="rp-switch">
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={(e) => setActive(e.target.checked)}
                    />
                    <span>Definição ativa</span>
                  </label>
                </div>
              </section>

              <section className="rp-card">
                <div className="rp-card__header">
                  <div>
                    <h2 className="rp-card__title">
                      <CalendarClock size={18} aria-hidden />
                      Agenda
                    </h2>
                    <p className="rp-card__hint">
                      Disparo automático (timezone America/Sao_Paulo).
                    </p>
                  </div>
                  <button
                    type="button"
                    className="rp-btn rp-btn--secondary"
                    disabled={busy}
                    onClick={() => void saveSchedule()}
                  >
                    <Save size={16} aria-hidden />
                    Salvar
                  </button>
                </div>
                <div className="rp-form-grid">
                  <label className="rp-field">
                    <span>Frequência</span>
                    <select
                      value={scheduleKind}
                      onChange={(e) =>
                        setScheduleKind(
                          e.target.value === "weekly" ? "weekly" : "daily",
                        )
                      }
                    >
                      <option value="daily">Diário</option>
                      <option value="weekly">Semanal</option>
                    </select>
                  </label>
                  {scheduleKind === "weekly" ? (
                    <label className="rp-field">
                      <span>Dia da semana</span>
                      <select
                        value={weekday}
                        onChange={(e) => setWeekday(Number(e.target.value))}
                      >
                        {WEEKDAY_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </label>
                  ) : (
                    <div className="rp-field rp-field--spacer" aria-hidden />
                  )}
                  <label className="rp-field">
                    <span>Hora</span>
                    <input
                      type="number"
                      min={0}
                      max={23}
                      value={hour}
                      onChange={(e) => setHour(Number(e.target.value))}
                    />
                  </label>
                  <label className="rp-field">
                    <span>Minuto</span>
                    <input
                      type="number"
                      min={0}
                      max={59}
                      value={minute}
                      onChange={(e) => setMinute(Number(e.target.value))}
                    />
                  </label>
                  <label className="rp-switch rp-field--full">
                    <input
                      type="checkbox"
                      checked={scheduleEnabled}
                      onChange={(e) => setScheduleEnabled(e.target.checked)}
                    />
                    <span>Agenda habilitada</span>
                  </label>
                  {schedule?.nextRunAt ? (
                    <p className="rp-inline-note rp-field--full">
                      Próximo disparo:{" "}
                      <strong>{formatDateTimeBr(schedule.nextRunAt)}</strong>
                      <span className="rp-inline-note__muted">
                        {" "}
                        ({schedule.timezone || "America/Sao_Paulo"})
                      </span>
                    </p>
                  ) : null}
                </div>
              </section>
            </div>

            <section className="rp-card">
              <div className="rp-card__header">
                <div>
                  <h2 className="rp-card__title">
                    <Users size={18} aria-hidden />
                    Destinatários
                  </h2>
                  <p className="rp-card__hint">
                    Colaboradores do diretório que receberão o e-mail.
                  </p>
                </div>
                <button
                  type="button"
                  className="rp-btn rp-btn--secondary"
                  disabled={busy}
                  onClick={() => void saveRecipients()}
                >
                  <Save size={16} aria-hidden />
                  Salvar lista
                </button>
              </div>
              <UserDirectoryPicker
                value={recipients}
                onChange={setRecipients}
                searchUsers={searchDirectoryUsers}
                showSelectedList
                labels={{
                  title: "Buscar colaboradores",
                  hint: "Busque por nome ou e-mail. «Enviar agora» também salva a seleção atual.",
                }}
              />
              {recipients.length === 0 ? (
                <p className="rp-inline-note">
                  Selecione ao menos um destinatário com e-mail válido para
                  enviar.
                </p>
              ) : null}
            </section>

            <section className="rp-card">
              <div className="rp-card__header">
                <div>
                  <h2 className="rp-card__title">
                    <History size={18} aria-hidden />
                    Histórico de execuções
                  </h2>
                  <p className="rp-card__hint">
                    Últimos envios manuais e pela agenda.
                  </p>
                </div>
              </div>
              {runs.length === 0 ? (
                <p className="rp-empty">Nenhuma execução ainda.</p>
              ) : (
                <ul className="rp-run-list">
                  {runs.map((run) => (
                    <li key={run.id} className="rp-run-list__item">
                      <div className="rp-run-list__main">
                        <span className={runStatusClass(run.status)}>
                          {formatRunStatusLabel(run.status)}
                        </span>
                        <span className="rp-run-list__trigger">
                          {formatTriggerLabel(run.trigger)}
                        </span>
                        <time
                          className="rp-run-list__time"
                          dateTime={run.createdAt ?? undefined}
                        >
                          {formatDateTimeBr(run.createdAt)}
                        </time>
                      </div>
                      <div className="rp-run-list__meta">
                        {typeof run.summary?.rowCount === "number" ? (
                          <span>{run.summary.rowCount} item(ns)</span>
                        ) : null}
                        {run.error ? (
                          <span className="rp-run-list__error">{run.error}</span>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        ) : null}
    </div>
  );
}
