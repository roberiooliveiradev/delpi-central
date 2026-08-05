import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { UserDirectoryPicker } from "@delpi/plugin-ui/index";
import { Network, Pencil, RotateCcw, UserMinus, UserPlus } from "lucide-react";

import { searchDirectoryUsers, type DirectoryUser } from "../../api/directoryApi";
import { HttpRequestError } from "../../api/httpClient";
import {
  createAdminBudgetResponsibility,
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
import { hasScopesManageAccess } from "../../utils/permissions";
import {
  costCenterKey,
  formatCostCenterLabel,
} from "../../utils/orgCostCenters";
import {
  buildCreateSummary,
  catalogLabel,
  displayUser,
  exerciseLabel,
  filterAreasForUnit,
  filterCostCenters,
  formatDateBr,
  formatValidity,
  responsibilityTypeLabel,
  validateValidityRange,
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
  const [editing, setEditing] = useState<BudgetResponsibility | null>(null);

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
            module: "capex",
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

  function openEdit(row: BudgetResponsibility) {
    setPanel("edit");
    setEditing(row);
    setEditType(row.responsibility_type);
    setEditFrom(row.valid_from?.slice(0, 10) ?? "");
    setEditUntil(row.valid_until?.slice(0, 10) ?? "");
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
      await createAdminBudgetResponsibility({
        exercise_id: createForm.exercise_id,
        module: "capex",
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
      setSuccessMsg("Responsabilidade cadastrada com sucesso.");
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
      await updateAdminBudgetResponsibility(editing.id, {
        responsibility_type: editType,
        valid_from: editFrom || null,
        valid_until: editUntil || null,
      });
      setSuccessMsg("Tipo e vigência atualizados.");
      setPanel("none");
      setEditing(null);
      await loadList();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Falha ao atualizar.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(row: BudgetResponsibility) {
    if (
      !window.confirm(
        `Desativar o vínculo de ${displayUser(row)} com ${formatCostCenterLabel({
          branch: row.branch ?? row.unit_id,
          code: row.cost_center_id,
        })}?`,
      )
    ) {
      return;
    }
    setFormError(null);
    try {
      await deactivateAdminBudgetResponsibility(row.id, "Desativação pela administração");
      setSuccessMsg("Vínculo desativado.");
      await loadList();
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : "Falha ao desativar.");
    }
  }

  async function handleReactivate(row: BudgetResponsibility) {
    setFormError(null);
    try {
      await reactivateAdminBudgetResponsibility(row.id);
      setSuccessMsg("Vínculo reativado.");
      await loadList();
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : "Falha ao reativar.");
    }
  }

  if (permLoading) {
    return (
      <PageShell title="Responsáveis por Centro de Custo" subtitle="Administração">
        <LoadingActivityCard title="Verificando permissões…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell title="Responsáveis por Centro de Custo" subtitle="Acesso restrito.">
        <StateBox variant="error" dismissible={false}>
          Sem permissão para gerenciar responsáveis (scopes.manage ou admin).
        </StateBox>
      </PageShell>
    );
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

  return (
    <PageShell
      title="Responsáveis por Centro de Custo"
      subtitle="Vínculos orçamentários CAPEX por exercício e centro de custo do catálogo."
      icon={<Network size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="admin"
      actions={
        <button type="button" className="po-btn po-btn--primary" onClick={openCreate}>
          <UserPlus size={16} aria-hidden="true" />
          Novo vínculo
        </button>
      }
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

      <SectionCard title="Filtros" hint="Filtros enviados ao backend, inclusive tipo de responsabilidade.">
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
        <div className="po-form" style={{ marginTop: 12 }}>
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
      </SectionCard>

      {panel === "create" ? (
        <SectionCard title="Novo vínculo" hint="Usuário e centro de custo não podem ser alterados depois — desative e crie outro se precisar trocar.">
          <form className="po-form" onSubmit={(e) => void handleCreate(e)}>
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
          <p className="po-muted">
            {displayUser(editing)} ·{" "}
            {catalogLabel(
              catalog?.cost_centers ?? [],
              editing.cost_center_id,
              editing.branch ?? editing.unit_id,
            )}{" "}
            · {exerciseLabel(exercises, editing.exercise_id)}
          </p>
          <form className="po-form" onSubmit={(e) => void handleEdit(e)}>
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
              <input type="date" value={editFrom} onChange={(e) => setEditFrom(e.target.value)} />
            </label>
            <label>
              Vigência fim
              <input type="date" value={editUntil} onChange={(e) => setEditUntil(e.target.value)} />
            </label>
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

      <SectionCard
        title="Vínculos"
        hint={loading ? "Carregando…" : `${total} registro(s) no filtro atual.`}
      >
        {loading ? (
          <div className="po-skeleton-stack" aria-busy="true" aria-label="Carregando listagem">
            <div className="po-skeleton" />
            <div className="po-skeleton" />
            <div className="po-skeleton" />
          </div>
        ) : null}

        {!loading && items.length === 0 ? (
          <StateBox variant="default" dismissible={false}>
            Nenhum vínculo encontrado para os filtros selecionados.
          </StateBox>
        ) : null}

        {!loading && items.length > 0 ? (
          <ul className="po-resp-list">
            {items.map((row) => (
              <li key={row.id} className="po-resp-card">
                <div className="po-resp-card__main">
                  <strong>{displayUser(row)}</strong>
                  <span className="po-muted">{row.user_email_snapshot || row.user_sub}</span>
                  <dl className="po-detail-grid">
                    <div>
                      <dt>Exercício</dt>
                      <dd>{exerciseLabel(exercises, row.exercise_id)}</dd>
                    </div>
                    <div>
                      <dt>Filial</dt>
                      <dd>{catalogLabel(catalog?.units ?? [], row.unit_id)}</dd>
                    </div>
                    <div>
                      <dt>Área</dt>
                      <dd>{catalogLabel(catalog?.areas ?? [], row.area_id)}</dd>
                    </div>
                    <div>
                      <dt>Centro de custo</dt>
                      <dd>
                        {catalogLabel(
                          catalog?.cost_centers ?? [],
                          row.cost_center_id,
                          row.branch ?? row.unit_id,
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt>Tipo</dt>
                      <dd>{responsibilityTypeLabel(row.responsibility_type)}</dd>
                    </div>
                    <div>
                      <dt>Vigência</dt>
                      <dd>{formatValidity(row.valid_from, row.valid_until)}</dd>
                    </div>
                    <div>
                      <dt>Status</dt>
                      <dd>
                        <span
                          className={`po-badge ${row.is_active ? "po-badge--success" : "po-badge--muted"}`}
                        >
                          {row.is_active ? "Ativo" : "Inativo"}
                        </span>
                      </dd>
                    </div>
                    <div>
                      <dt>Última alteração</dt>
                      <dd>{formatDateBr(row.updated_at?.slice(0, 10) ?? row.created_at?.slice(0, 10))}</dd>
                    </div>
                  </dl>
                </div>
                <div className="po-form-actions">
                  {row.is_active ? (
                    <>
                      <button
                        type="button"
                        className="po-btn po-btn--secondary"
                        onClick={() => openEdit(row)}
                      >
                        <Pencil size={14} aria-hidden="true" />
                        Editar
                      </button>
                      <button
                        type="button"
                        className="po-btn po-btn--secondary"
                        onClick={() => void handleDeactivate(row)}
                      >
                        <UserMinus size={14} aria-hidden="true" />
                        Desativar
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      className="po-btn po-btn--secondary"
                      onClick={() => void handleReactivate(row)}
                    >
                      <RotateCcw size={14} aria-hidden="true" />
                      Reativar
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : null}

        {!loading && total > 0 ? (
          <div className="po-pagination">
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
      </SectionCard>
    </PageShell>
  );
}
