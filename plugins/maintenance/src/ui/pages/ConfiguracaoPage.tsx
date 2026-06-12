import { useCallback, useEffect, useState } from "react";
import { Settings } from "lucide-react";

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
      setSuccess("Motivo criado.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar motivo.");
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
    if (!window.confirm(`Excluir motivo «${descricao}»?`)) return;
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

      <section className="dm-card dm-filter-bar">
        <p className="dm-filial-badge">Filial operacional: {filial}</p>
      </section>

      {error ? <p className="dm-state-box dm-state-box--error">{error}</p> : null}
      {success ? <p className="dm-state-box">{success}</p> : null}
      {loading ? <p className="dm-state-box">Carregando…</p> : null}

      <section className="dm-card">
        <h3 className="dm-card__title">Motivos de reposição</h3>
        {canManageMiniApplicators ? (
          <form className="dm-filter-bar" onSubmit={handleCreateMotivo}>
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
          </form>
        ) : null}
        <div className="dm-table-wrap">
          <table className="dm-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Descrição</th>
                {canManageMiniApplicators ? <th>Ações</th> : null}
              </tr>
            </thead>
            <tbody>
              {motivos.map((item) => (
                <tr key={item.motivo_id}>
                  <td data-label="ID">{item.motivo_id}</td>
                  <td data-label="Descrição">
                    {canManageMiniApplicators ? (
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
                    )}
                  </td>
                  {canManageMiniApplicators ? (
                    <td data-label="Ações">
                      <div className="dm-row-actions">
                        <button
                          type="button"
                          className="dm-ghost-btn"
                          onClick={() => void handleSaveMotivo(item.motivo_id)}
                        >
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
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="dm-card">
        <h3 className="dm-card__title">Status preventivo</h3>
        <div className="dm-table-wrap">
          <table className="dm-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Operador</th>
                <th>Percentual</th>
                {canManageMiniApplicators ? <th>Ações</th> : null}
              </tr>
            </thead>
            <tbody>
              {status.map((item) => {
                const draft = statusEdits[item.status_id] ?? item;
                return (
                  <tr key={item.status_id}>
                    <td data-label="Status">
                      {canManageMiniApplicators ? (
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
                      )}
                    </td>
                    <td data-label="Operador">
                      {canManageMiniApplicators ? (
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
                      )}
                    </td>
                    <td data-label="Percentual">
                      {canManageMiniApplicators ? (
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
                      )}
                    </td>
                    {canManageMiniApplicators ? (
                      <td data-label="Ações">
                        <button
                          type="button"
                          className="dm-ghost-btn"
                          onClick={() => void handleSaveStatus(item.status_id)}
                        >
                          Salvar
                        </button>
                      </td>
                    ) : null}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </MaintenanceShell>
  );
}
