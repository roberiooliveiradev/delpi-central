import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Layers, Pencil, RotateCcw, Tags, UserMinus } from "lucide-react";

import { HttpRequestError } from "../../api/httpClient";
import {
  createAdminCapexCategory,
  deactivateAdminCapexCategory,
  listAdminCapexCategories,
  reactivateAdminCapexCategory,
  updateAdminCapexCategory,
} from "../../api/budgetPlanningApi";
import type { CapexCategory } from "../../types/budgetPlanning";
import { PageShell } from "../../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../../components/uiKit";
import { usePermissions } from "../../hooks/usePermissions";
import { hasScopesManageAccess } from "../../utils/permissions";

type PanelMode = "none" | "create" | "edit";

const emptyCreate = {
  code: "",
  name: "",
  description: "",
  display_order: 0,
};

export function AdminCategoriasCapexPage() {
  const { profile, loading: permLoading } = usePermissions();
  const canAccess = hasScopesManageAccess(profile);

  const [items, setItems] = useState<CapexCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [panel, setPanel] = useState<PanelMode>("none");
  const [editing, setEditing] = useState<CapexCategory | null>(null);

  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "inactive">("all");
  const [filterQ, setFilterQ] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const [createForm, setCreateForm] = useState(emptyCreate);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editOrder, setEditOrder] = useState(0);

  const loadList = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setListError(null);
      try {
        const result = await listAdminCapexCategories(
          {
            is_active:
              filterStatus === "all" ? null : filterStatus === "active",
            q: filterQ || undefined,
          },
          signal,
        );
        setItems(result.items ?? []);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setListError("Sessão expirada (401). Faça login novamente.");
        } else if (err instanceof HttpRequestError && err.status === 403) {
          setListError("Acesso negado (403) para listar categorias CAPEX.");
        } else {
          setListError(err instanceof Error ? err.message : "Erro ao carregar categorias.");
        }
        setItems([]);
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [filterQ, filterStatus],
  );

  useEffect(() => {
    if (permLoading || !canAccess) {
      if (!permLoading && !canAccess) setLoading(false);
      return;
    }
    const controller = new AbortController();
    void loadList(controller.signal);
    return () => controller.abort();
  }, [canAccess, loadList, permLoading]);

  function openCreate() {
    setPanel("create");
    setCreateForm(emptyCreate);
    setFormError(null);
    setSuccessMsg(null);
  }

  function openEdit(row: CapexCategory) {
    setPanel("edit");
    setEditing(row);
    setEditName(row.name);
    setEditDescription(row.description ?? "");
    setEditOrder(row.display_order);
    setFormError(null);
    setSuccessMsg(null);
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (saving) return;
    if (!createForm.code.trim() || !createForm.name.trim()) {
      setFormError("Informe código e nome da categoria.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await createAdminCapexCategory({
        code: createForm.code.trim(),
        name: createForm.name.trim(),
        description: createForm.description.trim() || null,
        display_order: Number(createForm.display_order) || 0,
      });
      setSuccessMsg("Categoria criada com sucesso.");
      setPanel("none");
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
    if (!editName.trim()) {
      setFormError("Nome da categoria é obrigatório.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await updateAdminCapexCategory(editing.id, {
        name: editName.trim(),
        description: editDescription.trim() || null,
        display_order: Number(editOrder) || 0,
      });
      setSuccessMsg("Categoria atualizada.");
      setPanel("none");
      setEditing(null);
      await loadList();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Falha ao atualizar.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(row: CapexCategory) {
    if (
      !window.confirm(
        `Desativar a categoria "${row.name}"? Ela deixará de aparecer no cadastro futuro de investimentos.`,
      )
    ) {
      return;
    }
    setFormError(null);
    try {
      await deactivateAdminCapexCategory(row.id);
      setSuccessMsg("Categoria desativada.");
      await loadList();
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : "Falha ao desativar.");
    }
  }

  async function handleReactivate(row: CapexCategory) {
    setFormError(null);
    try {
      await reactivateAdminCapexCategory(row.id);
      setSuccessMsg("Categoria reativada.");
      await loadList();
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : "Falha ao reativar.");
    }
  }

  if (permLoading) {
    return (
      <PageShell title="Categorias de Investimento" subtitle="Administração">
        <LoadingActivityCard title="Verificando permissões…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell title="Categorias de Investimento" subtitle="Acesso restrito.">
        <StateBox variant="error" dismissible={false}>
          Sem permissão para gerenciar categorias CAPEX (scopes.manage ou admin).
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Categorias de Investimento"
      subtitle="Catálogo administrável de categorias CAPEX (não confundir com conta contábil do ERP)."
      icon={<Tags size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="admin"
      actions={
        <button type="button" className="po-btn po-btn--primary" onClick={openCreate}>
          <Layers size={16} aria-hidden="true" />
          Nova categoria
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

      <SectionCard title="Filtros" hint="Pesquisa e status enviados ao backend.">
        <div className="po-filter-grid">
          <label>
            Pesquisar
            <input
              type="search"
              value={searchInput}
              placeholder="Código, nome ou descrição…"
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") setFilterQ(searchInput.trim());
              }}
            />
          </label>
          <label>
            Status
            <select
              value={filterStatus}
              onChange={(e) =>
                setFilterStatus(e.target.value as "all" | "active" | "inactive")
              }
            >
              <option value="all">Todos</option>
              <option value="active">Ativas</option>
              <option value="inactive">Inativas</option>
            </select>
          </label>
        </div>
        <div className="po-form-actions" style={{ marginTop: 12 }}>
          <button
            type="button"
            className="po-btn po-btn--secondary"
            onClick={() => setFilterQ(searchInput.trim())}
          >
            Aplicar pesquisa
          </button>
        </div>
      </SectionCard>

      {panel === "create" ? (
        <SectionCard title="Nova categoria" hint="O código será imutável após salvar.">
          <form className="po-form" onSubmit={(e) => void handleCreate(e)}>
            <label>
              Código
              <input
                required
                value={createForm.code}
                placeholder="Ex.: FERRAMENTAS"
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))
                }
              />
            </label>
            <label>
              Nome
              <input
                required
                value={createForm.name}
                onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))}
              />
            </label>
            <label>
              Descrição
              <textarea
                rows={3}
                value={createForm.description}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, description: e.target.value }))
                }
              />
            </label>
            <label>
              Ordem
              <input
                type="number"
                value={createForm.display_order}
                onChange={(e) =>
                  setCreateForm((f) => ({
                    ...f,
                    display_order: Number(e.target.value) || 0,
                  }))
                }
              />
            </label>
            {formError ? (
              <StateBox variant="error" dismissible={false}>
                {formError}
              </StateBox>
            ) : null}
            <div className="po-form-actions">
              <button className="po-btn po-btn--primary" type="submit" disabled={saving}>
                {saving ? "Salvando…" : "Salvar categoria"}
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
          title="Editar categoria"
          hint="Nome, descrição e ordem. O código não pode ser alterado."
        >
          <p className="po-muted">
            Código: <strong>{editing.code}</strong>
            {editing.is_system_default ? " · origem padrão do sistema" : " · cadastrada administrativamente"}
          </p>
          <form className="po-form" onSubmit={(e) => void handleEdit(e)}>
            <label>
              Nome
              <input required value={editName} onChange={(e) => setEditName(e.target.value)} />
            </label>
            <label>
              Descrição
              <textarea
                rows={3}
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
              />
            </label>
            <label>
              Ordem
              <input
                type="number"
                value={editOrder}
                onChange={(e) => setEditOrder(Number(e.target.value) || 0)}
              />
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
                disabled={saving}
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
        title="Categorias"
        hint={loading ? "Carregando…" : `${items.length} registro(s).`}
      >
        {loading ? (
          <div className="po-skeleton-stack" aria-busy="true" aria-label="Carregando categorias">
            <div className="po-skeleton" />
            <div className="po-skeleton" />
          </div>
        ) : null}

        {!loading && items.length === 0 ? (
          <StateBox variant="default" dismissible={false}>
            Nenhuma categoria encontrada para os filtros selecionados.
          </StateBox>
        ) : null}

        {!loading && items.length > 0 ? (
          <ul className="po-resp-list">
            {items.map((row) => (
              <li key={row.id} className="po-resp-card">
                <div className="po-resp-card__main">
                  <strong className="po-resp-card__title">{row.name}</strong>
                  <span className="po-muted">{row.code}</span>
                  <dl className="po-detail-grid">
                    <div>
                      <dt>Descrição</dt>
                      <dd>{row.description || "—"}</dd>
                    </div>
                    <div>
                      <dt>Ordem</dt>
                      <dd>{row.display_order}</dd>
                    </div>
                    <div>
                      <dt>Origem</dt>
                      <dd>{row.is_system_default ? "Padrão do sistema" : "Administrativa"}</dd>
                    </div>
                    <div>
                      <dt>Status</dt>
                      <dd>
                        <span
                          className={`po-badge ${row.is_active ? "po-badge--success" : "po-badge--muted"}`}
                        >
                          {row.is_active ? "Ativa" : "Inativa"}
                        </span>
                      </dd>
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
      </SectionCard>
    </PageShell>
  );
}
