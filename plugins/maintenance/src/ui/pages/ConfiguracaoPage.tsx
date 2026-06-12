import { useEffect, useState } from "react";
import { Settings } from "lucide-react";

import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { fetchMotivos, fetchStatusPeca, type MotivoItem, type StatusItem } from "../../data/api/maintenanceApi";

type ConfiguracaoPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function ConfiguracaoPage({ getAccessToken, pathname, onNavigate }: ConfiguracaoPageProps) {
  const [motivos, setMotivos] = useState<MotivoItem[]>([]);
  const [status, setStatus] = useState<StatusItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchMotivos(getAccessToken), fetchStatusPeca(getAccessToken)])
      .then(([motivosData, statusData]) => {
        setMotivos(motivosData.items ?? []);
        setStatus(statusData.items ?? []);
      })
      .catch((err: Error) => setError(err.message));
  }, [getAccessToken]);

  return (
    <MaintenanceShell>
      <PageHeader
        title="Configuração"
        subtitle="Motivos de troca e regras de status preventivo."
        icon={Settings}
        currentPath={pathname}
        onNavigate={onNavigate}
      />

      {error ? <p className="dm-state-box dm-state-box--error">{error}</p> : null}

      <section className="dm-card">
        <h3 className="dm-card__title">Motivos de reposição</h3>
        <div className="dm-table-wrap">
          <table className="dm-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Descrição</th>
              </tr>
            </thead>
            <tbody>
              {motivos.map((item) => (
                <tr key={item.motivo_id}>
                  <td data-label="ID">{item.motivo_id}</td>
                  <td data-label="Descrição">{item.descricao}</td>
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
              </tr>
            </thead>
            <tbody>
              {status.map((item) => (
                <tr key={item.status_id}>
                  <td data-label="Status">{item.descricao}</td>
                  <td data-label="Operador">{item.operador}</td>
                  <td data-label="Percentual">{item.percentual}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </MaintenanceShell>
  );
}
