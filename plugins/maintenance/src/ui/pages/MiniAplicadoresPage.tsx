import { useCallback, useEffect, useState } from "react";
import { Hammer, RefreshCw } from "lucide-react";

import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import { fetchFerramentas, type FerramentaItem } from "../../data/api/maintenanceApi";

type MiniAplicadoresPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  onNavigate: (path: string) => void;
  codigoFerramenta?: string;
};

export function MiniAplicadoresPage({
  getAccessToken,
  pathname,
  onNavigate,
  codigoFerramenta,
}: MiniAplicadoresPageProps) {
  const [descricao, setDescricao] = useState("");
  const [items, setItems] = useState<FerramentaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFerramentas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFerramentas(
        { descricao: descricao.trim() || undefined, page: 1, page_size: 50 },
        getAccessToken,
      );
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar ferramentas.");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [descricao, getAccessToken]);

  useEffect(() => {
    void loadFerramentas();
  }, [loadFerramentas]);

  return (
    <MaintenanceShell>
      <PageHeader
        title={codigoFerramenta ? `Ferramenta ${codigoFerramenta}` : "Mini-aplicadores"}
        subtitle={
          codigoFerramenta
            ? "Detalhe e histórico de reposições — CRUD na Fase 1."
            : "Ferramentas dos grupos 23 e 24 via api-delpi."
        }
        icon={Hammer}
        currentPath={pathname}
        onNavigate={onNavigate}
        actions={
          <button
            type="button"
            className="dm-primary-btn"
            onClick={() => void loadFerramentas()}
            disabled={loading}
          >
            <RefreshCw size={16} />
            {loading ? "Carregando…" : "Atualizar"}
          </button>
        }
      />

      {!codigoFerramenta ? (
        <>
          <section className="dm-card dm-filter-bar">
            <label className="dm-field">
              <span>Buscar por descrição</span>
              <input
                value={descricao}
                onChange={(event) => setDescricao(event.target.value)}
                placeholder="Ex.: 23-"
              />
            </label>
            <button type="button" className="dm-primary-btn" onClick={() => void loadFerramentas()}>
              Buscar
            </button>
          </section>

          <section className="dm-card">
            <div className="dm-card__header">
              <h3 className="dm-card__title">Ferramentas</h3>
              <span className="dm-badge">{total} registro(s)</span>
            </div>

            {error ? <p className="dm-state-box dm-state-box--error">{error}</p> : null}

            <div className="dm-table-wrap">
              <table className="dm-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Descrição</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 && !loading ? (
                    <tr>
                      <td colSpan={2} className="dm-table__empty">
                        Nenhuma ferramenta encontrada.
                      </td>
                    </tr>
                  ) : null}
                  {items.map((item) => (
                    <tr key={item.codigo}>
                      <td data-label="Código">
                        <button
                          type="button"
                          className="dm-link-btn"
                          onClick={() =>
                            onNavigate(`${MAINTENANCE_ROUTES.miniAplicadores}/${item.codigo}`)
                          }
                        >
                          {item.codigo}
                        </button>
                      </td>
                      <td data-label="Descrição">{item.descricao}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : (
        <section className="dm-card">
          <p className="dm-state-box">
            Detalhe completo (reposições, peças, componentes) será entregue na Fase 1.
          </p>
          <button
            type="button"
            className="dm-ghost-btn"
            onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadores)}
          >
            Voltar para lista
          </button>
        </section>
      )}
    </MaintenanceShell>
  );
}
