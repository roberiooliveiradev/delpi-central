import { type FormEvent, useEffect, useState } from "react";
import { CalendarRange } from "lucide-react";

import {
  createAdminExercise,
  listAdminExercises,
  transitionAdminExercise,
  updateAdminExercise,
} from "../../api/budgetPlanningApi";
import type { AdminExerciseInput, BudgetExercise } from "../../types/budgetPlanning";
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

export function AdminExercisesPage() {
  const { profile, loading: permLoading } = usePermissions();
  const [items, setItems] = useState<BudgetExercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<AdminExerciseInput>(emptyForm);
  const [saving, setSaving] = useState(false);
  const canAccess = hasAdminAccess(profile);

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
    try {
      await createAdminExercise({
        year: Number(form.year),
        name: form.name.trim(),
        filling_starts_at: form.filling_starts_at || null,
        deadline_at: form.deadline_at || null,
      });
      setForm({ ...emptyForm, year: new Date().getFullYear() + 1 });
      await reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao criar exercício.");
    } finally {
      setSaving(false);
    }
  }

  async function publish(id: string) {
    setError(null);
    try {
      await transitionAdminExercise(id, "publish");
      await reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao publicar exercício.");
    }
  }

  if (permLoading || (canAccess && loading)) {
    return (
      <PageShell title="Exercícios" subtitle="Ciclos orçamentários.">
        <LoadingActivityCard title="Carregando…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell title="Exercícios" subtitle="Acesso restrito.">
        <StateBox variant="error" dismissible={false}>
          Sem permissão administrativa.
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Exercícios orçamentários"
      subtitle="Crie, edite e publique o ciclo ativo."
      icon={<CalendarRange size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="admin"
    >
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      <SectionCard title="Novo exercício" hint="Somente um exercício ativo por vez (ao publicar).">
        <form className="po-form" onSubmit={(e) => void handleSubmit(e)}>
          <label>
            Ano
            <input
              type="number"
              required
              value={form.year}
              onChange={(e) => setForm((f) => ({ ...f, year: Number(e.target.value) }))}
            />
          </label>
          <label>
            Nome
            <input
              required
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </label>
          <label>
            Início do preenchimento
            <input
              type="date"
              value={form.filling_starts_at ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, filling_starts_at: e.target.value }))}
            />
          </label>
          <label>
            Prazo
            <input
              type="date"
              value={form.deadline_at ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, deadline_at: e.target.value }))}
            />
          </label>
          <button className="po-btn po-btn--primary" type="submit" disabled={saving}>
            {saving ? "Salvando…" : "Criar rascunho"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Exercícios cadastrados">
        <ul className="po-link-list">
          {items.map((item) => (
            <li key={item.id}>
              <div>
                <strong>
                  {item.name} · {item.year}
                </strong>
                <span className="po-muted"> status: {item.status}</span>
              </div>
              {item.status === "draft" ? (
                <button type="button" className="po-btn po-btn--secondary" onClick={() => void publish(item.id)}>
                  Publicar (abrir ciclo)
                </button>
              ) : null}
              {item.status === "draft" ? (
                <button
                  type="button"
                  className="po-btn po-btn--secondary"
                  onClick={() =>
                    void updateAdminExercise(item.id, { name: `${item.name}`.trim() }).then(() => reload())
                  }
                >
                  Salvar
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      </SectionCard>
    </PageShell>
  );
}
