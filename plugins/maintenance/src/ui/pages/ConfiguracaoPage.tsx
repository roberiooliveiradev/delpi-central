import { useCallback, useEffect, useMemo, useState } from "react";
import { Settings } from "lucide-react";

import {
  type DataTableColumn,
  DataTableSection,
  FilialBadge,
  FilterBar,
  StateBox,
} from "../../components/data";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { MiniAplicadoresPageHeader } from "../../components/MiniAplicadoresPageHeader";
import {
  useMaintenanceActiveFilial,
  useMaintenanceModuleHomePath,
  useOperationalFilial,
} from "../../hooks/useMaintenanceScope";
import {
  createMotivo,
  deleteMotivo,
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

export function ConfiguracaoPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
}: ConfiguracaoPageProps) {
  const filial = useOperationalFilial(getAccessToken, filialScope) ?? "01";
  const moduleHomePath = useMaintenanceModuleHomePath(getAccessToken, filialScope ?? filial);
  const { canManageMiniApplicators } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const [motivos, setMotivos] = useState<MotivoItem[]>([]);
  const [status, setStatus] = useState<StatusItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [novoMotivo, setNovoMotivo] = useState("");
  const [motivoEdits, setMotivoEdits] = useState<Record<number, string>>({});
  const [statusEdits, setStatusEdits] = useState<Record<number, StatusItem>>({});

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [motivosData, statusData] = await Promise.all([
        fetchMotivos(filial, getAccessToken),
        fetchStatusPeca(filial, getAccessToken),
      ]);
      const motivoItems = motivosData.items ?? [];
      const statusItems = statusData.items ?? [];
      setMotivos(motivoItems);
      setStatus(statusItems);
      setMotivoEdits(Object.fromEntries(motivoItems.map((item) => [item.motivo_id, item.descricao])));
      setStatusEdits(Object.fromEntries(statusItems.map((item) => [item.status_id, { ...item }])));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar configuração.");
    } finally {
      setLoading(false);
    }
  }, [filial, getAccessToken]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  async function handleCreateMotivo(event: React.FormEvent) {
    event.preventDefault();
    const descricao = novoMotivo.trim();
    if (!descricao) return;
    setError(null);
    setSuccess(null);
    try {
      await createMotivo(descricao, getAccessToken);
      setNovoMotivo("");
      setSuccess("Motivo adicionado.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao adicionar motivo.");
    }
  }

  async function handleSaveMotivo(motivoId: number) {
    const descricao = (motivoEdits[motivoId] ?? "").trim();
    if (!descricao) return;
    setError(null);
    setSuccess(null);
    try {
      await updateMotivo(motivoId, descricao, getAccessToken);
      setSuccess("Motivo atualizado.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar motivo.");
    }
  }

  async function handleDeleteMotivo(motivoId: number, descricao: string) {
    if (!window.confirm(`Excluir motivo "${descricao}"?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteMotivo(motivoId, getAccessToken);
      setSuccess("Motivo excluído.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir motivo.");
    }
  }

  async function handleSaveStatus(statusId: number) {
    const draft = statusEdits[statusId];
    if (!draft) return;
    setError(null);
    setSuccess(null);
    try {
      await updateStatusPeca(
        statusId,
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

  const motivosColumns = useMemo<DataTableColumn<MotivoItem>[]>(() => {
    const columns: DataTableColumn<MotivoItem>[] = [
      { key: "id", header: "ID", render: (item) => item.motivo_id, align: "center" },
      {
        key: "descricao",
        header: "Descrição",
        render: (item) =>
          canManageMiniApplicators ? (
            <input
              value={motivoEdits[item.motivo_id] ?? item.descricao}
              onChange={(event) =>
                setMotivoEdits((prev) => ({
                  ...prev,
                  [item.motivo_id]: event.target.value,
                }))
              }
            />
          ) : (
            item.descricao
          ),
      },
    ];

    if (canManageMiniApplicators) {
      columns.push({
        key: "acoes",
        header: "Ações",
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
        render: (item) => {
          const draft = statusEdits[item.status_id] ?? item;
          return canManageMiniApplicators ? (
            <input
              value={draft.descricao}
              onChange={(event) =>
                setStatusEdits((prev) => ({
                  ...prev,
                  [item.status_id]: { ...draft, descricao: event.target.value },
                }))
              }
            />
          ) : (
            item.descricao
          );
        },
      },
      {
        key: "operador",
        header: "Operador",
        render: (item) => {
          const draft = statusEdits[item.status_id] ?? item;
          return canManageMiniApplicators ? (
            <select
              value={draft.operador}
              onChange={(event) =>
                setStatusEdits((prev) => ({
                  ...prev,
                  [item.status_id]: { ...draft, operador: event.target.value },
                }))
              }
            >
              {STATUS_OPERATORS.map((operador) => (
                <option key={operador} value={operador}>
                  {operador}
                </option>
              ))}
            </select>
          ) : (
            item.operador
          );
        },
      },
      {
        key: "percentual",
        header: "Percentual",
        render: (item) => {
          const draft = statusEdits[item.status_id] ?? item;
          return canManageMiniApplicators ? (
            <input
              type="number"
              min={0}
              max={200}
              value={draft.percentual}
              onChange={(event) =>
                setStatusEdits((prev) => ({
                  ...prev,
                  [item.status_id]: {
                    ...draft,
                    percentual: Number(event.target.value),
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
        render: (item) => (
          <button type="button" className="dm-ghost-btn" onClick={() => void handleSaveStatus(item.status_id)}>
            Salvar
          </button>
        ),
      });
    }

    return columns;
  }, [canManageMiniApplicators, statusEdits]);

  return (
    <MaintenanceShell>
      <MiniAplicadoresPageHeader
        title="Configuração"
        subtitle="Motivos de troca e regras de status preventivo."
        icon={Settings}
        moduleHomePath={moduleHomePath}
        showConfiguration={canManageMiniApplicators}
        currentPath={pathname}
        onNavigate={onNavigate}
      />

      <FilterBar leading={<FilialBadge filial={filial} />} />

      {error ? <StateBox variant="error">{error}</StateBox> : null}
      {success ? <StateBox variant="success">{success}</StateBox> : null}
      {loading ? <StateBox>Carregando…</StateBox> : null}

      <DataTableSection
        title="Motivos de reposição"
        toolbar={
          canManageMiniApplicators ? (
            <FilterBar embedded onSubmit={handleCreateMotivo}>
              <label className="dm-field">
                <span>Novo motivo</span>
                <input
                  value={novoMotivo}
                  onChange={(event) => setNovoMotivo(event.target.value)}
                  placeholder="Ex.: DESGASTE"
                />
              </label>
              <button type="submit" className="dm-primary-btn">
                Adicionar
              </button>
            </FilterBar>
          ) : null
        }
        columns={motivosColumns}
        rows={motivos}
        loading={loading}
        emptyMessage="Nenhum motivo cadastrado."
        getRowKey={(item) => String(item.motivo_id)}
      />

      <DataTableSection
        title="Status preventivo"
        columns={statusColumns}
        rows={status}
        loading={loading}
        emptyMessage="Nenhuma regra de status cadastrada."
        getRowKey={(item) => String(item.status_id)}
      />
    </MaintenanceShell>
  );
}
