import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { UserDirectoryPicker } from "@delpi/plugin-ui/index";
import {
  Filter,
  Network,
  Pencil,
  RotateCcw,
  UserMinus,
  UserPlus,
  Users,
} from "lucide-react";

import { searchDirectoryUsers, type DirectoryUser } from "../../api/directoryApi";
import { HttpRequestError } from "../../api/httpClient";
import {
  createAdminBudgetResponsibilityPair,
  deactivateAdminBudgetResponsibility,
  listAdminBudgetResponsibilities,
  listAdminExercises,
  listAdminScopes,
  reactivateAdminBudgetResponsibility,
  updateAdminBudgetResponsibility,
} from "../../api/budgetPlanningApi";
import type {
  BudgetExercise,
  BudgetResponsibility,
  OrgCatalog,
  ResponsibilityType,
} from "../../types/budgetPlanning";
import { PageShell } from "../../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../../components/uiKit";
import { usePermissions } from "../../hooks/usePermissions";
import { resolveCostCenterIcon } from "../../utils/costCenterIcons";
import { hasScopesManageAccess } from "../../utils/permissions";
import {
  costCenterKey,
  formatCostCenterLabel,
} from "../../utils/orgCostCenters";
import {
  areaCatalogLabel,
  buildCreateSummary,
  catalogLabel,
  displayUser,
  exerciseLabel,
  filterAreasForUnit,
  filterCostCenters,
  formatDateBr,
  formatValidity,
  mergeResponsibilityPairs,
  responsibilityTypeLabel,
  unitCatalogLabel,
  validateValidityRange,
  type ResponsibilityPair,
} from "../../utils/responsibilities";

type PanelMode = "none" | "create" | "edit";

const emptyCreate = {
  exercise_id: "",
  unit_id: "",
  area_id: "",
  cost_center_id: "",
  responsibility_type: "owner" as ResponsibilityType,
  valid_from: "",
  valid_until: "",
};

function userInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] ?? ""}${parts[parts.length - 1][0] ?? ""}`.toUpperCase();
}

function findCostCenterIcon(
  catalog: OrgCatalog | null,
  unitId: string | null | undefined,
  code: string | null | undefined,
) {
  if (!catalog || !code) return null;
  const row = catalog.cost_centers.find(
    (cc) =>
      cc.code === code &&
      (!unitId || cc.branch === unitId || cc.unit_code === unitId),
  );
  return row?.icon_key ?? null;
}

export function AdminResponsaveisPage() {
  const { profile, loading: permLoading } = usePermissions();
  const canAccess = hasScopesManageAccess(profile);

  const [exercises, setExercises] = useState<BudgetExercise[]>([]);
  const [catalog, setCatalog] = useState<OrgCatalog | null>(null);
  const [items, setItems] = useState<BudgetResponsibility[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [panel, setPanel] = useState<PanelMode>("none");
  const [editing, setEditing] = useState<ResponsibilityPair | null>(null);

  const [filterExercise, setFilterExercise] = useState("");
  const [filterUnit, setFilterUnit] = useState("");
  const [filterArea, setFilterArea] = useState("");
  const [filterCc, setFilterCc] = useState("");
  const [filterType, setFilterType] = useState<ResponsibilityType | "">("");
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "inactive">("all");
  const [filterUsers, setFilterUsers] = useState<DirectoryUser[]>([]);

  const [createForm, setCreateForm] = useState(emptyCreate);
  const [selectedUsers, setSelectedUsers] = useState<DirectoryUser[]>([]);
  const [editType, setEditType] = useState<ResponsibilityType>("owner");
  const [editFrom, setEditFrom] = useState("");
  const [editUntil, setEditUntil] = useState("");

  const loadMeta = useCallback(async (signal?: AbortSignal) => {
    const [exList, scopes] = await Promise.all([
      listAdminExercises(signal),
      listAdminScopes(signal),
    ]);
    setExercises(exList);
    setCatalog(scopes.catalog);
    if (!createForm.exercise_id) {
      const preferred =
        exList.find((e) => e.is_active) ?? exList.find((e) => e.status === "open") ?? exList[0];
      if (preferred) {
        setCreateForm((f) => ({ ...f, exercise_id: preferred.id }));
        setFilterExercise((prev) => prev || preferred.id);
      }
    }
  }, [createForm.exercise_id]);

  const loadList = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setListError(null);
      try {
        const result = await listAdminBudgetResponsibilities(
          {
            exercise_id: filterExercise || undefined,
            module: undefined,
            user_sub: filterUsers[0]?.id,
            unit_id: filterUnit || undefined,
            area_id: filterArea || undefined,
            cost_center_id: filterCc || undefined,
            is_active:
              filterStatus === "all" ? null : filterStatus === "active",
            responsibility_type: filterType,
            page,
            page_size: pageSize,
          },
          signal,
        );
        setItems(result.items);
        setTotal(result.pagination.total);
        setHasMore(result.pagination.has_more);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setListError("Sessão expirada (401). Faça login novamente.");
        } else if (err instanceof HttpRequestError && err.status === 403) {
          setListError("Acesso negado (403) para listar responsabilidades.");
        } else {
          setListError(err instanceof Error ? err.message : "Erro ao carregar a listagem.");
        }
        setItems([]);
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [
      filterArea,
      filterCc,
      filterExercise,
      filterStatus,
      filterType,
      filterUnit,
      filterUsers,
      page,
      pageSize,
    ],
  );

  useEffect(() => {
    if (permLoading) return;
    if (!canAccess) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    loadMeta(controller.signal).catch((err: unknown) => {
      if (!controller.signal.aborted) {
        setListError(err instanceof Error ? err.message : "Erro ao carregar catálogo.");
      }
    });
    return () => controller.abort();
  }, [canAccess, loadMeta, permLoading]);

  useEffect(() => {
    if (permLoading || !canAccess) return;
    const controller = new AbortController();
    void loadList(controller.signal);
    return () => controller.abort();
  }, [canAccess, loadList, permLoading]);

  const filterAreas = useMemo(
    () => filterAreasForUnit(catalog, filterUnit),
    [catalog, filterUnit],
  );
  const filterCcs = useMemo(
    () => filterCostCenters(catalog, filterUnit, filterArea),
    [catalog, filterArea, filterUnit],
  );

  const createAreas = useMemo(
    () => filterAreasForUnit(catalog, createForm.unit_id),
    [catalog, createForm.unit_id],
  );
  const createCcs = useMemo(
    () => filterCostCenters(catalog, createForm.unit_id, createForm.area_id),
    [catalog, createForm.area_id, createForm.unit_id],
  );

  const createSummary = useMemo(() => {
    const user = selectedUsers[0];
    if (!user || !createForm.cost_center_id || !createForm.exercise_id) return null;
    const exercise = exercises.find((e) => e.id === createForm.exercise_id);
    const ccLabel = catalogLabel(
      catalog?.cost_centers ?? [],
      createForm.cost_center_id,
      createForm.unit_id,
    );
    return buildCreateSummary({
      userName: user.name || user.email || user.id,
      costCenterLabel: ccLabel,
      exerciseYear: exercise?.year ?? "—",
      type: createForm.responsibility_type,
    });
  }, [catalog, createForm, exercises, selectedUsers]);

  const pairs = useMemo(() => mergeResponsibilityPairs(items), [items]);
  const activePairsOnPage = useMemo(
    () => pairs.filter((pair) => pair.is_active).length,
    [pairs],
  );
  const inactivePairsOnPage = pairs.length - activePairsOnPage;
  const filterExerciseLabel = filterExercise
    ? exerciseLabel(exercises, filterExercise)
    : "Todos os exercícios";

  function openCreate() {
    setPanel("create");
    setFormError(null);
    setSuccessMsg(null);
    setSelectedUsers([]);
    setCreateForm((f) => ({
      ...emptyCreate,
      exercise_id: filterExercise || f.exercise_id || exercises[0]?.id || "",
    }));
  }

  function openEdit(pair: ResponsibilityPair) {
    setPanel("edit");
    setEditing(pair);
    setEditType(pair.responsibility_type as ResponsibilityType);
    setEditFrom(pair.valid_from?.slice(0, 10) ?? "");
    setEditUntil(pair.valid_until?.slice(0, 10) ?? "");
    setFormError(null);
    setSuccessMsg(null);
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (saving) return;
    const user = selectedUsers[0];
    if (!user?.id) {
      setFormError("Selecione um usuário no diretório Minha DELPI.");
      return;
    }
    if (!createForm.exercise_id || !createForm.unit_id || !createForm.cost_center_id) {
      setFormError("Preencha exercício, unidade e centro de custo.");
      return;
    }
    const validityError = validateValidityRange(
      createForm.valid_from || null,
      createForm.valid_until || null,
    );
    if (validityError) {
      setFormError(validityError);
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const pair = await createAdminBudgetResponsibilityPair({
        exercise_id: createForm.exercise_id,
        user_sub: user.id,
        user_name_snapshot: user.name,
        user_email_snapshot: user.email,
        unit_id: createForm.unit_id,
        area_id: createForm.area_id || null,
        cost_center_id: createForm.cost_center_id,
        responsibility_type: createForm.responsibility_type,
        valid_from: createForm.valid_from || null,
        valid_until: createForm.valid_until || null,
      });
      const parts = [
        pair.capex ? "CAPEX" : null,
        pair.personnel ? "Pessoal" : null,
      ].filter(Boolean);
      setSuccessMsg(
        parts.length === 2
          ? "Vínculo cadastrado (CAPEX + Pessoal). O usuário elabora os dois módulos neste centro."
          : `Vínculo atualizado (${parts.join(" + ")}). Módulo complementar criado neste centro.`,
      );
      setPanel("none");
      setPage(1);
      await loadList();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Falha ao salvar.");
    } finally {
      setSaving(false);
    }
  }

  async function handleEdit(event: FormEvent) {
    event.preventDefault();
    if (!editing || saving) return;
    const validityError = validateValidityRange(editFrom || null, editUntil || null);
    if (validityError) {
      setFormError(validityError);
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const targets = editing.rows.filter((row) => row.is_active);
      await Promise.all(
        targets.map((row) =>
          updateAdminBudgetResponsibility(row.id, {
            responsibility_type: editType,
            valid_from: editFrom || null,
            valid_until: editUntil || null,
          }),
        ),
      );
      setSuccessMsg("Tipo e vigência atualizados nos módulos do vínculo.");
      setPanel("none");
      setEditing(null);
      await loadList();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Falha ao atualizar.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(pair: ResponsibilityPair) {
    if (
      !window.confirm(
        `Desativar o vínculo de ${displayUser(pair)} com ${formatCostCenterLabel({
          branch: pair.branch ?? pair.unit_id,
          code: pair.cost_center_id,
        })}? Isso remove CAPEX e Pessoal neste centro.`,
      )
    ) {
      return;
    }
    setFormError(null);
    try {
      const targets = pair.rows.filter((row) => row.is_active);
      await Promise.all(
        targets.map((row) =>
          deactivateAdminBudgetResponsibility(row.id, "Desativação pela administração"),
        ),
      );
      setSuccessMsg("Vínculo desativado (CAPEX e Pessoal).");
      await loadList();
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : "Falha ao desativar.");
    }
  }

  async function handleReactivate(pair: ResponsibilityPair) {
    setFormError(null);
    try {
      const targets = pair.rows.filter((row) => !row.is_active);
      await Promise.all(
        targets.map((row) => reactivateAdminBudgetResponsibility(row.id)),
      );
      setSuccessMsg("Vínculo reativado (CAPEX e Pessoal).");
      await loadList();
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : "Falha ao reativar.");
    }
  }

  if (permLoading) {
    return (
      <PageShell title="Responsáveis orçamentários" subtitle="Administração">
        <LoadingActivityCard title="Verificando permissões…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell title="Responsáveis orçamentários" subtitle="Acesso restrito.">
        <StateBox variant="error" dismissible={false}>
          Sem permissão para gerenciar responsáveis (scopes.manage ou admin).
        </StateBox>
      </PageShell>
    );
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

  return (
    <PageShell
      title="Responsáveis orçamentários"
      subtitle="Cada vínculo libera CAPEX e Pessoal no mesmo centro de custo."
      icon={<Network size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="admin"
    >
      {successMsg ? (
        <StateBox variant="success" dismissible={false}>
          {successMsg}
        </StateBox>
      ) : null}
      {listError ? (
        <StateBox variant="error" dismissible={false}>
          {listError}
        </StateBox>
      ) : null}

      <section className="po-resp-admin" aria-label="Administração de responsáveis">
        <div className="po-resp-admin__hero">
          <div>
            <p className="po-resp-admin__eyebrow">Administração · Elaboração</p>
            <h2 className="po-resp-admin__title">Responsáveis</h2>
            <p className="po-resp-admin__lead">
              Escopos administrativos não substituem este cadastro. O vínculo libera a
              elaboração de CAPEX e Pessoal no centro de custo escolhido.
            </p>
          </div>
          <aside className="po-resp-admin__hero-panel" aria-label="Resumo da listagem">
            <dl className="po-resp-admin__meta">
              <div>
                <dt>Total</dt>
                <dd>{loading ? "…" : total}</dd>
              </div>
              <div>
                <dt>Ativos</dt>
                <dd>{loading ? "…" : activePairsOnPage}</dd>
              </div>
              <div>
                <dt>Inativos</dt>
                <dd>{loading ? "…" : inactivePairsOnPage}</dd>
              </div>
            </dl>
            <p className="po-resp-admin__hero-note">
              <Filter size={14} aria-hidden="true" />
              {filterExerciseLabel}
              {filterUsers[0] ? ` · ${filterUsers[0].name || filterUsers[0].email}` : ""}
            </p>
            <button type="button" className="po-btn po-btn--primary" onClick={openCreate}>
              <UserPlus size={16} aria-hidden="true" />
              Novo vínculo
            </button>
          </aside>
        </div>

        <SectionCard
          title="Filtros"
          hint="Filtros enviados ao backend, inclusive tipo de responsabilidade."
        >
          <div className="po-resp-admin__filters">
            <div className="po-filter-grid">
              <label>
                Exercício
                <select
                  value={filterExercise}
                  onChange={(e) => {
                    setPage(1);
                    setFilterExercise(e.target.value);
                  }}
                >
                  <option value="">Todos</option>
                  {exercises.map((ex) => (
                    <option key={ex.id} value={ex.id}>
                      {ex.year} — {ex.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Unidade
                <select
                  value={filterUnit}
                  onChange={(e) => {
                    setPage(1);
                    setFilterUnit(e.target.value);
                    setFilterArea("");
                    setFilterCc("");
                  }}
                >
                  <option value="">Todas</option>
                  {(catalog?.units ?? []).map((u) => (
                    <option key={u.code} value={u.code}>
                      {u.code} — {u.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Área
                <select
                  value={filterArea}
                  onChange={(e) => {
                    setPage(1);
                    setFilterArea(e.target.value);
                    setFilterCc("");
                  }}
                >
                  <option value="">Todas</option>
                  {filterAreas.map((a) => (
                    <option key={a.code} value={a.code}>
                      {a.code} — {a.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Centro de custo
                <select
                  value={filterCc}
                  onChange={(e) => {
                    setPage(1);
                    setFilterCc(e.target.value);
                  }}
                >
                  <option value="">Todos</option>
                  {filterCcs.map((cc) => (
                    <option key={costCenterKey(cc)} value={cc.code}>
                      {formatCostCenterLabel(cc)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Tipo
                <select
                  value={filterType}
                  onChange={(e) => {
                    setPage(1);
                    setFilterType(e.target.value as ResponsibilityType | "");
                  }}
                >
                  <option value="">Todos</option>
                  <option value="owner">Responsável</option>
                  <option value="collaborator">Colaborador</option>
                </select>
              </label>
              <label>
                Status
                <select
                  value={filterStatus}
                  onChange={(e) => {
                    setPage(1);
                    setFilterStatus(e.target.value as "all" | "active" | "inactive");
                  }}
                >
                  <option value="all">Todos</option>
                  <option value="active">Ativo</option>
                  <option value="inactive">Inativo</option>
                </select>
              </label>
            </div>
            <div className="po-resp-admin__user-filter">
              <UserDirectoryPicker
                value={filterUsers}
                onChange={(users) => {
                  setPage(1);
                  setFilterUsers(users);
                }}
                searchUsers={searchDirectoryUsers}
                maxSelected={1}
                showEmail
                labels={{
                  title: "Usuário",
                  hint: "Filtrar por colaborador (diretório).",
                  placeholder: "Pesquisar usuário…",
                }}
              />
            </div>
          </div>
        </SectionCard>

        {panel === "create" ? (
          <SectionCard
            title="Novo vínculo"
            hint="Usuário e centro de custo não podem ser alterados depois — desative e crie outro se precisar trocar."
          >
            <form className="po-resp-admin__form" onSubmit={(e) => void handleCreate(e)}>
              <div className="po-resp-admin__form-grid">
                <label>
                  Exercício
                  <select
                    required
                    value={createForm.exercise_id}
                    onChange={(e) =>
                      setCreateForm((f) => ({ ...f, exercise_id: e.target.value }))
                    }
                  >
                    <option value="">Selecione…</option>
                    {exercises
                      .filter((ex) => ex.status !== "archived")
                      .map((ex) => (
                        <option key={ex.id} value={ex.id}>
                          {ex.year} — {ex.name}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Filial
                  <select
                    required
                    value={createForm.unit_id}
                    onChange={(e) =>
                      setCreateForm((f) => ({
                        ...f,
                        unit_id: e.target.value,
                        area_id: "",
                        cost_center_id: "",
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
                  Área
                  <select
                    disabled={!createForm.unit_id}
                    value={createForm.area_id}
                    onChange={(e) =>
                      setCreateForm((f) => ({
                        ...f,
                        area_id: e.target.value,
                        cost_center_id: "",
                      }))
                    }
                  >
                    <option value="">Opcional…</option>
                    {createAreas.map((a) => (
                      <option key={a.code} value={a.code}>
                        {a.code} — {a.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Centro de custo
                  <select
                    required
                    disabled={!createForm.unit_id}
                    value={createForm.cost_center_id}
                    onChange={(e) =>
                      setCreateForm((f) => ({ ...f, cost_center_id: e.target.value }))
                    }
                  >
                    <option value="">
                      {createForm.unit_id ? "Selecione…" : "Selecione a filial primeiro"}
                    </option>
                    {createCcs.map((cc) => (
                      <option key={costCenterKey(cc)} value={cc.code}>
                        {formatCostCenterLabel(cc)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Tipo
                  <select
                    value={createForm.responsibility_type}
                    onChange={(e) =>
                      setCreateForm((f) => ({
                        ...f,
                        responsibility_type: e.target.value as ResponsibilityType,
                      }))
                    }
                  >
                    <option value="owner">Responsável</option>
                    <option value="collaborator">Colaborador</option>
                  </select>
                </label>
                <label>
                  Vigência início
                  <input
                    type="date"
                    value={createForm.valid_from}
                    onChange={(e) =>
                      setCreateForm((f) => ({ ...f, valid_from: e.target.value }))
                    }
                  />
                </label>
                <label>
                  Vigência fim
                  <input
                    type="date"
                    value={createForm.valid_until}
                    onChange={(e) =>
                      setCreateForm((f) => ({ ...f, valid_until: e.target.value }))
                    }
                  />
                </label>
              </div>
              <div className="po-resp-admin__picker">
                <UserDirectoryPicker
                  value={selectedUsers}
                  onChange={setSelectedUsers}
                  searchUsers={searchDirectoryUsers}
                  maxSelected={1}
                  showEmail
                  labels={{
                    title: "Colaborador",
                    hint: "Obrigatório selecionar no diretório (sem digitação de sub).",
                    placeholder: "Pesquisar por nome ou e-mail…",
                  }}
                />
              </div>
              {createSummary ? (
                <StateBox variant="warning" dismissible={false}>
                  {createSummary}
                </StateBox>
              ) : null}
              {formError ? (
                <StateBox variant="error" dismissible={false}>
                  {formError}
                </StateBox>
              ) : null}
              <div className="po-form-actions">
                <button className="po-btn po-btn--primary" type="submit" disabled={saving}>
                  {saving ? "Salvando…" : "Salvar vínculo"}
                </button>
                <button
                  className="po-btn po-btn--secondary"
                  type="button"
                  disabled={saving}
                  onClick={() => setPanel("none")}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </SectionCard>
        ) : null}

        {panel === "edit" && editing ? (
          <SectionCard
            title="Alterar tipo e vigência"
            hint="Para trocar usuário ou centro de custo, desative este vínculo e cadastre um novo."
          >
            <div className="po-resp-admin__edit-banner">
              <span className="po-resp-admin__avatar" aria-hidden="true">
                {userInitials(displayUser(editing))}
              </span>
              <div>
                <strong>{displayUser(editing)}</strong>
                <p className="po-muted">
                  {catalogLabel(
                    catalog?.cost_centers ?? [],
                    editing.cost_center_id,
                    editing.branch ?? editing.unit_id,
                  )}{" "}
                  · {exerciseLabel(exercises, editing.exercise_id)}
                  {" · "}
                  {[
                    editing.capex ? "CAPEX" : null,
                    editing.personnel ? "Pessoal" : null,
                  ]
                    .filter(Boolean)
                    .join(" + ")}
                </p>
              </div>
            </div>
            <form className="po-resp-admin__form" onSubmit={(e) => void handleEdit(e)}>
              <div className="po-resp-admin__form-grid po-resp-admin__form-grid--edit">
                <label>
                  Tipo
                  <select
                    value={editType}
                    onChange={(e) => setEditType(e.target.value as ResponsibilityType)}
                  >
                    <option value="owner">Responsável</option>
                    <option value="collaborator">Colaborador</option>
                  </select>
                </label>
                <label>
                  Vigência início
                  <input
                    type="date"
                    value={editFrom}
                    onChange={(e) => setEditFrom(e.target.value)}
                  />
                </label>
                <label>
                  Vigência fim
                  <input
                    type="date"
                    value={editUntil}
                    onChange={(e) => setEditUntil(e.target.value)}
                  />
                </label>
              </div>
              {formError ? (
                <StateBox variant="error" dismissible={false}>
                  {formError}
                </StateBox>
              ) : null}
              <div className="po-form-actions">
                <button className="po-btn po-btn--primary" type="submit" disabled={saving}>
                  {saving ? "Salvando…" : "Salvar alterações"}
                </button>
                <button
                  className="po-btn po-btn--secondary"
                  type="button"
                  onClick={() => {
                    setPanel("none");
                    setEditing(null);
                  }}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </SectionCard>
        ) : null}

        <div className="po-resp-admin__list-head">
          <div>
            <h3 className="po-resp-admin__section-title">Vínculos</h3>
            <p className="po-muted">
              {loading
                ? "Carregando…"
                : `${pairs.length} vínculo(s) nesta página · ${total} registro(s) de módulo no filtro · página ${page} de ${totalPages}`}
            </p>
          </div>
          <span className="po-resp-admin__list-chip">
            <Users size={14} aria-hidden="true" />
            CAPEX + Pessoal por centro
          </span>
        </div>

        {loading ? (
          <div className="po-skeleton-stack" aria-busy="true" aria-label="Carregando listagem">
            <div className="po-skeleton" />
            <div className="po-skeleton" />
            <div className="po-skeleton" />
          </div>
        ) : null}

        {!loading && pairs.length === 0 ? (
          <StateBox variant="default" dismissible={false}>
            Nenhum vínculo encontrado para os filtros selecionados.
          </StateBox>
        ) : null}

        {!loading && pairs.length > 0 ? (
          <ul className="po-resp-admin__grid">
            {pairs.map((pair) => {
              const name = displayUser(pair);
              const iconKey = findCostCenterIcon(
                catalog,
                pair.branch ?? pair.unit_id,
                pair.cost_center_id,
              );
              const CcIcon = resolveCostCenterIcon(iconKey);
              return (
                <li
                  key={pair.key}
                  className={
                    pair.is_active
                      ? "po-resp-admin__card"
                      : "po-resp-admin__card is-inactive"
                  }
                >
                  <div className="po-resp-admin__card-top">
                    <div className="po-resp-admin__identity">
                      <span className="po-resp-admin__avatar" aria-hidden="true">
                        {userInitials(name)}
                      </span>
                      <div>
                        <strong>{name}</strong>
                        <p className="po-muted">
                          {pair.user_email_snapshot || pair.user_sub}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`po-badge ${pair.is_active ? "po-badge--success" : "po-badge--muted"}`}
                    >
                      {pair.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </div>

                  <div className="po-resp-admin__chips">
                    {pair.capex ? (
                      <span className="po-resp-admin__chip">CAPEX</span>
                    ) : null}
                    {pair.personnel ? (
                      <span className="po-resp-admin__chip">Pessoal</span>
                    ) : null}
                    <span className="po-resp-admin__chip po-resp-admin__chip--soft">
                      {responsibilityTypeLabel(pair.responsibility_type)}
                    </span>
                  </div>

                  <div className="po-resp-admin__cc">
                    <span className="po-resp-admin__cc-icon" aria-hidden="true">
                      <CcIcon size={16} />
                    </span>
                    <div>
                      <p className="po-resp-admin__cc-label">
                        {catalogLabel(
                          catalog?.cost_centers ?? [],
                          pair.cost_center_id,
                          pair.branch ?? pair.unit_id,
                        )}
                      </p>
                      <p className="po-muted">
                        {unitCatalogLabel(catalog?.units ?? [], pair.unit_id)}
                        {pair.area_id
                          ? ` · ${areaCatalogLabel(catalog?.areas ?? [], pair.area_id)}`
                          : ""}
                      </p>
                    </div>
                  </div>

                  <dl className="po-resp-admin__card-meta">
                    <div>
                      <dt>Exercício</dt>
                      <dd>{exerciseLabel(exercises, pair.exercise_id)}</dd>
                    </div>
                    <div>
                      <dt>Vigência</dt>
                      <dd>{formatValidity(pair.valid_from, pair.valid_until)}</dd>
                    </div>
                    <div>
                      <dt>Atualizado</dt>
                      <dd>
                        {formatDateBr(
                          pair.updated_at?.slice(0, 10) ?? pair.created_at?.slice(0, 10),
                        )}
                      </dd>
                    </div>
                  </dl>

                  <div className="po-resp-admin__actions">
                    {pair.is_active ? (
                      <>
                        <button
                          type="button"
                          className="po-btn po-btn--secondary po-btn--sm"
                          onClick={() => openEdit(pair)}
                        >
                          <Pencil size={14} aria-hidden="true" />
                          Editar
                        </button>
                        <button
                          type="button"
                          className="po-btn po-btn--secondary po-btn--sm"
                          onClick={() => void handleDeactivate(pair)}
                        >
                          <UserMinus size={14} aria-hidden="true" />
                          Desativar
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="po-btn po-btn--secondary po-btn--sm"
                        onClick={() => void handleReactivate(pair)}
                      >
                        <RotateCcw size={14} aria-hidden="true" />
                        Reativar
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        ) : null}

        {!loading && total > 0 ? (
          <div className="po-pagination po-resp-admin__pagination">
            <button
              type="button"
              className="po-btn po-btn--secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Anterior
            </button>
            <span className="po-muted">
              Página {page} de {totalPages}
              {hasMore ? " · há mais" : ""}
            </span>
            <button
              type="button"
              className="po-btn po-btn--secondary"
              disabled={!hasMore && page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Próxima
            </button>
          </div>
        ) : null}
      </section>
    </PageShell>
  );
}
