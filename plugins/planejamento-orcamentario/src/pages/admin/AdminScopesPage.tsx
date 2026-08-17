import { type FormEvent, useEffect, useMemo, useState } from "react";
import { UserDirectoryPicker } from "@delpi/plugin-ui/index";
import { Landmark, Users } from "lucide-react";

import { searchDirectoryUsers, type DirectoryUser } from "../../api/directoryApi";
import { HttpRequestError } from "../../api/httpClient";
import {
  createAdminScope,
  deactivateAdminScope,
  listAdminScopes,
} from "../../api/budgetPlanningApi";
import type { OrgCatalog, UserScope, UserScopeInput } from "../../types/budgetPlanning";
import { PageShell } from "../../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../../components/uiKit";
import { usePermissions } from "../../hooks/usePermissions";
import {
  costCenterKey,
  formatCostCenterLabel,
} from "../../utils/orgCostCenters";
import { hasScopesManageAccess } from "../../utils/permissions";
import { filterCostCenters } from "../../utils/responsibilities";
import { routeHref } from "../../utils/routing";

const emptyScope: UserScopeInput = {
  user_sub: "",
  user_name: "",
  user_email: "",
  unit_code: "",
  area_code: "",
  cost_center_code: "",
  scope_level: "cost_center",
  role_in_scope: "editor",
};

export function AdminScopesPage() {
  const { profile, loading: permLoading } = usePermissions();
  const [scopes, setScopes] = useState<UserScope[]>([]);
  const [catalog, setCatalog] = useState<OrgCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<UserScopeInput>(emptyScope);
  const [selectedUsers, setSelectedUsers] = useState<DirectoryUser[]>([]);
  const [saving, setSaving] = useState(false);
  const canAccess = hasScopesManageAccess(profile);

  async function reload(signal?: AbortSignal) {
    const data = await listAdminScopes(signal);
    setScopes(data.items);
    setCatalog(data.catalog);
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
          if (err instanceof HttpRequestError && err.status === 401) {
            setError("Sessão expirada (401). Faça login novamente.");
          } else if (err instanceof HttpRequestError && err.status === 403) {
            setError("Acesso negado (403) para gerenciar escopos.");
          } else {
            setError(err instanceof Error ? err.message : "Erro ao carregar escopos.");
          }
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [canAccess, permLoading]);

  const costCenterOptions = useMemo(
    () => filterCostCenters(catalog, form.unit_code, ""),
    [catalog, form.unit_code],
  );

  function handleUserSelection(users: DirectoryUser[]) {
    setSelectedUsers(users);
    const picked = users[0];
    setForm((prev) => ({
      ...prev,
      user_sub: picked?.id ?? "",
      user_name: picked?.name ?? "",
      user_email: picked?.email ?? "",
    }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!form.user_sub.trim() || !form.unit_code || !form.cost_center_code) {
      setError("Selecione usuário, filial e um centro de custo do catálogo interno.");
      return;
    }
    const selectedCc = costCenterOptions.find((cc) => cc.code === form.cost_center_code);
    if (!selectedCc) {
      setError("Centro de custo incompatível com a filial selecionada.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createAdminScope({
        ...form,
        user_sub: form.user_sub.trim(),
        area_code: form.area_code || null,
      });
      setForm(emptyScope);
      setSelectedUsers([]);
      await reload();
    } catch (err: unknown) {
      if (err instanceof HttpRequestError && err.status === 401) {
        setError("Sessão expirada (401). Faça login novamente.");
      } else if (err instanceof HttpRequestError && err.status === 403) {
        setError("Acesso negado (403) para criar escopo.");
      } else {
        setError(err instanceof Error ? err.message : "Falha ao criar escopo.");
      }
    } finally {
      setSaving(false);
    }
  }

  if (permLoading || loading) {
    return (
      <PageShell
        title="Escopos"
        subtitle="Cadastro auxiliar — não libera CAPEX nem Pessoal."
      >
        <LoadingActivityCard title="Carregando…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell title="Escopos" subtitle="Acesso restrito.">
        <StateBox variant="error" dismissible={false}>
          Sem permissão para gerenciar escopos.
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Escopos organizacionais"
      subtitle="Cadastro auxiliar de vínculos. Para liberar elaboração por centro, use Responsáveis orçamentários."
      icon={<Users size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="admin"
    >
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      <StateBox variant="warning" dismissible={false}>
        Vinculações nesta tela <strong>não</strong> aparecem em Orçamento por centro. Para o
        Fabiano (ou qualquer responsável) ver os centros 0205 / 0405, cadastre em{" "}
        <a href={routeHref("admin-responsaveis")}>Administração → Responsáveis orçamentários</a>, no
        exercício vigente (CAPEX + Pessoal juntos).
      </StateBox>

      <SectionCard
        title="Catálogo de centros de custo"
        hint="Cadastro somente a partir do ERP, por filial — sem código ou descrição digitados."
      >
        <p className="po-muted">
          Use a tela administrativa para consultar o ERP e adicionar centros ao planejamento.
        </p>
        <a className="po-btn po-btn--secondary" href={routeHref("admin-centros-de-custo")}>
          <Landmark size={16} aria-hidden="true" />
          Abrir Centros de Custo
        </a>
        {(catalog?.cost_centers?.length ?? 0) > 0 ? (
          <ul className="po-link-list" style={{ marginTop: "1rem" }}>
            {(catalog?.cost_centers ?? []).map((cc) => (
              <li key={costCenterKey(cc)}>
                <strong>{formatCostCenterLabel(cc)}</strong>
              </li>
            ))}
          </ul>
        ) : (
          <p className="po-muted" style={{ marginTop: "1rem" }}>
            Nenhum centro cadastrado ainda.
          </p>
        )}
      </SectionCard>

      <SectionCard title="Novo escopo" hint="Fluxo: filial → centro de custo daquela filial.">
        <form className="po-form" onSubmit={(e) => void handleSubmit(e)}>
          <UserDirectoryPicker
            value={selectedUsers}
            onChange={handleUserSelection}
            searchUsers={searchDirectoryUsers}
            maxSelected={1}
            showEmail
            labels={{
              title: "Colaborador",
              hint: "Busque por nome, e-mail ou identificador (mín. 2 caracteres).",
              placeholder: "Pesquisar usuário…",
            }}
          />
          {form.user_sub ? (
            <p className="po-muted">
              Selecionado: {form.user_name || form.user_sub}
              {form.user_email ? ` · ${form.user_email}` : ""}
            </p>
          ) : (
            <p className="po-muted">Nenhum usuário selecionado.</p>
          )}
          <label>
            Filial
            <select
              required
              value={form.unit_code}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  unit_code: e.target.value,
                  cost_center_code: "",
                  area_code: "",
                }))
              }
            >
              <option value="">Selecione…</option>
              {(catalog?.units ?? []).map((u) => (
                <option key={u.code} value={u.code}>
                  {u.code} — {u.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Centro de custo
            <select
              required
              disabled={!form.unit_code}
              value={form.cost_center_code ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, cost_center_code: e.target.value }))}
            >
              <option value="">
                {form.unit_code ? "Selecione…" : "Selecione a filial primeiro"}
              </option>
              {costCenterOptions.map((cc) => (
                <option key={costCenterKey(cc)} value={cc.code}>
                  {formatCostCenterLabel(cc)}
                </option>
              ))}
            </select>
          </label>
          <button
            className="po-btn po-btn--primary"
            type="submit"
            disabled={saving || costCenterOptions.length === 0 || !form.user_sub || !form.unit_code}
          >
            {saving ? "Salvando…" : "Vincular escopo"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Escopos ativos/inativos">
        <ul className="po-link-list">
          {scopes.map((scope) => (
            <li key={scope.id}>
              <div>
                <strong>{scope.user_name || scope.user_sub}</strong>
                <span className="po-muted">
                  {" "}
                  · {scope.user_email ?? scope.user_sub} ·{" "}
                  {formatCostCenterLabel({
                    branch: scope.unit_code,
                    code: scope.cost_center_code,
                  })}{" "}
                  · {scope.active ? "ativo" : "inativo"}
                </span>
              </div>
              {scope.active ? (
                <button
                  type="button"
                  className="po-btn po-btn--secondary"
                  onClick={() =>
                    void deactivateAdminScope(scope.id)
                      .then(() => reload())
                      .catch((err: unknown) =>
                        setError(err instanceof Error ? err.message : "Falha ao desativar."),
                      )
                  }
                >
                  Desativar
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      </SectionCard>
    </PageShell>
  );
}
