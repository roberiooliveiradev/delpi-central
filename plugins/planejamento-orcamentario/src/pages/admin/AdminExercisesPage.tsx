import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  Archive,
  CalendarRange,
  CheckCircle2,
  FilePenLine,
  Lock,
  Plus,
  RefreshCw,
  Unlock,
} from "lucide-react";

import {
  createAdminExercise,
  listAdminExercises,
  transitionAdminExercise,
  updateAdminExercise,
} from "../../api/budgetPlanningApi";
import type {
  AdminExerciseInput,
  BudgetExercise,
  ExerciseStatus,
} from "../../types/budgetPlanning";
import { PageShell } from "../../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../../components/uiKit";
import { usePermissions } from "../../hooks/usePermissions";
import { hasAdminAccess } from "../../utils/permissions";

const emptyForm: AdminExerciseInput = {
  year: new Date().getFullYear() + 1,
  name: "",
  filling_starts_at: "",
  deadline_at: "",
};

type ExerciseEditDraft = {
  name: string;
  filling_starts_at: string;
  deadline_at: string;
};

const STATUS_LABEL: Record<ExerciseStatus, string> = {
  draft: "Rascunho",
  open: "Aberto",
  closing: "Em encerramento",
  locked: "Encerrado",
  archived: "Arquivado",
};

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const raw = value.length >= 10 ? value.slice(0, 10) : value;
  const date = new Date(`${raw}T12:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function toDateInput(value?: string | null): string {
  if (!value) return "";
  return value.length >= 10 ? value.slice(0, 10) : value;
}

function statusTone(status: ExerciseStatus): string {
  switch (status) {
    case "open":
      return "success";
    case "draft":
    case "closing":
      return "warning";
    case "locked":
    case "archived":
      return "muted";
    default:
      return "muted";
  }
}

function pickActiveExercise(items: BudgetExercise[]): BudgetExercise | null {
  return (
    items.find((item) => item.is_active) ??
    items.find((item) => item.status === "open" || item.status === "closing") ??
    items.find((item) => item.status === "draft") ??
    null
  );
}

export function AdminExercisesPage() {
  const { profile, loading: permLoading } = usePermissions();
  const [items, setItems] = useState<BudgetExercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [form, setForm] = useState<AdminExerciseInput>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<ExerciseEditDraft | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const canAccess = hasAdminAccess(profile);

  const active = useMemo(() => pickActiveExercise(items), [items]);
  const sorted = useMemo(
    () =>
      [...items].sort((a, b) => {
        if (b.year !== a.year) return b.year - a.year;
        return a.name.localeCompare(b.name, "pt-BR");
      }),
    [items],
  );

  async function reload(signal?: AbortSignal) {
    const data = await listAdminExercises(signal);
    setItems(data);
  }

  useEffect(() => {
    if (permLoading) return;
    if (!canAccess) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    reload(controller.signal)
      .then(() => setError(null))
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Erro ao listar exercícios.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [canAccess, permLoading]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await createAdminExercise({
        year: Number(form.year),
        name: form.name.trim(),
        filling_starts_at: form.filling_starts_at || null,
        deadline_at: form.deadline_at || null,
      });
      setForm({ ...emptyForm, year: new Date().getFullYear() + 1 });
      setShowCreate(false);
      setSuccess("Rascunho do exercício criado. Publique para abrir o ciclo.");
      await reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao criar exercício.");
    } finally {
      setSaving(false);
    }
  }

  function startEdit(item: BudgetExercise) {
    setEditingId(item.id);
    setEditDraft({
      name: item.name,
      filling_starts_at: toDateInput(item.filling_starts_at),
      deadline_at: toDateInput(item.deadline_at),
    });
    setError(null);
    setSuccess(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditDraft(null);
  }

  async function saveEdit(id: string) {
    if (!editDraft) return;
    const name = editDraft.name.trim();
    if (!name) {
      setError("Informe o nome do exercício.");
      return;
    }
    setBusyId(id);
    setError(null);
    setSuccess(null);
    try {
      await updateAdminExercise(id, {
        name,
        filling_starts_at: editDraft.filling_starts_at || null,
        deadline_at: editDraft.deadline_at || null,
      });
      cancelEdit();
      setSuccess("Exercício atualizado.");
      await reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar exercício.");
    } finally {
      setBusyId(null);
    }
  }

  async function runTransition(id: string, action: string, okMessage: string) {
    setBusyId(id);
    setError(null);
    setSuccess(null);
    try {
      await transitionAdminExercise(id, action);
      setSuccess(okMessage);
      await reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao alterar o status do exercício.");
    } finally {
      setBusyId(null);
    }
  }

  if (permLoading || (canAccess && loading)) {
    return (
      <PageShell
        title="Exercícios orçamentários"
        subtitle="Ciclos anuais do planejamento."
        icon={<CalendarRange size={28} strokeWidth={1.75} aria-hidden="true" />}
        backRoute="admin"
      >
        <LoadingActivityCard title="Carregando exercícios…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell
        title="Exercícios orçamentários"
        subtitle="Área restrita a administradores."
        icon={<CalendarRange size={28} strokeWidth={1.75} aria-hidden="true" />}
        backRoute="admin"
      >
        <StateBox variant="error" dismissible={false}>
          Sem permissão administrativa.
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Exercícios orçamentários"
      subtitle="Defina o ciclo ativo, prazos e o momento de abrir ou encerrar a elaboração."
      icon={<CalendarRange size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="admin"
    >
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}
      {success ? (
        <StateBox variant="success" dismissible={false}>
          {success}
        </StateBox>
      ) : null}

      <section className="po-exercise-admin" aria-label="Gestão de exercícios">
        <div className="po-exercise-admin__hero">
          <div className="po-exercise-admin__hero-copy">
            <p className="po-exercise-admin__eyebrow">Administração · Ciclo</p>
            {active ? (
              <>
                <h2 className="po-exercise-admin__year">{active.year}</h2>
                <p className="po-exercise-admin__name">{active.name}</p>
                <p className="po-exercise-admin__lead">
                  {active.status === "draft"
                    ? "Este ciclo ainda é rascunho. Publique para liberar a elaboração aos responsáveis."
                    : active.status === "open"
                      ? "Ciclo aberto: responsáveis podem elaborar CAPEX e Pessoal nos centros vinculados."
                      : active.status === "closing"
                        ? "Ciclo em encerramento: finalize aprovações e prepare o bloqueio."
                        : active.status === "locked"
                          ? "Ciclo encerrado. Reabra apenas se precisar corrigir o período."
                          : "Ciclo arquivado — somente consulta histórica."}
                </p>
              </>
            ) : (
              <>
                <h2 className="po-exercise-admin__year">—</h2>
                <p className="po-exercise-admin__name">Nenhum exercício cadastrado</p>
                <p className="po-exercise-admin__lead">
                  Crie o primeiro rascunho do ciclo orçamentário para começar a configuração.
                </p>
              </>
            )}
          </div>

          <aside className="po-exercise-admin__hero-panel" aria-label="Resumo do ciclo em destaque">
            {active ? (
              <>
                <span
                  className={`po-badge po-badge--${statusTone(active.status)} po-exercise-admin__status`}
                >
                  {STATUS_LABEL[active.status]}
                  {active.is_active ? " · ativo" : ""}
                </span>
                <dl className="po-exercise-admin__meta">
                  <div>
                    <dt>Abertura</dt>
                    <dd>{formatDate(active.filling_starts_at)}</dd>
                  </div>
                  <div>
                    <dt>Prazo</dt>
                    <dd>{formatDate(active.deadline_at)}</dd>
                  </div>
                  <div>
                    <dt>Exercícios</dt>
                    <dd>{items.length}</dd>
                  </div>
                </dl>
              </>
            ) : (
              <p className="po-muted po-exercise-admin__hero-empty">
                Quando houver um ciclo, o status e os prazos aparecerão aqui.
              </p>
            )}
            <button
              type="button"
              className="po-btn po-btn--primary"
              onClick={() => {
                setShowCreate((v) => !v);
                setSuccess(null);
              }}
            >
              <Plus size={16} aria-hidden="true" />
              {showCreate ? "Fechar formulário" : "Novo exercício"}
            </button>
          </aside>
        </div>

        {showCreate ? (
          <SectionCard
            title="Novo exercício"
            hint="Cria um rascunho. Só um ciclo ativo por vez — a publicação abre a elaboração."
          >
            <form className="po-stack-gap" onSubmit={(e) => void handleSubmit(e)}>
              <div className="po-form-grid">
                <label className="po-field">
                  <span>Ano</span>
                  <input
                    type="number"
                    required
                    min={2000}
                    max={2100}
                    value={form.year}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, year: Number(e.target.value) }))
                    }
                  />
                </label>
                <label className="po-field">
                  <span>Nome</span>
                  <input
                    required
                    placeholder="Ex.: Planejamento Orçamentário Delpi - 2028"
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  />
                </label>
                <label className="po-field">
                  <span>Início do preenchimento</span>
                  <input
                    type="date"
                    value={form.filling_starts_at ?? ""}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, filling_starts_at: e.target.value }))
                    }
                  />
                </label>
                <label className="po-field">
                  <span>Prazo final</span>
                  <input
                    type="date"
                    value={form.deadline_at ?? ""}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, deadline_at: e.target.value }))
                    }
                  />
                </label>
              </div>
              <div className="po-form-actions">
                <button
                  type="button"
                  className="po-btn po-btn--secondary"
                  onClick={() => setShowCreate(false)}
                >
                  Cancelar
                </button>
                <button className="po-btn po-btn--primary" type="submit" disabled={saving}>
                  {saving ? "Salvando…" : "Criar rascunho"}
                </button>
              </div>
            </form>
          </SectionCard>
        ) : null}

        <div className="po-exercise-admin__list-head">
          <h3 className="po-exercise-admin__list-title">Ciclos cadastrados</h3>
          <p className="po-exercise-admin__list-subtitle">
            Publique o rascunho para abrir; depois encerrar, bloquear ou arquivar conforme o
            calendário.
          </p>
        </div>

        {sorted.length === 0 ? (
          <StateBox variant="default" dismissible={false}>
            Ainda não há exercícios. Use «Novo exercício» para criar o primeiro rascunho.
          </StateBox>
        ) : (
          <ul className="po-exercise-admin__grid">
            {sorted.map((item) => {
              const editing = editingId === item.id && editDraft;
              const canEdit =
                item.status === "draft" ||
                item.status === "open" ||
                item.status === "closing";
              const busy = busyId === item.id;

              return (
                <li key={item.id} className="po-exercise-admin__card">
                  <div className="po-exercise-admin__card-top">
                    <div>
                      <p className="po-exercise-admin__card-year">{item.year}</p>
                      {editing ? (
                        <label className="po-field">
                          <span className="po-sr-only">Nome</span>
                          <input
                            value={editDraft.name}
                            onChange={(e) =>
                              setEditDraft((d) =>
                                d ? { ...d, name: e.target.value } : d,
                              )
                            }
                          />
                        </label>
                      ) : (
                        <h4 className="po-exercise-admin__card-name">{item.name}</h4>
                      )}
                    </div>
                    <span className={`po-badge po-badge--${statusTone(item.status)}`}>
                      {STATUS_LABEL[item.status]}
                    </span>
                  </div>

                  {editing ? (
                    <div className="po-form-grid po-exercise-admin__edit-grid">
                      <label className="po-field">
                        <span>Início do preenchimento</span>
                        <input
                          type="date"
                          value={editDraft.filling_starts_at}
                          onChange={(e) =>
                            setEditDraft((d) =>
                              d ? { ...d, filling_starts_at: e.target.value } : d,
                            )
                          }
                        />
                      </label>
                      <label className="po-field">
                        <span>Prazo final</span>
                        <input
                          type="date"
                          value={editDraft.deadline_at}
                          onChange={(e) =>
                            setEditDraft((d) =>
                              d ? { ...d, deadline_at: e.target.value } : d,
                            )
                          }
                        />
                      </label>
                    </div>
                  ) : (
                    <dl className="po-exercise-admin__card-meta">
                      <div>
                        <dt>Abertura</dt>
                        <dd>{formatDate(item.filling_starts_at)}</dd>
                      </div>
                      <div>
                        <dt>Prazo</dt>
                        <dd>{formatDate(item.deadline_at)}</dd>
                      </div>
                      {item.is_active ? (
                        <div>
                          <dt>Destaque</dt>
                          <dd>
                            <span className="po-inline-success">
                              <CheckCircle2 size={14} aria-hidden="true" /> Ativo
                            </span>
                          </dd>
                        </div>
                      ) : null}
                    </dl>
                  )}

                  <div className="po-exercise-admin__actions">
                    {editing ? (
                      <>
                        <button
                          type="button"
                          className="po-btn po-btn--secondary po-btn--sm"
                          disabled={busy}
                          onClick={cancelEdit}
                        >
                          Cancelar
                        </button>
                        <button
                          type="button"
                          className="po-btn po-btn--primary po-btn--sm"
                          disabled={busy}
                          onClick={() => void saveEdit(item.id)}
                        >
                          {busy ? "Salvando…" : "Salvar alterações"}
                        </button>
                      </>
                    ) : (
                      <>
                        {canEdit ? (
                          <button
                            type="button"
                            className="po-btn po-btn--secondary po-btn--sm"
                            disabled={busy}
                            onClick={() => startEdit(item)}
                          >
                            <FilePenLine size={14} aria-hidden="true" />
                            Editar
                          </button>
                        ) : null}

                        {item.status === "draft" ? (
                          <button
                            type="button"
                            className="po-btn po-btn--primary po-btn--sm"
                            disabled={busy}
                            onClick={() =>
                              void runTransition(
                                item.id,
                                "publish",
                                "Ciclo publicado e aberto para elaboração.",
                              )
                            }
                          >
                            <Unlock size={14} aria-hidden="true" />
                            {busy ? "Publicando…" : "Publicar ciclo"}
                          </button>
                        ) : null}

                        {item.status === "open" ? (
                          <>
                            <button
                              type="button"
                              className="po-btn po-btn--secondary po-btn--sm"
                              disabled={busy}
                              onClick={() =>
                                void runTransition(
                                  item.id,
                                  "start_close",
                                  "Ciclo marcado como em encerramento.",
                                )
                              }
                            >
                              Iniciar encerramento
                            </button>
                            <button
                              type="button"
                              className="po-btn po-btn--secondary po-btn--sm"
                              disabled={busy}
                              onClick={() =>
                                void runTransition(
                                  item.id,
                                  "lock",
                                  "Ciclo encerrado (bloqueado).",
                                )
                              }
                            >
                              <Lock size={14} aria-hidden="true" />
                              Encerrar
                            </button>
                          </>
                        ) : null}

                        {item.status === "closing" ? (
                          <>
                            <button
                              type="button"
                              className="po-btn po-btn--secondary po-btn--sm"
                              disabled={busy}
                              onClick={() =>
                                void runTransition(
                                  item.id,
                                  "reopen",
                                  "Ciclo reaberto para elaboração.",
                                )
                              }
                            >
                              <RefreshCw size={14} aria-hidden="true" />
                              Reabrir
                            </button>
                            <button
                              type="button"
                              className="po-btn po-btn--secondary po-btn--sm"
                              disabled={busy}
                              onClick={() =>
                                void runTransition(
                                  item.id,
                                  "lock",
                                  "Ciclo encerrado (bloqueado).",
                                )
                              }
                            >
                              <Lock size={14} aria-hidden="true" />
                              Encerrar
                            </button>
                          </>
                        ) : null}

                        {item.status === "locked" ? (
                          <>
                            <button
                              type="button"
                              className="po-btn po-btn--secondary po-btn--sm"
                              disabled={busy}
                              onClick={() =>
                                void runTransition(
                                  item.id,
                                  "reopen",
                                  "Ciclo reaberto.",
                                )
                              }
                            >
                              <RefreshCw size={14} aria-hidden="true" />
                              Reabrir
                            </button>
                            <button
                              type="button"
                              className="po-btn po-btn--secondary po-btn--sm"
                              disabled={busy}
                              onClick={() =>
                                void runTransition(
                                  item.id,
                                  "archive",
                                  "Ciclo arquivado.",
                                )
                              }
                            >
                              <Archive size={14} aria-hidden="true" />
                              Arquivar
                            </button>
                          </>
                        ) : null}

                        {item.status === "draft" ? (
                          <button
                            type="button"
                            className="po-btn po-btn--secondary po-btn--sm"
                            disabled={busy}
                            onClick={() =>
                              void runTransition(item.id, "archive", "Rascunho arquivado.")
                            }
                          >
                            <Archive size={14} aria-hidden="true" />
                            Arquivar
                          </button>
                        ) : null}
                      </>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </PageShell>
  );
}
