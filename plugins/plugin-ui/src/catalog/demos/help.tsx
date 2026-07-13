import { useState } from "react";

import {
  FieldLabel,
  HelpTooltip,
  HintAction,
  SectionHintLabel,
  TabHintCell,
  TitleWithHelp,
  titleWithHelpBemClasses,
} from "../../components/help";
import { PUC_PREFIX } from "../../app/bemPrefix";
import type { CatalogEntryDraft } from "../types";

const titleClasses = titleWithHelpBemClasses(PUC_PREFIX);

export const helpCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "help.HelpTooltip",
    family: "help",
    exportName: "HelpTooltip",
    title: "HelpTooltip",
    description: "Balão ao passar o mouse ou focar. Ícone ? por padrão; modo wrap envolve filho.",
    docAnchor: "helptooltip",
    propsSummary: ["content", "ariaLabel", "wrap", "placement"],
    demos: [
      {
        id: "default",
        label: "Ícone ?",
        render: () => (
          <HelpTooltip content="Explicação curta do catálogo." ariaLabel="Ajuda: exemplo" />
        ),
      },
      {
        id: "wrap",
        label: "Wrap",
        render: () => (
          <HelpTooltip content="Abre ao passar no botão." wrap placement="bottom" ariaLabel="Ajuda: salvar">
            <button type="button" className="puc-primary-btn">
              Salvar
            </button>
          </HelpTooltip>
        ),
      },
    ],
  },
  {
    id: "help.FieldLabel",
    family: "help",
    exportName: "FieldLabel",
    title: "FieldLabel",
    description: "Rótulo de formulário com ? opcional.",
    docAnchor: "fieldlabel",
    propsSummary: ["label", "hint", "htmlFor"],
    demos: [
      {
        id: "default",
        label: "Com hint",
        render: () => (
          <div className="puc-field">
            <FieldLabel htmlFor="puc-periodo" label="Período (dias)" hint="Janela de análise em dias corridos." />
            <input id="puc-periodo" className="puc-input" defaultValue="30" />
          </div>
        ),
      },
    ],
  },
  {
    id: "help.SectionHintLabel",
    family: "help",
    exportName: "SectionHintLabel",
    title: "SectionHintLabel",
    description: "Rótulo de seção (ribbon) com balão no hover.",
    docAnchor: "sectionhintlabel",
    propsSummary: ["label", "hint"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <SectionHintLabel label="Inserir" hint="Insere um elemento no canvas." className="puc-section-hint" />
        ),
      },
    ],
  },
  {
    id: "help.TabHintCell",
    family: "help",
    exportName: "TabHintCell",
    title: "TabHintCell",
    description: "Aba acessível + ícone ? como irmão (evita botão aninhado).",
    docAnchor: "tabhintcell",
    propsSummary: ["label", "hint", "active", "onSelect"],
    demos: [
      {
        id: "default",
        label: "Abas",
        render: () => <TabHintCellDemo />,
      },
    ],
  },
  {
    id: "help.HintAction",
    family: "help",
    exportName: "HintAction",
    title: "HintAction",
    description: "Envolve um controle com balão sem aninhar botões.",
    docAnchor: "hintaction",
    propsSummary: ["hint", "ariaLabel", "children"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <HintAction hint="Exporta o relatório atual." ariaLabel="Ajuda: exportar">
            <button type="button" className="puc-ghost-btn">
              Exportar
            </button>
          </HintAction>
        ),
      },
    ],
  },
  {
    id: "help.TitleWithHelp",
    family: "help",
    exportName: "TitleWithHelp",
    title: "TitleWithHelp",
    description: "Título + HelpTooltip com classes BEM do consumidor.",
    docAnchor: "titlewithhelp",
    propsSummary: ["title", "hint", "classNames", "labels"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <TitleWithHelp
            title="Indicadores"
            hint="Resumo dos KPIs do período."
            classNames={titleClasses}
            labels={{ titleHelpAriaLabel: (t) => `Ajuda: ${t}` }}
          />
        ),
      },
    ],
  },
];

function TabHintCellDemo() {
  const [active, setActive] = useState("geral");

  return (
    <div className="puc-tab-row" role="tablist" aria-label="Abas de exemplo">
      <TabHintCell
        label="Geral"
        hint="Visão geral do módulo."
        active={active === "geral"}
        onSelect={() => setActive("geral")}
      />
      <TabHintCell
        label="Detalhes"
        hint="Campos e metadados."
        active={active === "detalhes"}
        onSelect={() => setActive("detalhes")}
      />
    </div>
  );
}
