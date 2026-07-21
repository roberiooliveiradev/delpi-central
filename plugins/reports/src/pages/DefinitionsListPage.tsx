import { useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { listReportDefinitions } from "../api/reportsApi";
import type { ReportDefinition } from "../types/reports";
import { formatBranchUnitLabel } from "../utils/format";
import { definitionPath, REPORTS_NEW_PATH } from "../utils/route";

export function DefinitionsListPage() {
  const [items, setItems] = useState<ReportDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await listReportDefinitions(controller.signal);
        setItems(data.items);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar as definições.",
        );
        setItems([]);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => controller.abort();
  }, []);

  return (
    <div className="rp-page-content">
      <header className="rp-page-header">
        <div className="rp-page-header__shell">
          <div className="rp-page-header__main">
            <div className="rp-page-header__brand">
              <div className="rp-page-header__titles">
                <p className="rp-page-header__eyebrow">Delpi Reports</p>
                <div className="rp-page-header__title-row">
                  <h1>Relatórios</h1>
                </div>
                <p className="rp-page-header__subtitle">
                  Cadastre, agende e envie relatórios por e-mail aos
                  colaboradores.
                </p>
              </div>
            </div>
            <div className="rp-page-header__actions">
              <a className="rp-btn rp-btn--primary" href={REPORTS_NEW_PATH}>
                <Plus size={16} aria-hidden />
                Novo relatório
              </a>
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

      {loading ? <p className="rp-banner">Carregando…</p> : null}
      {error ? (
        <p className="rp-banner rp-banner--error">{error}</p>
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <p className="rp-empty">
          Nenhuma definição cadastrada. Use «Novo relatório» para começar.
        </p>
      ) : null}

      {!loading && items.length > 0 ? (
        <ul className="rp-list">
          {items.map((item) => (
            <li key={item.id} className="rp-list__item">
              <a href={definitionPath(item.id)}>
                <strong>{item.name}</strong>
                <span>{formatBranchUnitLabel(String(item.params.branch))}</span>
                <span
                  className={
                    item.active
                      ? "rp-pill rp-pill--success"
                      : "rp-pill rp-pill--muted"
                  }
                >
                  {item.active ? "Ativa" : "Inativa"}
                </span>
              </a>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
