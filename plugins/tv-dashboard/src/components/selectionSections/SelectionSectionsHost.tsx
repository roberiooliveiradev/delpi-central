import { useMemo, type ReactNode } from "react";

import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ActionsSection } from "./ActionsSection";
import { AlignMultiSection, OrganizeSection } from "./OrganizeSection";
import { AnimationSection } from "./AnimationSection";
import { DataSourceHintSection } from "./DataSourceHintSection";
import { FrameSizeSection } from "./FrameSizeSection";
import { ShapeChromeSection } from "./ShapeChromeSection";
import { ShapeGallerySection } from "./ShapeGallerySection";
import {
  TableBordersSection,
  TableStyleOptionsSection,
  TableStylesSection,
} from "./TableDesignSections";
import { TextBoxSection } from "./TextBoxSection";
import { TypographySection } from "./TypographySection";
import {
  resolveSelectionSections,
  SHARED_HOST_SECTIONS,
} from "./resolveSelectionSections";
import type { SelectionSectionId, SelectionSectionLayout } from "./types";

type Labels = Record<string, string>;

type Props = {
  layout: SelectionSectionLayout;
  labels?: Labels;
  /**
   * Se informado, renderiza só estes IDs (interseção com resolve).
   * Útil para injetar frame/organize no ribbon legado sem duplicar o resto.
   */
  only?: SelectionSectionId[];
  /**
   * Quando true, renderiza todas as seções resolvidas que já estão no host
   * (`SHARED_HOST_SECTIONS`). Default também filtra por SHARED.
   */
  full?: boolean;
};

function renderSection(
  id: SelectionSectionId,
  layout: SelectionSectionLayout,
  labels: Labels,
): ReactNode {
  switch (id) {
    case "frame":
      return <FrameSizeSection key={id} layout={layout} />;
    case "organize":
      return <OrganizeSection key={id} layout={layout} labels={labels} />;
    case "alignMulti":
      return <AlignMultiSection key={id} layout={layout} />;
    case "dataSourceHint":
      return <DataSourceHintSection key={id} layout={layout} />;
    case "typography":
      return <TypographySection key={id} layout={layout} />;
    case "textBox":
      return <TextBoxSection key={id} layout={layout} />;
    case "shapeGallery":
      return <ShapeGallerySection key={id} layout={layout} />;
    case "shapeChrome":
      return <ShapeChromeSection key={id} layout={layout} />;
    case "tableStyleOptions":
      return <TableStyleOptionsSection key={id} layout={layout} />;
    case "tableStyles":
      return <TableStylesSection key={id} layout={layout} />;
    case "tableBorders":
      return <TableBordersSection key={id} layout={layout} />;
    case "animation":
      return <AnimationSection key={id} layout={layout} />;
    case "actions":
      return <ActionsSection key={id} layout={layout} />;
    default:
      return null;
  }
}

/**
 * Host de seções Elemento compartilhadas (ribbon | pane).
 * Tipografia, Caixa, forma, tabela Design, frame/organize, animação/ações (pane).
 */
export function SelectionSectionsHost({
  layout,
  labels = {},
  only,
  full = false,
}: Props) {
  const {
    selected,
    selectedIds,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
  } = useComunicadoEditor();

  const sections = useMemo(() => {
    const resolved = resolveSelectionSections({
      selected,
      selectedIds,
      selectedChartPart,
      selectedKpiPart,
      selectedTablePart,
      selectedInputPart,
    });
    if (only) {
      const allow = new Set(only);
      return resolved.filter((id) => allow.has(id) && SHARED_HOST_SECTIONS.has(id));
    }
    // `full` e default: só seções já migradas (evita buracos null no ribbon).
    void full;
    return resolved.filter((id) => SHARED_HOST_SECTIONS.has(id));
  }, [
    selected,
    selectedIds,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
    only,
    full,
  ]);

  if (sections.length === 0) return null;

  if (layout === "ribbon") {
    return <>{sections.map((id) => renderSection(id, layout, labels))}</>;
  }

  return (
    <div className="td-selection-sections td-selection-sections--pane">
      {sections.map((id) => renderSection(id, layout, labels))}
    </div>
  );
}
