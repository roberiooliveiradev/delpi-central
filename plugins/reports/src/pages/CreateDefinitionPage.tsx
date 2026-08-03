import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ArrowLeft, Save } from "lucide-react";

import {
  createReportDefinition,
  listReportProviders,
} from "../api/reportsApi";
import type { ReportProviderInfo } from "../types/reports";
import { definitionPath, REPORTS_LIST_PATH } from "../utils/route";

const SHORTAGE_KEY = "safety_stock_shortage_30d";
const MANAGEMENT_KEY = "management_revenue_monthly";

const PROVIDER_FALLBACK_LABELS: Record<string, string> = {
  [SHORTAGE_KEY]: "Rupturas próximos 30 dias",
  [MANAGEMENT_KEY]: "Relatório Gerencial — Faturamento",
};

export function CreateDefinitionPage() {
  const [providers, setProviders] = useState<ReportProviderInfo[]>([]);
  const [providerKey, setProviderKey] = useState(SHORTAGE_KEY);
  const [name, setName] = useState("Rupturas próximos 30 dias");
  const [branch, setBranch] = useState("01");
  const [horizonDays, setHorizonDays] = useState(30);
  const [customerLimit, setCustomerLimit] = useState(20);
  const [asOfDate, setAsOfDate] = useState("");
  const [active, setActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadingProviders, setLoadingProviders] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const payload = await listReportProviders(controller.signal);
        if (controller.signal.aborted) return;
        setProviders(payload.items);
        if (payload.items.length > 0) {
          const preferred =
            payload.items.find((item) => item.key === SHORTAGE_KEY) ??
            payload.items[0];
          setProviderKey(preferred.key);
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar os providers.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoadingProviders(false);
        }
      }
    })();
    return () => controller.abort();
  }, []);

  const selected = useMemo(
    () => providers.find((item) => item.key === providerKey) ?? null,
    [providers, providerKey],
  );

  useEffect(() => {
    const label =
      (selected?.paramsSchema?.displayName as string | undefined) ||
      PROVIDER_FALLBACK_LABELS[providerKey] ||
      providerKey;
    setName(label);
  }, [providerKey, selected]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const params =
        providerKey === MANAGEMENT_KEY
          ? {
              customerLimit,
              ...(asOfDate.trim() ? { asOfDate: asOfDate.trim() } : {}),
            }
          : {
              branch,
              horizonDays,
            };
      const created = await createReportDefinition({
        name: name.trim(),
        providerKey,
        params,
        active,
      });
      window.location.assign(definitionPath(created.id));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Não foi possível criar a definição.",
      );
      setSaving(false);
    }
  }

  const isManagement = providerKey === MANAGEMENT_KEY;

  return (
    <div className="rp-page-content">
      <header className="rp-page-header">
        <div className="rp-page-header__shell">
          <div className="rp-page-header__main">
            <div className="rp-page-header__brand">
              <div className="rp-page-header__titles">
                <p className="rp-page-header__eyebrow">Delpi Reports</p>
                <div className="rp-page-header__title-row">
                  <h1>Nova definição</h1>
                </div>
                <p className="rp-page-header__subtitle">
                  Escolha o tipo de relatório e os parâmetros iniciais.
                </p>
              </div>
            </div>
            <div className="rp-page-header__actions">
              <a className="rp-btn rp-btn--ghost" href={REPORTS_LIST_PATH}>
                <ArrowLeft size={16} aria-hidden />
                Voltar
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

      <section className="rp-card">
        <div className="rp-card__header">
          <div>
            <h2 className="rp-card__title">Parâmetros</h2>
            <p className="rp-card__hint">
              {loadingProviders
                ? "Carregando providers…"
                : `Provider: ${providerKey}`}
            </p>
          </div>
        </div>

        <form className="rp-form-grid" onSubmit={(e) => void handleSubmit(e)}>
          <label className="rp-field rp-field--full">
            <span>Tipo de relatório</span>
            <select
              value={providerKey}
              onChange={(e) => setProviderKey(e.target.value)}
              disabled={loadingProviders || providers.length === 0}
            >
              {providers.map((item) => {
                const label =
                  (item.paramsSchema?.displayName as string | undefined) ||
                  PROVIDER_FALLBACK_LABELS[item.key] ||
                  item.key;
                return (
                  <option key={item.key} value={item.key}>
                    {label}
                  </option>
                );
              })}
            </select>
          </label>

          <label className="rp-field rp-field--full">
            <span>Nome</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength={200}
            />
          </label>

          {isManagement ? (
            <>
              <label className="rp-field">
                <span>Top clientes</span>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={customerLimit}
                  onChange={(e) =>
                    setCustomerLimit(Number(e.target.value) || 20)
                  }
                />
              </label>
              <label className="rp-field">
                <span>Data referência (opcional)</span>
                <input
                  type="date"
                  value={asOfDate}
                  onChange={(e) => setAsOfDate(e.target.value)}
                />
              </label>
              <p className="rp-inline-note rp-field--full">
                Sem data de referência, o envio usa o mês civil anterior à data
                do disparo (agenda mensal no dia 1).
              </p>
            </>
          ) : (
            <>
              <label className="rp-field">
                <span>Filial</span>
                <select
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                >
                  <option value="01">01 — Jaraguá do Sul/SC</option>
                  <option value="02">02 — Rio Bananal/ES</option>
                </select>
              </label>

              <label className="rp-field">
                <span>Horizonte (dias)</span>
                <input
                  type="number"
                  min={1}
                  max={365}
                  value={horizonDays}
                  onChange={(e) =>
                    setHorizonDays(Number(e.target.value) || 30)
                  }
                />
              </label>
            </>
          )}

          <label className="rp-switch rp-field--full">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
            />
            Definição ativa
          </label>

          {error ? (
            <p className="rp-banner rp-banner--error rp-field--full">{error}</p>
          ) : null}

          <div className="rp-field--full">
            <button
              type="submit"
              className="rp-btn rp-btn--primary"
              disabled={saving || loadingProviders}
            >
              <Save size={16} aria-hidden />
              {saving ? "Salvando…" : "Criar definição"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
