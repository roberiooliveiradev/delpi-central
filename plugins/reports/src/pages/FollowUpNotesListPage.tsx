import { useCallback, useEffect, useState } from "react";
import { ClipboardList, RefreshCw } from "lucide-react";

import { listReportDefinitions } from "../api/reportsApi";
import type { ReportDefinition } from "../types/reports";
import { formatBranchUnitLabel } from "../utils/format";
import { followUpPath } from "../utils/route";

const SHORTAGE_PROVIDER = "safety_stock_shortage_30d";

export function FollowUpNotesListPage() {
  const [items, setItems] = useState<ReportDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const payload = await listReportDefinitions(signal);
      if (signal?.aborted) return;
      const filtered = payload.items.filter(
        (item) =>
          item.active &&
          String(item.providerKey || "").trim() === SHORTAGE_PROVIDER,
      );
      setItems(filtered);
    } catch (err) {
      if (signal?.aborted) return;
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível carregar as definições.",
      );
      setItems([]);
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);

  return (
    <div className="rp-page-content">
      <header className="rp-page-header">
        <div className="rp-page-header__shell">
          <div className="rp-page-header__main">
            <div className="rp-page-header__brand">
              <div className="rp-page-header__titles">
                <p className="rp-page-header__eyebrow">Delpi Reports</p>
                <div className="rp-page-header__title-row">
                  <h1>
                    <ClipboardList size={28} aria-hidden />
                    Acompanhamentos
                  </h1>
                </div>
                <p className="rp-page-header__subtitle">
                  Escolha o relatório de rupturas para registrar comentários na
                  Observação do e-mail.
                </p>
              </div>
            </div>
            <div className="rp-page-header__actions">
              <button
                type="button"
                className="rp-btn rp-btn--ghost"
                disabled={loading}
                onClick={() => void reload()}
              >
                <RefreshCw
                  size={16}
                  aria-hidden
                  className={loading ? "rp-spin" : undefined}
                />
                Atualizar
              </button>
            </div>
          </div>
          <div className="rp-page-header__brand-bar" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      </header>

      {error ? (
        <p className="rp-banner rp-banner--error" role="alert">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className="rp-banner">Carregando…</p>
      ) : items.length === 0 ? (
        <p className="rp-empty">
          Nenhuma definição ativa de rupturas 30 dias encontrada.
        </p>
      ) : (
        <ul className="rp-list">
          {items.map((item) => (
            <li key={item.id} className="rp-list__item">
              <a href={followUpPath(item.id)}>
                <strong>{item.name}</strong>
                <span>
                  {formatBranchUnitLabel(String(item.params.branch ?? ""))}
                </span>
                <span className="rp-pill rp-pill--info">Abrir</span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
