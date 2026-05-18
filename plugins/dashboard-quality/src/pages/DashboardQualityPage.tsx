import { ShieldCheck } from "lucide-react";
import "../App.css";

const PLANNED_MODULES = [
  "PPM interno e externo",
  "Kaizens",
  "Auditoria 5S",
  "Não conformidades (TOTVS)",
] as const;

export function DashboardQualityPage() {
  return (
    <div className="dashboard-quality">
      <header className="dq-header">
        <div className="dq-header__icon" aria-hidden="true">
          <ShieldCheck size={32} strokeWidth={1.75} />
        </div>
        <div>
          <h1 className="dq-header__title">Dashboard Qualidade</h1>
          <p className="dq-header__subtitle">
            Painel analítico conectado à api-delpi. Em desenvolvimento — Fase 1
            do roadmap.
          </p>
        </div>
      </header>

      <section className="dq-card">
        <h2 className="dq-card__title">Módulos previstos</h2>
        <ul className="dq-module-list">
          {PLANNED_MODULES.map((label) => (
            <li key={label}>{label}</li>
          ))}
        </ul>
        <p className="dq-card__hint">
          API: <code>/apps/api-delpi/quality/*</code> — permissão{" "}
          <code>dashboard-quality.view</code> ou{" "}
          <code>api-delpi.quality.access</code>
        </p>
      </section>
    </div>
  );
}
