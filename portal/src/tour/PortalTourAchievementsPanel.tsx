import { useContext, useEffect, useMemo, useState } from "react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi, type PortalTourAchievementsResponse } from "../data/coreApi";
import { resolvePortalTourAchievementIcon } from "./portalTourAchievementIcons";
import { PortalTourPreferencesToggle } from "./PortalTourPreferencesToggle";
import "./portalTourAchievements.css";

function formatUnlockedAt(value: string | null): string | null {
  if (!value) return null;
  try {
    return new Intl.DateTimeFormat("pt-BR", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return null;
  }
}

export function PortalTourAchievementsPanel() {
  const { getAccessToken, refreshToken } = useContext(AuthContext);
  const [data, setData] = useState<PortalTourAchievementsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const coreApi = useMemo(
    () =>
      new CoreApi(
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
        const response = await coreApi.getPortalTourAchievements();
        if (!cancelled) setData(response);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Falha ao carregar conquistas",
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
  }, [coreApi]);

  const unlockedItems = data?.items.filter((item) => item.unlocked) ?? [];
  const lockedItems = data?.items.filter((item) => !item.unlocked) ?? [];

  return (
    <div
      className="home-panel portal-tour-achievements-panel"
      role="region"
      data-tour="profile-tour-achievements"
      aria-labelledby="profile-tour-achievements-title"
    >
      <header className="home-panel-header portal-tour-achievements-header">
        <div>
          <h3 className="home-panel-title" id="profile-tour-achievements-title">
            Conquistas do portal
          </h3>
          <p className="home-panel-hint">
            Selos desbloqueados ao explorar a Minha DELPI no tour gamificado.
          </p>
        </div>
        {data ? (
          <div className="portal-tour-achievements-summary">
            <span className="portal-tour-achievements-level">{data.explorerLevel}</span>
            <div
              className="portal-tour-achievements-progress"
              role="progressbar"
              aria-valuenow={data.unlockedCount}
              aria-valuemin={0}
              aria-valuemax={Math.max(data.totalCount, 1)}
              aria-label="Progresso das conquistas"
            >
              <div
                className="portal-tour-achievements-progress__fill"
                style={{
                  width: `${
                    data.totalCount > 0
                      ? Math.min(100, Math.round((data.unlockedCount / data.totalCount) * 100))
                      : 0
                  }%`,
                }}
              />
            </div>
            <span className="portal-tour-achievements-count">
              {data.unlockedCount}/{data.totalCount} desbloqueadas
            </span>
          </div>
        ) : null}
      </header>

      <PortalTourPreferencesToggle />

      {loading ? (
        <p className="portal-tour-achievements-empty">Carregando conquistas…</p>
      ) : error ? (
        <p className="portal-tour-achievements-empty portal-tour-achievements-empty--error">
          {error}
        </p>
      ) : !data?.items.length ? (
        <p className="portal-tour-achievements-empty">
          Nenhuma conquista disponível ainda. Inicie o tour na home ou use o link
          abaixo.
        </p>
      ) : (
        <>
          {unlockedItems.length > 0 ? (
            <div className="portal-tour-achievements-group">
              <h4 className="portal-tour-achievements-group-title">Desbloqueadas</h4>
              <ul className="portal-tour-achievements-grid">
                {unlockedItems.map((item) => {
                  const Icon = resolvePortalTourAchievementIcon(item.id, true);
                  const unlockedLabel = formatUnlockedAt(item.unlockedAt);
                  return (
                    <li
                      key={item.id}
                      className="portal-tour-achievement-card is-unlocked"
                      title={item.description}
                    >
                      <span className="portal-tour-achievement-icon" aria-hidden>
                        <Icon size={20} />
                      </span>
                      <span className="portal-tour-achievement-title">
                        {item.title}
                      </span>
                      {unlockedLabel ? (
                        <span className="portal-tour-achievement-meta">
                          {unlockedLabel}
                        </span>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}

          {lockedItems.length > 0 ? (
            <div className="portal-tour-achievements-group">
              <h4 className="portal-tour-achievements-group-title">A descobrir</h4>
              <ul className="portal-tour-achievements-grid">
                {lockedItems.map((item) => {
                  const Icon = resolvePortalTourAchievementIcon(item.id, false);
                  return (
                    <li
                      key={item.id}
                      className="portal-tour-achievement-card is-locked"
                      title={item.description}
                    >
                      <span className="portal-tour-achievement-icon" aria-hidden>
                        <Icon size={18} />
                      </span>
                      <span className="portal-tour-achievement-title">
                        {item.title}
                      </span>
                      <span className="portal-tour-achievement-meta">
                        {item.description}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
