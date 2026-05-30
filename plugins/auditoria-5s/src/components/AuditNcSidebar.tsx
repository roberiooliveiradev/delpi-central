import { CheckCircle2 } from "lucide-react";

import { NC_PRIORITY_OPTIONS } from "../constants/audit5s";

const TIPS = [
  "Descreva objetivamente o que foi observado.",
  "Informe a causa raiz identificada.",
  "Defina responsável e prazo realistas.",
  "Priorize ações com maior impacto no posto.",
];

export function AuditNcSidebar() {
  return (
    <aside className="a5s-nc-sidebar" aria-label="Orientações para registro de NC">
      <section className="a5s-nc-sidebar__card">
        <h3>Boas práticas para registrar NCs</h3>
        <ul className="a5s-nc-sidebar__tips">
          {TIPS.map((tip) => (
            <li key={tip}>
              <CheckCircle2 size={16} aria-hidden />
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="a5s-nc-sidebar__card">
        <h3>Legenda de prioridade</h3>
        <ul className="a5s-nc-sidebar__legend">
          {NC_PRIORITY_OPTIONS.map((item) => (
            <li key={item.value}>
              <span className={`a5s-priority-dot a5s-priority-dot--${item.tone}`} aria-hidden />
              <div>
                <strong>{item.label}</strong>
                <p>
                  {item.value === "high"
                    ? "Risco alto ou impacto imediato na operação."
                    : item.value === "medium"
                      ? "Risco moderado ou impacto relevante."
                      : "Risco baixo ou impacto limitado."}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </aside>
  );
}
