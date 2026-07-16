import { Activity } from "lucide-react";
import { useState } from "react";

import { PUC_DASHBOARD_ROOT, PUC_PREFIX } from "../../app/bemPrefix";
import { ActionButton, BackLink } from "../../components/actions";
import {
  ChartCard,
  chartCardBemClasses,
  ContentCard,
  contentCardBemClasses,
  DelpiKpiCard,
  DetailCard,
  detailCardProductionBemClasses,
  DetailFieldGrid,
  detailFieldGridBemClasses,
  FilterInputField,
  FiltersRow,
  filtersRowBemClasses,
  FitText,
  FormActions,
  formActionsBemClasses,
  FormGrid,
  formGridBemClasses,
  FormatPaneSection,
  FormatPaneShell,
  KpiCard,
  kpiCardBemClasses,
  MetricKpiCard,
  metricKpiCardBemClasses,
  PageHeader,
  pageHeaderBrandBemClasses,
  PanelCard,
  panelCardBemClasses,
  SectionBlock,
  sectionBlockBemClasses,
  SectionCard,
  sectionCardKaizenBemClasses,
  SimpleKpiCard,
  simpleKpiCardBemClasses,
} from "../../components/layout";
import type { CatalogEntryDraft } from "../types";

const pageHeaderCn = pageHeaderBrandBemClasses(PUC_PREFIX);
const panelCn = panelCardBemClasses(PUC_PREFIX);
const contentCn = contentCardBemClasses(PUC_PREFIX);
const kpiCn = kpiCardBemClasses(PUC_PREFIX);
const chartCn = chartCardBemClasses(PUC_PREFIX, { withActions: false });
const filtersCn = filtersRowBemClasses(PUC_PREFIX);
const sectionCn = sectionCardKaizenBemClasses(PUC_PREFIX);
const simpleKpiCn = simpleKpiCardBemClasses(PUC_PREFIX, "kpi-card", { withBody: true, withSubtitle: true });
const metricKpiCn = metricKpiCardBemClasses(PUC_PREFIX);
const detailCn = detailCardProductionBemClasses(PUC_PREFIX);
const detailGridCn = detailFieldGridBemClasses(PUC_PREFIX);
const formGridCn = formGridBemClasses(PUC_PREFIX);
const formActionsCn = formActionsBemClasses(PUC_PREFIX);
const sectionBlockCn = sectionBlockBemClasses(PUC_PREFIX);

export const layoutCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "layout.ActionButton",
    family: "layout",
    exportName: "ActionButton",
    title: "ActionButton",
    description: "Ações consistentes entre MFEs, com variantes sem CSS local.",
    docAnchor: "actionbutton-e-backlink",
    propsSummary: ["variant", "type", "disabled", "onClick"],
    demos: [
      {
        id: "variants",
        label: "Variantes",
        render: () => (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            <ActionButton variant="primary">Salvar</ActionButton>
            <ActionButton>Editar</ActionButton>
            <ActionButton variant="ghost">Atualizar</ActionButton>
            <ActionButton variant="link">Gerenciar</ActionButton>
          </div>
        ),
      },
    ],
  },
  {
    id: "layout.BackLink",
    family: "layout",
    exportName: "BackLink",
    title: "BackLink",
    description: "Ação de retorno para cabeçalhos e páginas internas.",
    docAnchor: "actionbutton-e-backlink",
    propsSummary: ["onClick", "className"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <BackLink onClick={() => undefined}>Voltar para atas</BackLink>,
      },
    ],
  },
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
  {
    id: "layout.DelpiKpiCard",
    family: "layout",
    exportName: "DelpiKpiCard",
    title: "DelpiKpiCard",
    description: "KPI canônico Delpi (primitivos / TV).",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <div className="puc-kpi-grid">
            <DelpiKpiCard label="OEE" value="87%" hint="Meta 85%" icon={<Activity size={22} />} />
          </div>
        ),
      },
    ],
  },
  {
    id: "layout.SimpleKpiCard",
    family: "layout",
    exportName: "SimpleKpiCard",
    title: "SimpleKpiCard",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <SimpleKpiCard
            title="Abertos"
            value="42"
            subtitle="últimos 30 dias"
            icon={<Activity size={22} />}
            classNames={simpleKpiCn}
          />
        ),
      },
    ],
  },
  {
    id: "layout.MetricKpiCard",
    family: "layout",
    exportName: "MetricKpiCard",
    title: "MetricKpiCard",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <MetricKpiCard
            label="Taxa"
            value="12,4%"
            hint="vs. mês anterior"
            tone="positive"
            icon={<Activity size={22} />}
            classNames={metricKpiCn}
          />
        ),
      },
    ],
  },
  {
    id: "layout.DetailCard",
    family: "layout",
    exportName: "DetailCard",
    title: "DetailCard",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <DetailCard
            title="Detalhe"
            titleHint="Ficha resumida"
            classNames={detailCn}
            labels={{ titleHelpAriaLabel: (t) => `Ajuda: ${t}` }}
          >
            <p className="puc-muted">Corpo do detalhe.</p>
          </DetailCard>
        ),
      },
    ],
  },
  {
    id: "layout.DetailFieldGrid",
    family: "layout",
    exportName: "DetailFieldGrid",
    title: "DetailFieldGrid",
    demos: [
      {
        id: "default",
        label: "Campos",
        render: () => (
          <DetailFieldGrid
            fields={[
              { label: "Código", value: "A-100" },
              { label: "Status", value: "Ativo" },
            ]}
            classNames={detailGridCn}
            labels={{ fieldHelpAriaLabel: (l) => `Ajuda: ${l}` }}
            valueFallback="—"
          />
        ),
      },
    ],
  },
  {
    id: "layout.FormGrid",
    family: "layout",
    exportName: "FormGrid",
    title: "FormGrid",
    demos: [
      {
        id: "default",
        label: "Grid",
        render: () => (
          <FormGrid classNames={formGridCn}>
            <div className="puc-field">Campo A</div>
            <div className="puc-field">Campo B</div>
          </FormGrid>
        ),
      },
    ],
  },
  {
    id: "layout.FormActions",
    family: "layout",
    exportName: "FormActions",
    title: "FormActions",
    demos: [
      {
        id: "default",
        label: "Ações",
        render: () => (
          <FormActions classNames={formActionsCn} align="end">
            <button type="button" className="puc-ghost-btn">
              Cancelar
            </button>
            <button type="button" className="puc-primary-btn">
              Salvar
            </button>
          </FormActions>
        ),
      },
    ],
  },
  {
    id: "layout.SectionBlock",
    family: "layout",
    exportName: "SectionBlock",
    title: "SectionBlock",
    demos: [
      {
        id: "default",
        label: "Bloco",
        render: () => (
          <SectionBlock title="Bloco" classNames={sectionBlockCn}>
            <p className="puc-muted">Conteúdo.</p>
          </SectionBlock>
        ),
      },
    ],
  },
  {
    id: "layout.FormatPaneSection",
    family: "layout",
    exportName: "FormatPaneSection",
    title: "FormatPaneSection",
    demos: [
      {
        id: "default",
        label: "Seção",
        render: () => (
          <FormatPaneSection title="Camadas" hint="Ordem de construção">
            <p className="puc-muted">Itens da seção.</p>
          </FormatPaneSection>
        ),
      },
    ],
  },
  {
    id: "layout.FormatPaneShell",
    family: "layout",
    exportName: "FormatPaneShell",
    title: "FormatPaneShell",
    demos: [
      {
        id: "default",
        label: "Shell",
        render: () => (
          <FormatPaneShell
            title="Formatar"
            tabs={[
              { id: "format", label: "Formatar" },
              { id: "data", label: "Dados" },
            ]}
            activeTabId="format"
            onTabChange={() => undefined}
          >
            <p className="puc-muted">Corpo do painel.</p>
          </FormatPaneShell>
        ),
      },
    ],
  },
  {
    id: "layout.FitText",
    family: "layout",
    exportName: "FitText",
    title: "FitText",
    demos: [
      {
        id: "default",
        label: "Ajuste",
        render: () => (
          <div style={{ width: 120, height: 48, border: "1px dashed var(--puc-border)" }}>
            <FitText>87,4%</FitText>
          </div>
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
