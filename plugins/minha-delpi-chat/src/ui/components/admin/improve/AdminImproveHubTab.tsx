import { SectionHintLabel } from "@delpi/plugin-ui/index";
import { ArrowRight } from "lucide-react";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import { buildAdminHref, type AdminNavState } from "../../../../navigation/adminNavigation";
import { navigateChatHref } from "../../../../navigation/chatNavigation";
import { AdminTabHeader } from "../shared/AdminTabHeader";

import "./AdminImproveHubTab.css";

const HITL_CARDS: Array<{
  id: string;
  title: string;
  description: string;
  hint: string;
  nav: AdminNavState;
}> = [
  {
    id: "evaluations",
    title: "Avaliações humanas",
    description: ADMIN_HELP.fields.improve.evaluations,
    hint: ADMIN_HELP.fields.improve.evaluations,
    nav: { section: "quality", subTab: "evaluations" },
  },
  {
    id: "learning-candidates",
    title: "Candidatos de aprendizagem",
    description: ADMIN_HELP.fields.improve.candidates,
    hint: ADMIN_HELP.fields.improve.candidates,
    nav: { section: "knowledge", subTab: "learning", page: "candidates" },
  },
  {
    id: "metrics-feedback",
    title: "Feedback nas métricas",
    description: ADMIN_HELP.fields.improve.feedback,
    hint: ADMIN_HELP.fields.improve.feedback,
    nav: { section: "quality", subTab: "metrics", page: "feedback" },
  },
];

export function AdminImproveHubTab() {
  return (
    <section className="mdc-admin-improve" aria-label="Melhoria contínua">
      <AdminTabHeader
        eyebrow="Qualidade"
        title="Melhoria contínua"
        description="Hub HITL: avaliações, candidatos de aprendizagem e feedback — sem fundir as filas."
        helpHint={ADMIN_HELP.pages.improve}
      />

      <div className="mdc-admin-improve__grid">
        {HITL_CARDS.map((card) => (
          <article key={card.id} className="mdc-admin-improve__card">
            <h3>
              <SectionHintLabel label={card.title} hint={card.hint} />
            </h3>
            <p>{card.description}</p>
            <button
              type="button"
              className="mdc-admin-btn mdc-admin-btn--primary"
              onClick={() => navigateChatHref(buildAdminHref(card.nav))}
            >
              Abrir
              <ArrowRight size={15} aria-hidden="true" />
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
