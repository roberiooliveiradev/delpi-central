import { GuidelineListPanel } from "./GuidelineListPanel";
import { GuidelineTestPanel } from "./GuidelineTestPanel";
import { GuidelineVersionPanel } from "./GuidelineVersionPanel";
import type { AdminGuideline, GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./AdminGuidelinesTab.css";

const DEFAULT_GUIDELINES: AdminGuideline[] = [
  {
    id: "no-hallucination",
    title: "Não inventar respostas",
    description: "Quando não houver fonte suficiente, o chat deve admitir limitação e pedir contexto.",
    status: "active",
    category: "behavior",
  },
  {
    id: "global-sources-first",
    title: "Priorizar fontes globais antes de conhecimento geral",
    description: "Documentos globais do admin devem orientar a resposta antes de fallback genérico.",
    status: "active",
    category: "rag",
  },
  {
    id: "authorized-tools",
    title: "Executar ferramentas autorizadas quando necessário",
    description: "Actions e ferramentas só devem ser usadas quando permitidas pelo contexto e permissões.",
    status: "active",
    category: "tools",
  },
];

type AdminGuidelinesTabProps = GuidelineBackendPlaceholders;

export function AdminGuidelinesTab(props: AdminGuidelinesTabProps) {
  return (
    <section className="mdc-admin-guidelines">
      <GuidelineListPanel
        guidelines={DEFAULT_GUIDELINES}
        publishGuideline={props.publishGuideline}
        archiveGuideline={props.archiveGuideline}
      />

      <GuidelineTestPanel testGuidelines={props.testGuidelines} />

      <GuidelineVersionPanel
        loadGuidelines={props.loadGuidelines}
        saveGuideline={props.saveGuideline}
      />
    </section>
  );
}
