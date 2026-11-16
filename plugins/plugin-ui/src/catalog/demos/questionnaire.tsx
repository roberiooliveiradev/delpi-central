import type { ReactNode } from "react";

import { PUC_PREFIX } from "../../app/bemPrefix";
import {
  FormPageLayout,
  QuestionnaireThemeScope,
  useQuestionnaireColorScheme,
} from "../../components/forms/questionnaire";
import type { CatalogEntryDraft } from "../types";

function ThemeToggleButton() {
  const { scheme, toggle } = useQuestionnaireColorScheme();
  return (
    <button
      type="button"
      className="puc-questionnaire-theme-btn"
      onClick={toggle}
    >
      Alternar tema ({scheme === "dark" ? "escuro" : "claro"})
    </button>
  );
}

function SampleCards({ actions }: { actions?: ReactNode }) {
  return (
    <>
      <div className="puc-questionnaire-card">
        <strong>Cartão de exemplo</strong>
        <p>Conteúdo neutro do kit — superfícies, bordas e texto seguem os tokens do tema.</p>
        {actions}
      </div>
      <div className="puc-questionnaire-card">
        <strong>Segundo cartão</strong>
        <p>O layout sobrepõe a coluna à faixa da marca e centraliza o conteúdo.</p>
      </div>
    </>
  );
}

type FrameProps = {
  colorScheme?: "auto" | "light" | "dark";
  band?: "compact" | "tall";
  withToggle?: boolean;
};

function DemoFrame({ colorScheme, band = "compact", withToggle }: FrameProps) {
  return (
    <div className="puc-questionnaire-frame">
      <QuestionnaireThemeScope prefix={PUC_PREFIX} colorScheme={colorScheme}>
        <FormPageLayout prefix={PUC_PREFIX} band={band}>
          <SampleCards actions={withToggle ? <ThemeToggleButton /> : undefined} />
        </FormPageLayout>
      </QuestionnaireThemeScope>
    </div>
  );
}

export const questionnaireCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "forms.QuestionnaireThemeScope",
    family: "forms",
    exportName: "QuestionnaireThemeScope",
    title: "QuestionnaireThemeScope",
    description:
      "Raiz temática do kit de formulário: resolve auto/light/dark, aplica data-color-scheme e expõe o tema da visita (sem persistência).",
    docAnchor: "questionnaire-theme-scope-e-formpagelayout",
    propsSummary: ["colorScheme", "prefix", "className", "children"],
    demos: [
      {
        id: "auto",
        label: "auto + alternar",
        render: () => <DemoFrame colorScheme="auto" withToggle />,
      },
      {
        id: "fixed",
        label: "claro × escuro fixos",
        render: () => (
          <div className="puc-questionnaire-pair">
            <DemoFrame colorScheme="light" />
            <DemoFrame colorScheme="dark" />
          </div>
        ),
      },
    ],
  },
  {
    id: "forms.FormPageLayout",
    family: "forms",
    exportName: "FormPageLayout",
    title: "FormPageLayout",
    description:
      "Página do kit de formulário: faixa da marca (compact/tall) + coluna sobreposta (16 px / máx. 760 px), quebra em 600 px.",
    docAnchor: "questionnaire-theme-scope-e-formpagelayout",
    propsSummary: ["band", "prefix", "className", "children"],
    demos: [
      {
        id: "bands",
        label: "compact × tall",
        render: () => (
          <div className="puc-questionnaire-pair">
            <DemoFrame colorScheme="auto" band="compact" />
            <DemoFrame colorScheme="auto" band="tall" />
          </div>
        ),
      },
    ],
  },
];
