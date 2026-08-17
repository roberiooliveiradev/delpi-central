import { useCallback, useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Landmark,
  Plus,
  Search,
  Warehouse,
} from "lucide-react";

import { HttpRequestError } from "../../api/httpClient";
import {
  createOrgCostCenterFromErp,
  listAdminScopes,
  listErpCostCenters,
  updateOrgCostCenterIcon,
} from "../../api/budgetPlanningApi";
import type { ErpCostCenter, OrgCatalog, OrgCostCenter } from "../../types/budgetPlanning";
import { CostCenterIconPicker } from "../../components/CostCenterIconPicker";
import { PageShell } from "../../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../../components/uiKit";
import { usePermissions } from "../../hooks/usePermissions";
import { hasScopesManageAccess } from "../../utils/permissions";
import {
  BUDGET_BRANCHES,
  branchLabel,
  costCenterKey,
  formatCostCenterLabel,
  isSameCostCenter,
  matchesCostCenterSearch,
  normalizeBranchCode,
} from "../../utils/orgCostCenters";

export function AdminCentrosCustoPage() {
  const { profile, loading: permLoading } = usePermissions();
  const canAccess = hasScopesManageAccess(profile);

  const [branch, setBranch] = useState("");
  const [search, setSearch] = useState("");
  const [catalog, setCatalog] = useState<OrgCatalog | null>(null);
  const [erpItems, setErpItems] = useState<ErpCostCenter[]>([]);
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [loadingErp, setLoadingErp] = useState(false);
  const [addingKey, setAddingKey] = useState<string | null>(null);
  const [iconBusyKey, setIconBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadCatalog = useCallback(async (signal?: AbortSignal) => {
    setLoadingCatalog(true);
    try {
      const data = await listAdminScopes(signal);
      if (!signal?.aborted) {
        setCatalog(data.catalog);
        setError(null);
      }
    } catch (err: unknown) {
      if (signal?.aborted) return;
      if (err instanceof HttpRequestError && err.status === 401) {
        setError("Sessão expirada (401). Faça login novamente.");
      } else if (err instanceof HttpRequestError && err.status === 403) {
        setError("Acesso negado (403) para administrar centros de custo.");
      } else {
        setError(err instanceof Error ? err.message : "Erro ao carregar o catálogo interno.");
      }
    } finally {
      if (!signal?.aborted) setLoadingCatalog(false);
    }
  }, []);

  useEffect(() => {
    if (permLoading || !canAccess) return;
    const controller = new AbortController();
    void loadCatalog(controller.signal);
    return () => controller.abort();
  }, [canAccess, loadCatalog, permLoading]);

  useEffect(() => {
    if (permLoading || !canAccess) return;
    const branchNorm = normalizeBranchCode(branch);
    if (!branchNorm) {
      setErpItems([]);
      setLoadingErp(false);
      return;
    }
    const controller = new AbortController();
    setLoadingErp(true);
    setError(null);
    listErpCostCenters(branchNorm, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setErpItems(data.items ?? []);
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setErpItems([]);
        if (err instanceof HttpRequestError && err.status === 401) {
          setError("Sessão expirada (401). Faça login novamente.");
        } else if (err instanceof HttpRequestError && err.status === 403) {
          setError("Acesso negado (403) para consultar centros de custo do ERP.");
        } else {
          setError(err instanceof Error ? err.message : "Erro ao consultar o ERP.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingErp(false);
      });
    return () => controller.abort();
  }, [branch, canAccess, permLoading]);

  const registered = useMemo(() => catalog?.cost_centers ?? [], [catalog]);

  const registeredForBranch = useMemo(() => {
    const branchNorm = normalizeBranchCode(branch);
    if (!branchNorm) return registered;
    return registered.filter(
      (cc) =>
        normalizeBranchCode(cc.branch) === branchNorm ||
        normalizeBranchCode(cc.unit_code) === branchNorm,
    );
  }, [branch, registered]);

  const filteredErp = useMemo(
    () => erpItems.filter((item) => matchesCostCenterSearch(item, search)),
    [erpItems, search],
  );

  const availableCount = useMemo(() => {
    return filteredErp.filter(
      (item) =>
        !registered.some((cc) =>
          isSameCostCenter(cc, { branch: item.branch, code: item.code }),
        ),
    ).length;
  }, [filteredErp, registered]);

  const selectedBranchMeta = BUDGET_BRANCHES.find((b) => b.code === branch);

  function isRegistered(item: ErpCostCenter): boolean {
    return registered.some((cc) =>
      isSameCostCenter(cc, { branch: item.branch, code: item.code }),
    );
  }

  async function handleAdd(item: ErpCostCenter) {
    const key = costCenterKey(item);
    if (addingKey || isRegistered(item)) return;
    setAddingKey(key);
    setError(null);
    setSuccessMsg(null);
    try {
      const created = await createOrgCostCenterFromErp({
        branch: item.branch,
        code: item.code,
        unit_id: item.branch,
      });
      setSuccessMsg(`Centro cadastrado: ${formatCostCenterLabel(created)}`);
      await loadCatalog();
    } catch (err: unknown) {
      if (err instanceof HttpRequestError && err.status === 401) {
        setError("Sessão expirada (401). Faça login novamente.");
      } else if (err instanceof HttpRequestError && err.status === 403) {
        setError("Acesso negado (403) para cadastrar centros de custo.");
      } else {
        setError(err instanceof Error ? err.message : "Falha ao cadastrar o centro de custo.");
      }
    } finally {
      setAddingKey(null);
    }
  }

  async function handleIconChange(cc: OrgCostCenter, iconKey: string | null) {
    const branchCode = normalizeBranchCode(cc.branch || cc.unit_code || "");
    if (!branchCode || !cc.code) return;
    const key = costCenterKey(cc);
    setIconBusyKey(key);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await updateOrgCostCenterIcon({
        branch: branchCode,
        code: cc.code,
        icon_key: iconKey,
      });
      setCatalog((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          cost_centers: prev.cost_centers.map((row) =>
            isSameCostCenter(row, updated)
              ? { ...row, icon_key: updated.icon_key ?? null }
              : row,
          ),
        };
      });
      setSuccessMsg(
        iconKey
          ? `Ícone atualizado: ${formatCostCenterLabel(updated)}`
          : `Ícone padrão restaurado: ${formatCostCenterLabel(updated)}`,
      );
    } catch (err: unknown) {
      if (err instanceof HttpRequestError && err.status === 401) {
        setError("Sessão expirada (401). Faça login novamente.");
      } else if (err instanceof HttpRequestError && err.status === 403) {
        setError("Acesso negado (403) para personalizar ícones.");
      } else {
        setError(err instanceof Error ? err.message : "Falha ao atualizar o ícone.");
      }
    } finally {
      setIconBusyKey(null);
    }
  }

  function selectBranch(code: string) {
    setBranch(code);
    setSearch("");
    setSuccessMsg(null);
  }

  if (permLoading || (canAccess && loadingCatalog)) {
    return (
      <PageShell
        title="Centros de Custo"
        subtitle="Catálogo interno a partir do ERP."
        icon={<Landmark size={28} strokeWidth={1.75} aria-hidden="true" />}
        backRoute="admin"
      >
        <LoadingActivityCard title="Carregando catálogo…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell
        title="Centros de Custo"
        subtitle="Acesso restrito."
        icon={<Landmark size={28} strokeWidth={1.75} aria-hidden="true" />}
        backRoute="admin"
      >
        <StateBox variant="error" dismissible={false}>
          Sem permissão para administrar centros de custo (scopes.manage ou admin).
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Centros de Custo"
      subtitle="Importe do ERP por filial — sem digitação livre de código ou descrição."
      icon={<Landmark size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="admin"
    >
      {successMsg ? (
        <StateBox variant="success" dismissible={false}>
          {successMsg}
        </StateBox>
      ) : null}
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      <section className="po-cc-admin" aria-label="Centros de custo">
        <div className="po-cc-admin__hero">
          <div className="po-cc-admin__hero-copy">
            <p className="po-cc-admin__eyebrow">Administração · Catálogo</p>
            <h2 className="po-cc-admin__title">
              {selectedBranchMeta
                ? `Filial ${selectedBranchMeta.code}`
                : "Escolha a filial"}
            </h2>
            <p className="po-cc-admin__lead">
              {selectedBranchMeta
                ? `${selectedBranchMeta.label}. Consulte o ERP e adicione centros ao planejamento.`
                : "Selecione Jaraguá do Sul (01) ou Rio Bananal (02) para listar os centros do ERP."}
            </p>
          </div>

          <aside className="po-cc-admin__hero-panel" aria-label="Resumo">
            <dl className="po-cc-admin__meta">
              <div>
                <dt>No planejamento</dt>
                <dd>{registeredForBranch.length}</dd>
              </div>
              <div>
                <dt>No ERP</dt>
                <dd>{normalizeBranchCode(branch) ? erpItems.length : "—"}</dd>
              </div>
              <div>
                <dt>Disponíveis</dt>
                <dd>{normalizeBranchCode(branch) ? availableCount : "—"}</dd>
              </div>
            </dl>
          </aside>
        </div>

        <div className="po-cc-admin__branch-block">
          <div className="po-cc-admin__branch-head">
            <h3 className="po-cc-admin__section-title">Filial</h3>
            <p className="po-muted">A consulta ERP carrega apenas a filial selecionada.</p>
          </div>

          <label className="po-sr-only" htmlFor="po-cc-branch-select">
            Filial
          </label>
          <select
            id="po-cc-branch-select"
            className="po-sr-only"
            value={branch}
            onChange={(e) => selectBranch(e.target.value)}
          >
            <option value="">Selecione a filial…</option>
            {BUDGET_BRANCHES.map((b) => (
              <option key={b.code} value={b.code}>
                {b.code} — {b.label}
              </option>
            ))}
          </select>

          <div className="po-cc-admin__branch-grid" role="group" aria-label="Filiais">
            {BUDGET_BRANCHES.map((b) => {
              const selected = branch === b.code;
              return (
                <button
                  key={b.code}
                  type="button"
                  className={
                    selected
                      ? "po-cc-admin__branch-card is-selected"
                      : "po-cc-admin__branch-card"
                  }
                  aria-pressed={selected}
                  onClick={() => selectBranch(b.code)}
                >
                  <span className="po-cc-admin__branch-code">{b.code}</span>
                  <strong>{b.label}</strong>
                  <span className="po-muted">
                    {selected ? "Consultando ERP" : "Toque para consultar"}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <SectionCard
          title="Centros disponíveis no ERP"
          hint="Somente leitura. A descrição vem do ERP; não é possível editar o texto."
        >
          {!normalizeBranchCode(branch) ? (
            <p className="po-muted">
              Selecione uma filial para consultar os centros de custo do ERP.
            </p>
          ) : (
            <>
              <label className="po-field po-cc-admin__search">
                <span>Busca</span>
                <span className="po-input-with-icon">
                  <Search size={16} aria-hidden="true" />
                  <input
                    type="search"
                    placeholder="Código ou descrição…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </span>
              </label>

              {loadingErp ? (
                <LoadingActivityCard title="Carregando centros do ERP…" variant="panel" />
              ) : filteredErp.length === 0 ? (
                <p className="po-muted">
                  Nenhum centro de custo encontrado para a filial selecionada
                  {search.trim() ? " com o filtro informado" : ""}.
                </p>
              ) : (
                <ul className="po-cc-admin__erp-grid">
                  {filteredErp.map((item) => {
                    const key = costCenterKey(item);
                    const registeredAlready = isRegistered(item);
                    const busy = addingKey === key;
                    return (
                      <li
                        key={key}
                        className={
                          registeredAlready
                            ? "po-cc-admin__erp-card is-registered"
                            : "po-cc-admin__erp-card"
                        }
                      >
                        <div className="po-cc-admin__erp-card-top">
                          <Warehouse size={18} aria-hidden="true" />
                          {registeredAlready ? (
                            <span className="po-badge po-badge--success">Já cadastrado</span>
                          ) : (
                            <span className="po-muted">Disponível</span>
                          )}
                        </div>
                        <strong className="po-cc-admin__erp-name">
                          {formatCostCenterLabel(item)}
                        </strong>
                        <p className="po-muted po-cc-admin__erp-desc">
                          {item.description?.trim() || "Sem descrição no ERP"}
                        </p>
                        <button
                          type="button"
                          className={
                            registeredAlready
                              ? "po-btn po-btn--secondary po-btn--sm"
                              : "po-btn po-btn--primary po-btn--sm"
                          }
                          disabled={registeredAlready || Boolean(addingKey)}
                          onClick={() => void handleAdd(item)}
                        >
                          <Plus size={14} aria-hidden="true" />
                          {busy
                            ? "Cadastrando…"
                            : registeredAlready
                              ? "Já no planejamento"
                              : "Adicionar ao planejamento"}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </>
          )}
        </SectionCard>

        <div className="po-cc-admin__registered-head">
          <h3 className="po-cc-admin__section-title">
            Centros cadastrados no planejamento
          </h3>
          <p className="po-muted">
            {normalizeBranchCode(branch)
              ? `Lista interna filtrada por ${branchLabel(branch)}.`
              : "Todos os centros internos (todas as filiais)."}{" "}
            Clique no ícone do card para personalizar.
          </p>
        </div>

        {registeredForBranch.length === 0 ? (
          <StateBox variant="default" dismissible={false}>
            Nenhum centro cadastrado internamente nesta visão.
          </StateBox>
        ) : (
          <ul className="po-cc-admin__registered-grid">
            {registeredForBranch.map((cc: OrgCostCenter) => (
              <li key={costCenterKey(cc)} className="po-cc-admin__registered-card">
                <CostCenterIconPicker
                  iconKey={cc.icon_key}
                  label={formatCostCenterLabel(cc)}
                  busy={iconBusyKey === costCenterKey(cc)}
                  onSelect={(next) => void handleIconChange(cc, next)}
                />
                <div>
                  <strong>{formatCostCenterLabel(cc)}</strong>
                  <p className="po-muted">
                    origem {cc.source === "erp" ? "ERP" : cc.source || "manual"}
                    {cc.active === false ? " · inativo" : ""}
                  </p>
                </div>
                {cc.active !== false ? (
                  <span className="po-inline-success" title="Ativo">
                    <CheckCircle2 size={16} aria-hidden="true" />
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </PageShell>
  );
}
