import { useCallback, useEffect, useMemo, useState } from "react";
import { Building2, Landmark, Plus, Search } from "lucide-react";

import { HttpRequestError } from "../../api/httpClient";
import {
  createOrgCostCenterFromErp,
  listAdminScopes,
  listErpCostCenters,
} from "../../api/budgetPlanningApi";
import type { ErpCostCenter, OrgCatalog, OrgCostCenter } from "../../types/budgetPlanning";
import { PageShell } from "../../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../../components/uiKit";
import { usePermissions } from "../../hooks/usePermissions";
import { hasScopesManageAccess } from "../../utils/permissions";
import {
  BUDGET_BRANCHES,
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

  if (permLoading) {
    return (
      <PageShell title="Centros de Custo" subtitle="Catálogo interno a partir do ERP.">
        <LoadingActivityCard title="Carregando…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell title="Centros de Custo" subtitle="Acesso restrito.">
        <StateBox variant="error" dismissible={false}>
          Sem permissão para administrar centros de custo (scopes.manage ou admin).
        </StateBox>
      </PageShell>
    );
  }

  if (loadingCatalog) {
    return (
      <PageShell title="Centros de Custo" subtitle="Catálogo interno a partir do ERP.">
        <LoadingActivityCard title="Carregando…" variant="panel" />
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Centros de Custo"
      subtitle="Selecione a filial, consulte o ERP e cadastre centros no planejamento (sem digitação livre)."
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

      <SectionCard title="Filial" hint="A consulta ERP carrega apenas a filial selecionada.">
        <div className="po-filter-grid">
          <label>
            Filial
            <select
              value={branch}
              onChange={(e) => {
                setBranch(e.target.value);
                setSearch("");
                setSuccessMsg(null);
              }}
            >
              <option value="">Selecione a filial…</option>
              {BUDGET_BRANCHES.map((b) => (
                <option key={b.code} value={b.code}>
                  {b.code} — {b.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Busca
            <span className="po-input-with-icon">
              <Search size={16} aria-hidden="true" />
              <input
                type="search"
                placeholder="Código ou descrição…"
                value={search}
                disabled={!normalizeBranchCode(branch)}
                onChange={(e) => setSearch(e.target.value)}
              />
            </span>
          </label>
        </div>
      </SectionCard>

      <SectionCard
        title="Centros disponíveis no ERP"
        hint="Somente leitura. A descrição vem do ERP; não é possível editar o texto."
      >
        {!normalizeBranchCode(branch) ? (
          <p className="po-muted">
            Selecione uma filial para consultar os centros de custo do ERP.
          </p>
        ) : loadingErp ? (
          <LoadingActivityCard title="Carregando centros do ERP…" variant="panel" />
        ) : filteredErp.length === 0 ? (
          <p className="po-muted">
            Nenhum centro de custo encontrado para a filial selecionada
            {search.trim() ? " com o filtro informado" : ""}.
          </p>
        ) : (
          <div className="po-table-wrap">
            <table className="po-table">
              <thead>
                <tr>
                  <th>Identificação</th>
                  <th>Situação</th>
                  <th>Ação</th>
                </tr>
              </thead>
              <tbody>
                {filteredErp.map((item) => {
                  const key = costCenterKey(item);
                  const registeredAlready = isRegistered(item);
                  const busy = addingKey === key;
                  return (
                    <tr key={key}>
                      <td data-label="Identificação">
                        <strong>{formatCostCenterLabel(item)}</strong>
                      </td>
                      <td data-label="Situação">
                        {registeredAlready ? (
                          <span className="po-badge po-badge--success">Já cadastrado</span>
                        ) : (
                          <span className="po-muted">Disponível</span>
                        )}
                      </td>
                      <td data-label="Ação">
                        <button
                          type="button"
                          className="po-btn po-btn--secondary"
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
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      <SectionCard
        title="Centros cadastrados no planejamento"
        hint={
          normalizeBranchCode(branch)
            ? "Lista interna filtrada pela filial selecionada."
            : "Todos os centros internos (todas as filiais)."
        }
      >
        {registeredForBranch.length === 0 ? (
          <p className="po-muted">Nenhum centro cadastrado internamente nesta visão.</p>
        ) : (
          <ul className="po-link-list">
            {registeredForBranch.map((cc: OrgCostCenter) => (
              <li key={costCenterKey(cc)}>
                <div>
                  <Building2 size={16} aria-hidden="true" />{" "}
                  <strong>{formatCostCenterLabel(cc)}</strong>
                  <span className="po-muted">
                    {" "}
                    · origem {cc.source === "erp" ? "ERP" : cc.source || "manual"}
                    {cc.active === false ? " · inativo" : ""}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </PageShell>
  );
}
