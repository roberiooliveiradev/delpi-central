import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  Layers,
  Pencil,
  RotateCcw,
  Search,
  Tags,
  UserMinus,
} from "lucide-react";

import { HttpRequestError } from "../../api/httpClient";
import {
  createAdminCapexCategory,
  clearAdminCapexCategoryIconImage,
  deactivateAdminCapexCategory,
  listAdminCapexCategories,
  reactivateAdminCapexCategory,
  updateAdminCapexCategory,
  uploadAdminCapexCategoryIconImage,
} from "../../api/budgetPlanningApi";
import type { CapexCategory } from "../../types/budgetPlanning";
import { CapexCategoryVisual } from "../../components/CapexCategoryVisual";
import { CategoryVisualPicker } from "../../components/CategoryVisualPicker";
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
  icon_key: null as string | null,
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
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "inactive">("all");
  const [filterQ, setFilterQ] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const [createForm, setCreateForm] = useState(emptyCreate);
  const [pendingIconFile, setPendingIconFile] = useState<File | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editOrder, setEditOrder] = useState(0);
  const [editIconKey, setEditIconKey] = useState<string | null>(null);
  const [iconBusy, setIconBusy] = useState(false);

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

  const activeCount = useMemo(
    () => items.filter((row) => row.is_active).length,
    [items],
  );
  const inactiveCount = items.length - activeCount;
  const selected = useMemo(
    () => items.find((row) => row.id === selectedId) ?? null,
    [items, selectedId],
  );

  function openCreate() {
    setPanel("create");
    setCreateForm(emptyCreate);
    setPendingIconFile(null);
    setFormError(null);
    setSuccessMsg(null);
  }

  function openEdit(row: CapexCategory) {
    setSelectedId(row.id);
    setPanel("edit");
    setEditing(row);
    setEditName(row.name);
    setEditDescription(row.description ?? "");
    setEditOrder(row.display_order);
    setEditIconKey(row.icon_key ?? null);
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
      const created = await createAdminCapexCategory({
        code: createForm.code.trim(),
        name: createForm.name.trim(),
        description: createForm.description.trim() || null,
        display_order: Number(createForm.display_order) || 0,
        icon_key: createForm.icon_key,
      });
      if (pendingIconFile) {
        await uploadAdminCapexCategoryIconImage(created.id, pendingIconFile);
      }
      setSuccessMsg("Categoria criada com sucesso.");
      setPanel("none");
      setPendingIconFile(null);
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
        icon_key: editIconKey,
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
      if (selectedId === row.id) setSelectedId(null);
      await loadList();
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : "Falha ao desativar.");
    }
  }

  async function handleUploadEditIcon(file: File) {
    if (!editing) return;
    setIconBusy(true);
    setFormError(null);
    try {
      const updated = await uploadAdminCapexCategoryIconImage(editing.id, file);
      setEditing(updated);
      setItems((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
      setSuccessMsg("Imagem do ícone enviada.");
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Falha ao enviar imagem.");
    } finally {
      setIconBusy(false);
    }
  }

  async function handleClearEditIcon() {
    if (!editing) return;
    setIconBusy(true);
    setFormError(null);
    try {
      const updated = await clearAdminCapexCategoryIconImage(editing.id);
      setEditing(updated);
      setItems((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
      setSuccessMsg("Imagem do ícone removida.");
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Falha ao remover imagem.");
    } finally {
      setIconBusy(false);
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
      subtitle="Catálogo CAPEX — não confundir com conta contábil do ERP."
      icon={<Tags size={28} strokeWidth={1.75} aria-hidden="true" />}
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

      <section className="po-cat-admin" aria-label="Categorias de investimento CAPEX">
        <div className="po-cat-admin__hero">
          <div>
            <p className="po-cat-admin__eyebrow">Administração · CAPEX</p>
            <h2 className="po-cat-admin__title">Categorias</h2>
            <p className="po-cat-admin__lead">
              Grade compacta com ícone por categoria — escolha o visual para facilitar a
              identificação no cadastro de investimentos.
            </p>
          </div>
          <aside className="po-cat-admin__hero-panel" aria-label="Resumo do catálogo">
            <dl className="po-cat-admin__meta">
              <div>
                <dt>Total</dt>
                <dd>{loading ? "…" : items.length}</dd>
              </div>
              <div>
                <dt>Ativas</dt>
                <dd>{loading ? "…" : activeCount}</dd>
              </div>
              <div>
                <dt>Inativas</dt>
                <dd>{loading ? "…" : inactiveCount}</dd>
              </div>
            </dl>
            <button type="button" className="po-btn po-btn--primary" onClick={openCreate}>
              <Layers size={16} aria-hidden="true" />
              Nova categoria
            </button>
          </aside>
        </div>

        <SectionCard title="Filtros" hint="Pesquisa e status enviados ao backend.">
          <div className="po-cat-admin__filters">
            <label className="po-cat-admin__search">
              <span className="po-sr-only">Pesquisar</span>
              <Search size={16} aria-hidden="true" />
              <input
                type="search"
                aria-label="Pesquisar"
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
            <form className="po-cat-admin__form" onSubmit={(e) => void handleCreate(e)}>
              <div className="po-cat-admin__form-grid">
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
              </div>
              <div className="po-cat-admin__icon-field">
                <span>Visual (Lucide ou imagem)</span>
                <CategoryVisualPicker
                  label={createForm.name || "nova categoria"}
                  iconKey={createForm.icon_key}
                  busy={saving}
                  onSelectLucide={(next) =>
                    setCreateForm((f) => ({ ...f, icon_key: next }))
                  }
                  pendingFile={pendingIconFile}
                  pendingFileName={pendingIconFile?.name ?? null}
                  onPickPendingFile={setPendingIconFile}
                />
              </div>
              <label>
                Descrição
                <textarea
                  rows={2}
                  value={createForm.description}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, description: e.target.value }))
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
            hint="Nome, descrição, ordem e ícone. O código não pode ser alterado."
          >
            <p className="po-muted po-cat-admin__edit-code">
              Código: <strong>{editing.code}</strong>
              {editing.is_system_default
                ? " · origem padrão do sistema"
                : " · cadastrada administrativamente"}
            </p>
            <form className="po-cat-admin__form" onSubmit={(e) => void handleEdit(e)}>
              <div className="po-cat-admin__form-grid">
                <label>
                  Nome
                  <input
                    required
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
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
              </div>
              <div className="po-cat-admin__icon-field">
                <span>Visual (Lucide ou imagem)</span>
                <CategoryVisualPicker
                  label={editName || editing.name}
                  categoryId={editing.id}
                  iconKey={editIconKey}
                  hasCustomIcon={Boolean(editing.has_custom_icon)}
                  busy={saving || iconBusy}
                  onSelectLucide={setEditIconKey}
                  onUploadFile={(file) => void handleUploadEditIcon(file)}
                  onClearImage={() => void handleClearEditIcon()}
                />
              </div>
              <label>
                Descrição
                <textarea
                  rows={2}
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
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

        <div className="po-cat-admin__list-head">
          <div>
            <h3 className="po-cat-admin__section-title">Catálogo</h3>
            <p className="po-muted">
              {loading
                ? "Carregando…"
                : `${items.length} categoria(s) · toque no tile para selecionar`}
            </p>
          </div>
        </div>

        {selected ? (
          <div className="po-cat-admin__selection" role="status">
            <div className="po-cat-admin__selection-main">
              <CapexCategoryVisual
                categoryId={selected.id}
                iconKey={selected.icon_key}
                hasCustomIcon={Boolean(selected.has_custom_icon)}
                size={18}
                alt=""
              />
              <div>
                <strong>{selected.name}</strong>
                <p className="po-muted">{selected.code}</p>
              </div>
            </div>
            <div className="po-cat-admin__selection-actions">
              {selected.is_active ? (
                <>
                  <button
                    type="button"
                    className="po-btn po-btn--secondary po-btn--sm"
                    onClick={() => openEdit(selected)}
                  >
                    <Pencil size={14} aria-hidden="true" />
                    Editar
                  </button>
                  <button
                    type="button"
                    className="po-btn po-btn--secondary po-btn--sm"
                    onClick={() => void handleDeactivate(selected)}
                  >
                    <UserMinus size={14} aria-hidden="true" />
                    Desativar
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  className="po-btn po-btn--secondary po-btn--sm"
                  onClick={() => void handleReactivate(selected)}
                >
                  <RotateCcw size={14} aria-hidden="true" />
                  Reativar
                </button>
              )}
            </div>
          </div>
        ) : null}

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
          <ul className="po-cat-admin__grid">
            {items.map((row) => {
              const isSelected = selectedId === row.id;
              return (
                <li key={row.id}>
                  <button
                    type="button"
                    className={
                      isSelected
                        ? "po-cat-admin__tile is-selected"
                        : row.is_active
                          ? "po-cat-admin__tile"
                          : "po-cat-admin__tile is-inactive"
                    }
                    aria-pressed={isSelected}
                    onClick={() => setSelectedId(row.id)}
                    onDoubleClick={() => openEdit(row)}
                    title={row.description || row.name}
                  >
                    <span className="po-cat-admin__tile-icon" aria-hidden="true">
                      <CapexCategoryVisual
                        categoryId={row.id}
                        iconKey={row.icon_key}
                        hasCustomIcon={Boolean(row.has_custom_icon)}
                        size={22}
                        alt=""
                      />
                    </span>
                    <span className="po-cat-admin__tile-name">{row.name}</span>
                    <span className="po-cat-admin__tile-code">{row.code}</span>
                    {!row.is_active ? (
                      <span className="po-cat-admin__tile-badge">Inativa</span>
                    ) : null}
                  </button>
                </li>
              );
            })}
          </ul>
        ) : null}
      </section>
    </PageShell>
  );
}
