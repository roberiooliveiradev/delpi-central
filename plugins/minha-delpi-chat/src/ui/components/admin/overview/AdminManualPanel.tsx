import { ADMIN_MANUAL_PERSONAS } from "../../../../content/adminManualContent";
import type { AdminNavState } from "../../../../navigation/adminNavigation";

import "./AdminManualPanel.css";

type AdminManualPanelProps = {
  onOpen: (nav: AdminNavState) => void;
};

export function AdminManualPanel({ onOpen }: AdminManualPanelProps) {
  return (
    <article className="mdc-admin-manual" aria-label="Manual do admin por persona">
      <header className="mdc-admin-manual__header">
        <h3>Manual por persona</h3>
        <p>
          Atalhos curtos para curadoria, plataforma e auditoria. Detalhes de cada tela
          ficam nos tooltips de Ajuda do cabeçalho.
        </p>
      </header>

      <div className="mdc-admin-manual__grid">
        {ADMIN_MANUAL_PERSONAS.map((persona) => (
          <section key={persona.id} className="mdc-admin-manual__persona">
            <h4>{persona.title}</h4>
            <p>{persona.summary}</p>
            <ol>
              {persona.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <div className="mdc-admin-manual__links">
              {persona.links.map((link) => (
                <button
                  key={link.label}
                  type="button"
                  onClick={() => onOpen(link.nav)}
                >
                  {link.label}
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </article>
  );
}
