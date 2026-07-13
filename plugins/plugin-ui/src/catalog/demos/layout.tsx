import { Activity } from "lucide-react";
import { useState } from "react";

import { PUC_DASHBOARD_ROOT, PUC_PREFIX } from "../../app/bemPrefix";
import {
  ChartCard,
  chartCardBemClasses,
  ContentCard,
  contentCardBemClasses,
  FilterInputField,
  FiltersRow,
  filtersRowBemClasses,
  KpiCard,
  kpiCardBemClasses,
  PageHeader,
  pageHeaderBrandBemClasses,
  PanelCard,
  panelCardBemClasses,
  SectionCard,
  sectionCardKaizenBemClasses,
} from "../../components/layout";
import type { CatalogEntry } from "../types";

const pageHeaderCn = pageHeaderBrandBemClasses(PUC_PREFIX);
const panelCn = panelCardBemClasses(PUC_PREFIX);
const contentCn = contentCardBemClasses(PUC_PREFIX);
const kpiCn = kpiCardBemClasses(PUC_PREFIX);
const chartCn = chartCardBemClasses(PUC_PREFIX, { withActions: false });
const filtersCn = filtersRowBemClasses(PUC_PREFIX);
const sectionCn = sectionCardKaizenBemClasses(PUC_PREFIX);

export const layoutCatalogEntries: CatalogEntry[] = [
  {
    id: "layout.PageHeader",
    family: "layout",
    exportName: "PageHeader",
    title: "PageHeader",
    description: "Cabeçalho de página (layout brand / titleRow / stack).",
    docAnchor: "pageheader",
    propsSummary: ["layout", "title", "subtitle", "classNames", "labels"],
    demos: [
      {
        id: "brand",
        label: "Brand",
        render: () => (
          <PageHeader
            layout="brand"
            title="Catálogo UI"
            subtitle="Prévia dos componentes @delpi/plugin-ui"
            eyebrow="Design system"
            icon={<Activity size={28} strokeWidth={1.75} aria-hidden="true" />}
            classNames={pageHeaderCn}
            labels={{ refresh: "Atualizar", refreshing: "Atualizando…" }}
            onRefresh={() => undefined}
          />
        ),
      },
    ],
  },
  {
    id: "layout.PanelCard",
    family: "layout",
    exportName: "PanelCard",
    title: "PanelCard",
    description: "Seção com título — cartão de painel.",
    docAnchor: "panelcard",
    propsSummary: ["title", "children", "highlight"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <PanelCard title="Painel de exemplo" classNames={panelCn}>
            <p className="puc-muted">Conteúdo interno do painel.</p>
          </PanelCard>
        ),
      },
    ],
  },
  {
    id: "layout.ContentCard",
    family: "layout",
    exportName: "ContentCard",
    title: "ContentCard",
    description: "Cartão com header, descrição e body.",
    docAnchor: "contentcard",
    propsSummary: ["title", "description", "children"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <ContentCard
            title="Conteúdo"
            description="Descrição curta do bloco."
            classNames={contentCn}
          >
            <p className="puc-muted">Corpo do cartão.</p>
          </ContentCard>
        ),
      },
    ],
  },
  {
    id: "layout.KpiCard",
    family: "layout",
    exportName: "KpiCard",
    title: "KpiCard",
    description: "Cartão KPI departamental (meta, badges, ícone).",
    docAnchor: "kpicard",
    propsSummary: ["title", "value", "icon", "goalLabel"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <div className="puc-kpi-grid">
            <KpiCard
              title="OEE"
              titleHint="Overall Equipment Effectiveness"
              value="87,4%"
              goalLabel="85%"
              icon={<Activity size={22} aria-hidden="true" />}
              classNames={kpiCn}
              labels={{
                goalPrefix: "Meta",
                iddScorePrefix: "IDD",
                badgesStatus: "Status",
              }}
            />
          </div>
        ),
      },
    ],
  },
  {
    id: "layout.ChartCard",
    family: "layout",
    exportName: "ChartCard",
    title: "ChartCard",
    description: "Cartão de gráfico (header + body).",
    docAnchor: "chartcard",
    propsSummary: ["title", "hint", "children"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <ChartCard title="Evolução" hint="Série ilustrativa" classNames={chartCn}>
            <div className="puc-chart-placeholder">Área do gráfico (slot)</div>
          </ChartCard>
        ),
      },
    ],
  },
  {
    id: "layout.FiltersRow",
    family: "layout",
    exportName: "FiltersRow",
    title: "FiltersRow",
    description: "Linha de filtros com campos de input.",
    docAnchor: "filtersrow",
    propsSummary: ["children", "ariaLabel"],
    demos: [
      {
        id: "default",
        label: "Com FilterInputField",
        render: () => <FiltersRowDemo />,
      },
    ],
  },
  {
    id: "layout.SectionCard",
    family: "layout",
    exportName: "SectionCard",
    title: "SectionCard",
    description: "Seção com título, subtítulo e hint.",
    docAnchor: "sectioncard",
    propsSummary: ["title", "subtitle", "hint", "children"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <SectionCard
            title="Seção"
            subtitle="Subtítulo opcional"
            hint="Ajuda da seção"
            classNames={sectionCn}
            labels={{ titleHelpAriaLabel: (t) => `Ajuda: ${t}` }}
          >
            <p className="puc-muted">Conteúdo da seção.</p>
          </SectionCard>
        ),
      },
    ],
  },
];

function FiltersRowDemo() {
  const [month, setMonth] = useState("2026-07");

  return (
    <FiltersRow classNames={filtersCn} ariaLabel="Filtros de exemplo">
      <FilterInputField
        label="Mês"
        hint="Competência de referência"
        type="month"
        value={month}
        onChange={setMonth}
        classNames={filtersCn}
      />
      <div className={filtersCn.filterBox}>
        <span className="puc-muted">Escopo portal: {PUC_DASHBOARD_ROOT}</span>
      </div>
    </FiltersRow>
  );
}
