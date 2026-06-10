import { useContext, useEffect, useMemo, useState } from "react";
import { Compass } from "lucide-react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { PortalTourExplorersResponse } from "../../../data/coreApi";
import { PORTAL_TOUR_VERSION } from "../../../tour/portalTourStorage";
import { formatGeneratedAt } from "./StatsShared";

const STATUS_LABELS: Record<string, string> = {
  exploring: "Explorando",
  completed: "Concluiu",
  dismissed: "Pulou",
};

export function PortalTourExplorersPanel() {
  const { getAccessToken, refreshToken } = useContext(AuthContext);
  const [data, setData] = useState<PortalTourExplorersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const adminApi = useMemo(
    () =>
      new AdminApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await adminApi.listPortalTourExplorers({
          tourVersion: PORTAL_TOUR_VERSION,
          status: "exploring",
          limit: 12,
        });
        if (!cancelled) setData(response);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Falha ao carregar exploradores",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [adminApi]);

  const items = data?.items ?? [];

  return (
    <section className="admin-stats__panel admin-stats__panel--wide">
      <div className="admin-stats-panel__title-row">
        <h5>
          <Compass size={14} aria-hidden="true" />
          Tour do portal — quem está explorando
        </h5>
        <span className="admin-stats-panel__badge">{data?.total ?? 0}</span>
      </div>
      <p className="admin-stats-panel__lede">
        Usuários com o tour gamificado em andamento na versão atual (
        {PORTAL_TOUR_VERSION}).
      </p>

      {loading ? (
        <p className="admin-stats__empty">Carregando…</p>
      ) : error ? (
        <p className="admin-stats__empty">{error}</p>
      ) : items.length === 0 ? (
        <p className="admin-stats__empty">
          Ninguém explorando o tour neste momento.
        </p>
      ) : (
        <ul
          className="admin-stats-least-engaged-list"
          aria-label="Usuários explorando o tour do portal"
        >
          {items.map((item) => (
            <li key={item.userId} className="admin-stats-least-engaged-item">
              <div className="admin-stats-least-engaged-item__head">
                <div>
                  <strong>{item.name}</strong>
                  <span className="admin-stats-least-engaged-item__email">
                    {item.email}
                  </span>
                </div>
                <div className="admin-stats-least-engaged-item__metrics">
                  <span>{STATUS_LABELS[item.status] ?? item.status}</span>
                  <span>{item.completedQuestCount} desafios</span>
                </div>
              </div>
              <div className="admin-stats-least-engaged-item__meta">
                <span>Início: {formatGeneratedAt(item.startedAt)}</span>
                <span>
                  Última atividade: {formatGeneratedAt(item.lastActivityAt)}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
