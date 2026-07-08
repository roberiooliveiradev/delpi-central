import { useCallback, useEffect, useMemo, useState } from "react";
import { Settings } from "lucide-react";

import {
  type DataTableColumn,
  DataTableSection,
  FieldLabel,
  FilterBar,
  HelpTooltip,
  PendingChangeBadge,
  StateBox,
} from "../../components/data";
import { EditableCell } from "../../components/EditableCell";
import { CONFIG_TOOLTIPS } from "../../content/configTooltips";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { MiniAplicadoresPageHeader } from "../../components/MiniAplicadoresPageHeader";
import {
  useMaintenanceActiveFilial,
  useMaintenanceModuleHomePath,
  useOperationalFilial,
} from "../../hooks/useMaintenanceScope";
import { useServerTable } from "../../hooks/useServerTable";
import { resolveFilialDisplayName } from "../../utils/maintenanceFilialSelection";
import {
  createMotivo,
  createStatusPeca,
  deleteMotivo,
  deleteStatusPeca,
  fetchMotivos,
  fetchStatusPeca,
  updateMotivo,
  updateStatusPeca,
  type MotivoItem,
  type StatusItem,
} from "../../data/api/maintenanceApi";

type ConfiguracaoPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

const STATUS_OPERATORS = [">=", "<=", ">", "<"] as const;

type NovoStatusDraft = {
  descricao: string;
  operador: (typeof STATUS_OPERATORS)[number];
  percentual: number;
};

type MotivoDraft = {
  descricao: string;
  excluir_preventiva: boolean;
};

const DEFAULT_NOVO_STATUS: NovoStatusDraft = {
  descricao: "",
  operador: ">=",
  percentual: 80,
};

function toMotivoDraft(item: MotivoItem): MotivoDraft {
  return {
    descricao: item.descricao,
    excluir_preventiva: Boolean(item.excluir_preventiva),
  };
}

function isMotivoDirty(item: MotivoItem, edits: Record<string, MotivoDraft>): boolean {
  const draft = edits[item.motivo_id];
  if (!draft) return false;
  return (
    draft.descricao.trim() !== item.descricao ||
    draft.excluir_preventiva !== Boolean(item.excluir_preventiva)
  );
}

function isStatusDirty(item: StatusItem, edits: Record<string, StatusItem>): boolean {
  const draft = edits[item.status_id];
  if (!draft) return false;
  return (
    draft.descricao !== item.descricao ||
    draft.operador !== item.operador ||
    draft.percentual !== item.percentual
  );
}

export function ConfiguracaoPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
}: ConfiguracaoPageProps) {
  const filial = useOperationalFilial(getAccessToken, filialScope) ?? "01";
  const moduleHomePath = useMaintenanceModuleHomePath(getAccessToken, filialScope ?? filial);
  const { canManageMiniApplicators, filiais } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const filialDisplayName = resolveFilialDisplayName(filiais, filial);
  const motivosTable = useServerTable({ defaultSortKey: "descricao" });
  const statusTable = useServerTable({ defaultSortKey: "percentual" });
  const [motivos, setMotivos] = useState<MotivoItem[]>([]);
  const [motivosTotal, setMotivosTotal] = useState(0);
  const [status, setStatus] = useState<StatusItem[]>([]);
  const [statusTotal, setStatusTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [motivosLoading, setMotivosLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);
  const [novoMotivo, setNovoMotivo] = useState("");
  const [novoMotivoExcluirPreventiva, setNovoMotivoExcluirPreventiva] = useState(false);
  const [novoStatus, setNovoStatus] = useState<NovoStatusDraft>(DEFAULT_NOVO_STATUS);
  const [motivoEdits, setMotivoEdits] = useState<Record<string, MotivoDraft>>({});
  const [statusEdits, setStatusEdits] = useState<Record<string, StatusItem>>({});

  const loadMotivos = useCallback(async () => {
    setMotivosLoading(true);
    setError(null);
    try {
      const data = await fetchMotivos(
        filial,
        {
          page: motivosTable.query.page,
          pageSize: motivosTable.query.pageSize,
          sortKey: motivosTable.query.sortKey,
          sortDirection: motivosTable.query.sortDirection,
        },
        {},
        getAccessToken,
      );
      const motivoItems = data.items ?? [];
      setMotivos(motivoItems);
      setMotivosTotal(data.total ?? 0);
      setMotivoEdits((current) => {
        const next = { ...current };
        for (const item of motivoItems) {
          if (next[item.motivo_id] === undefined) {
            next[item.motivo_id] = toMotivoDraft(item);
          }
        }
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar motivos.");
    } finally {
      setMotivosLoading(false);
    }
  }, [filial, getAccessToken, motivosTable.query]);

  const loadStatus = useCallback(async () => {
    setStatusLoading(true);
    setError(null);
    try {
      const data = await fetchStatusPeca(
        filial,
        {
          page: statusTable.query.page,
          pageSize: statusTable.query.pageSize,
          sortKey: statusTable.query.sortKey,
          sortDirection: statusTable.query.sortDirection,
        },
        {},
        getAccessToken,
      );
      const statusItems = data.items ?? [];
      setStatus(statusItems);
      setStatusTotal(data.total ?? 0);
      setStatusEdits((current) => {
        const next = { ...current };
        for (const item of statusItems) {
          if (!next[item.status_id]) {
            next[item.status_id] = { ...item };
          }
        }
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar status.");
    } finally {
      setStatusLoading(false);
    }
  }, [filial, getAccessToken, statusTable.query]);

  const loadData = useCallback(async () => {
    await Promise.all([loadMotivos(), loadStatus()]);
  }, [loadMotivos, loadStatus]);

  useEffect(() => {
    void loadMotivos();
  }, [loadMotivos]);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    motivosTable.resetPage();
    statusTable.resetPage();
  }, [filial, motivosTable.resetPage, statusTable.resetPage]);

  async function handleCreateMotivo(event: React.FormEvent) {
    event.preventDefault();
    const descricao = novoMotivo.trim();
    if (!descricao) return;
    setError(null);
    setSuccess(null);
    try {
      await createMotivo(filial, descricao, getAccessToken, novoMotivoExcluirPreventiva);
      setNovoMotivo("");
      setNovoMotivoExcluirPreventiva(false);
      setSuccess("Motivo adicionado.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao adicionar motivo.");
    }
  }

  async function handleSaveMotivo(motivoId: string) {
    const draft = motivoEdits[motivoId];
    const descricao = (draft?.descricao ?? "").trim();
    if (!descricao) return;
    setError(null);
    setSuccess(null);
    try {
      await updateMotivo(
        motivoId,
        filial,
        {
          descricao,
          excluir_preventiva: draft?.excluir_preventiva ?? false,
        },
        getAccessToken,
      );
      setSuccess("Motivo atualizado.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar motivo.");
    }
  }

  async function handleDeleteMotivo(motivoId: string, descricao: string) {
    if (!window.confirm(`Excluir motivo "${descricao}"?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteMotivo(motivoId, filial, getAccessToken);
      setSuccess("Motivo excluído.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir motivo.");
    }
  }

  async function handleCreateStatus(event: React.FormEvent) {
    event.preventDefault();
    const descricao = novoStatus.descricao.trim();
    if (!descricao) return;
    setError(null);
    setSuccess(null);
    try {
      await createStatusPeca(
        {
          filial,
          descricao,
          operador: novoStatus.operador,
          percentual: novoStatus.percentual,
        },
        getAccessToken,
      );
      setNovoStatus(DEFAULT_NOVO_STATUS);
      setSuccess("Status preventivo adicionado.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao adicionar status.");
    }
  }

  async function handleSaveStatus(statusId: string) {
    const draft = statusEdits[statusId];
    if (!draft) return;
    setError(null);
    setSuccess(null);
    try {
      await updateStatusPeca(
        statusId,
        filial,
        {
          descricao: draft.descricao,
          operador: draft.operador,
          percentual: draft.percentual,
        },
        getAccessToken,
      );
      setSuccess("Status atualizado.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar status.");
    }
  }

  async function handleDeleteStatus(statusId: string, descricao: string) {
    if (!window.confirm(`Excluir regra de status "${descricao}"?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteStatusPeca(statusId, filial, getAccessToken);
      setSuccess("Status excluído.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir status.");
    }
  }

  const motivosColumns = useMemo<DataTableColumn<MotivoItem>[]>(() => {
    const columns: DataTableColumn<MotivoItem>[] = [
      {
        key: "descricao",
        header: "Descrição",
        headerHint: CONFIG_TOOLTIPS.motivoDescricao,
        sortable: true,
        sortValue: (item) => motivoEdits[item.motivo_id]?.descricao ?? item.descricao,
        render: (item) =>
          canManageMiniApplicators ? (
            <EditableCell
              value={motivoEdits[item.motivo_id]?.descricao ?? item.descricao}
              aria-label={`Descrição do motivo ${item.motivo_id}`}
              onChange={(descricao) =>
                setMotivoEdits((prev) => ({
                  ...prev,
                  [item.motivo_id]: {
                    ...(prev[item.motivo_id] ?? toMotivoDraft(item)),
                    descricao,
                  },
                }))
              }
              badge={<PendingChangeBadge visible={isMotivoDirty(item, motivoEdits)} />}
            />
          ) : (
            item.descricao
          ),
      },
      {
        key: "excluir_preventiva",
        header: "Ignora preventiva",
        headerHint: CONFIG_TOOLTIPS.excluirPreventiva,
        align: "center",
        render: (item) => {
          const draft = motivoEdits[item.motivo_id] ?? toMotivoDraft(item);
          if (!canManageMiniApplicators) {
            return draft.excluir_preventiva ? "Sim" : "Não";
          }
          return (
            <label className="dm-checkbox-field">
              <input
                type="checkbox"
                checked={draft.excluir_preventiva}
                onChange={(event) =>
                  setMotivoEdits((prev) => ({
                    ...prev,
                    [item.motivo_id]: {
                      ...(prev[item.motivo_id] ?? toMotivoDraft(item)),
                      excluir_preventiva: event.target.checked,
                    },
                  }))
                }
              />
              <HelpTooltip content={CONFIG_TOOLTIPS.excluirPreventiva} wrap ariaLabel="Ajuda: ignora preventiva">
                <span>Não conta</span>
              </HelpTooltip>
            </label>
          );
        },
      },
    ];

    if (canManageMiniApplicators) {
      columns.push({
        key: "acoes",
        header: "Ações",
        interactive: true,
        render: (item) => (
          <div className="dm-row-actions">
            <button type="button" className="dm-ghost-btn" onClick={() => void handleSaveMotivo(item.motivo_id)}>
              Salvar
            </button>
            <button
              type="button"
              className="dm-ghost-btn dm-ghost-btn--danger"
              onClick={() => void handleDeleteMotivo(item.motivo_id, item.descricao)}
            >
              Excluir
            </button>
          </div>
        ),
      });
    }

    return columns;
  }, [canManageMiniApplicators, motivoEdits]);

  const statusColumns = useMemo<DataTableColumn<StatusItem>[]>(() => {
    const columns: DataTableColumn<StatusItem>[] = [
      {
        key: "status",
        header: "Status",
        headerHint: CONFIG_TOOLTIPS.statusDescricao,
        sortable: true,
        sortValue: (item) => (statusEdits[item.status_id] ?? item).descricao,
        render: (item) => {
          const draft = statusEdits[item.status_id] ?? item;
          return canManageMiniApplicators ? (
            <EditableCell
              value={draft.descricao}
              aria-label={`Descrição do status ${item.status_id}`}
              onChange={(descricao) =>
                setStatusEdits((prev) => ({
                  ...prev,
                  [item.status_id]: { ...draft, descricao },
                }))
              }
              badge={<PendingChangeBadge visible={isStatusDirty(item, statusEdits)} />}
            />
          ) : (
            item.descricao
          );
        },
      },
      {
        key: "operador",
        header: "Operador",
        headerHint: CONFIG_TOOLTIPS.statusOperador,
        sortable: true,
        sortValue: (item) => (statusEdits[item.status_id] ?? item).operador,
        render: (item) => {
          const draft = statusEdits[item.status_id] ?? item;
          return canManageMiniApplicators ? (
            <EditableCell
              as="select"
              value={draft.operador}
              aria-label={`Operador do status ${item.status_id}`}
              onChange={(operador) =>
                setStatusEdits((prev) => ({
                  ...prev,
                  [item.status_id]: { ...draft, operador },
                }))
              }
              options={STATUS_OPERATORS.map((operador) => ({
                value: operador,
                label: operador,
              }))}
            />
          ) : (
            item.operador
          );
        },
      },
      {
        key: "percentual",
        header: "Percentual",
        headerHint: CONFIG_TOOLTIPS.statusPercentual,
        sortable: true,
        sortValue: (item) => (statusEdits[item.status_id] ?? item).percentual,
        render: (item) => {
          const draft = statusEdits[item.status_id] ?? item;
          return canManageMiniApplicators ? (
            <EditableCell
              type="number"
              min={0}
              value={draft.percentual}
              aria-label={`Percentual do status ${item.status_id}`}
              onChange={(raw) =>
                setStatusEdits((prev) => ({
                  ...prev,
                  [item.status_id]: {
                    ...draft,
                    percentual: Number(raw),
                  },
                }))
              }
            />
          ) : (
            `${item.percentual}%`
          );
        },
        align: "right",
      },
    ];

    if (canManageMiniApplicators) {
      columns.push({
        key: "acoes",
        header: "Ações",
        interactive: true,
        render: (item) => (
          <div className="dm-row-actions">
            <button type="button" className="dm-ghost-btn" onClick={() => void handleSaveStatus(item.status_id)}>
              Salvar
            </button>
            <button
              type="button"
              className="dm-ghost-btn dm-ghost-btn--danger"
              onClick={() => void handleDeleteStatus(item.status_id, item.descricao)}
            >
              Excluir
            </button>
          </div>
        ),
      });
    }

    return columns;
  }, [canManageMiniApplicators, statusEdits]);

  return (
    <MaintenanceShell>
      <MiniAplicadoresPageHeader
        title="Configuração"
        subtitle={`Motivos de troca e regras de status preventivo por golpes da filial ${filialDisplayName}.`}
        icon={Settings}
        filial={filial}
        filialDisplayName={filialDisplayName}
        moduleHomePath={moduleHomePath}
        showConfiguration={canManageMiniApplicators}
        currentPath={pathname}
        onNavigate={onNavigate}
      />

      {error ? (
        <StateBox variant="error" onDismiss={() => setError(null)}>
          {error}
        </StateBox>
      ) : null}
      {success ? (
        <StateBox variant="success" onDismiss={() => setSuccess(null)}>
          {success}
        </StateBox>
      ) : null}

      <DataTableSection
        className="dm-table-section--editable-config"
        title="Motivos de reposição"
        titleHint={CONFIG_TOOLTIPS.motivosSection}
        toolbar={
          canManageMiniApplicators ? (
            <FilterBar embedded className="dm-filter-bar--motivo-create" onSubmit={handleCreateMotivo}>
              <label className="dm-field">
                <FieldLabel label="Novo motivo" hint={CONFIG_TOOLTIPS.motivoDescricao}  className="dm-field__label" />
                <input
                  value={novoMotivo}
                  onChange={(event) => setNovoMotivo(event.target.value)}
                  placeholder="Ex.: DESGASTE"
                />
              </label>
              <label className="dm-checkbox-field">
                <input
                  type="checkbox"
                  checked={novoMotivoExcluirPreventiva}
                  onChange={(event) => setNovoMotivoExcluirPreventiva(event.target.checked)}
                />
                <HelpTooltip content={CONFIG_TOOLTIPS.excluirPreventiva} wrap ariaLabel="Ajuda: não conta no preventivo">
                  <span>Não conta no preventivo</span>
                </HelpTooltip>
              </label>
              <button type="submit" className="dm-primary-btn">
                Adicionar
              </button>
            </FilterBar>
          ) : null
        }
        columns={motivosColumns}
        rows={motivos}
        loading={motivosLoading}
        emptyMessage="Nenhum motivo cadastrado."
        getRowKey={(item) => String(item.motivo_id)}
        serverTable={{
          page: motivosTable.query.page,
          pageSize: motivosTable.query.pageSize,
          total: motivosTotal,
          onPageChange: motivosTable.setPage,
          sortKey: motivosTable.query.sortKey,
          sortDirection: motivosTable.query.sortDirection,
          onSortChange: motivosTable.handleSortChange,
        }}
      />

      <DataTableSection
        className="dm-table-section--editable-config dm-table-section--editable-status"
        title="Status preventivo"
        titleHint={CONFIG_TOOLTIPS.statusSection}
        toolbar={
          canManageMiniApplicators ? (
            <FilterBar embedded className="dm-filter-bar--status-create" onSubmit={handleCreateStatus}>
              <label className="dm-field">
                <FieldLabel label="Novo status" hint={CONFIG_TOOLTIPS.statusDescricao}  className="dm-field__label" />
                <input
                  value={novoStatus.descricao}
                  onChange={(event) =>
                    setNovoStatus((prev) => ({ ...prev, descricao: event.target.value }))
                  }
                  placeholder="Ex.: CRÍTICO"
                />
              </label>
              <label className="dm-field">
                <FieldLabel label="Operador" hint={CONFIG_TOOLTIPS.statusOperador}  className="dm-field__label" />
                <select
                  value={novoStatus.operador}
                  onChange={(event) =>
                    setNovoStatus((prev) => ({
                      ...prev,
                      operador: event.target.value as NovoStatusDraft["operador"],
                    }))
                  }
                >
                  {STATUS_OPERATORS.map((operador) => (
                    <option key={operador} value={operador}>
                      {operador}
                    </option>
                  ))}
                </select>
              </label>
              <label className="dm-field">
                <FieldLabel label="Percentual" hint={CONFIG_TOOLTIPS.statusPercentual}  className="dm-field__label" />
                <input
                  type="number"
                  min={0}
                  max={200}
                  value={novoStatus.percentual}
                  onChange={(event) =>
                    setNovoStatus((prev) => ({
                      ...prev,
                      percentual: Number(event.target.value),
                    }))
                  }
                />
              </label>
              <button type="submit" className="dm-primary-btn">
                Adicionar
              </button>
            </FilterBar>
          ) : null
        }
        columns={statusColumns}
        rows={status}
        loading={statusLoading}
        emptyMessage="Nenhuma regra de status cadastrada."
        getRowKey={(item) => String(item.status_id)}
        serverTable={{
          page: statusTable.query.page,
          pageSize: statusTable.query.pageSize,
          total: statusTotal,
          onPageChange: statusTable.setPage,
          sortKey: statusTable.query.sortKey,
          sortDirection: statusTable.query.sortDirection,
          onSortChange: statusTable.handleSortChange,
        }}
      />
    </MaintenanceShell>
  );
}
