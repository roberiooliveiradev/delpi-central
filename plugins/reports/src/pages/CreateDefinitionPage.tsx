import { useState, type FormEvent } from "react";
import { ArrowLeft, Save } from "lucide-react";

import { createReportDefinition } from "../api/reportsApi";
import { definitionPath, REPORTS_LIST_PATH } from "../utils/route";

const PROVIDER_KEY = "safety_stock_shortage_30d";

export function CreateDefinitionPage() {
  const [name, setName] = useState("Rupturas próximos 30 dias");
  const [branch, setBranch] = useState("01");
  const [horizonDays, setHorizonDays] = useState(30);
  const [active, setActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createReportDefinition({
        name: name.trim(),
        providerKey: PROVIDER_KEY,
        params: {
          branch,
          horizonDays,
        },
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
                  Relatório de rupturas projetadas nos próximos dias (estoque
                  de segurança).
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
              Provider: <code>{PROVIDER_KEY}</code>
            </p>
          </div>
        </div>

        <form className="rp-form-grid" onSubmit={(e) => void handleSubmit(e)}>
          <label className="rp-field rp-field--full">
            <span>Nome</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength={200}
            />
          </label>

          <label className="rp-field">
            <span>Filial</span>
            <select value={branch} onChange={(e) => setBranch(e.target.value)}>
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
              onChange={(e) => setHorizonDays(Number(e.target.value) || 30)}
            />
          </label>

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
              disabled={saving}
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
