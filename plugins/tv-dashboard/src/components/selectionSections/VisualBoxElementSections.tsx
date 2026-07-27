import { FormatRibbonTypographySections } from "../formatRibbon/FormatRibbonTypographySections";
import { VisualBoxFormaChrome } from "../formatRibbon/VisualBoxFormaChrome";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import type { SelectionSectionLayout } from "./types";
import { resolveVisualBoxElementCapabilitiesForSelection } from "./visualBoxElementCapabilities";

/**
 * Faixa Elemento da caixa visual (texto / título / forma) — ordem fixa:
 * tipografia → Forma (com flags por tipo). Rabo display/organize/actions
 * continua em `withCommonTail` via seção `visualBox`.
 * Multi-seleção: capabilities = AND de todos os blocos selecionados.
 */
export function VisualBoxElementSections({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, selectedBlocks, selectedIds } = useComunicadoEditor();
  const blocks =
    selectedIds.length > 1
      ? selectedBlocks
      : selected
        ? [selected]
        : [];
  const caps = resolveVisualBoxElementCapabilitiesForSelection(blocks);
  if (!caps) return null;

  return (
    <>
      {layout === "pane" ? (
        <div className="td-selection-section td-selection-section--pane-typography">
          <FormatRibbonTypographySections embed capabilities={caps} />
        </div>
      ) : (
        <FormatRibbonTypographySections capabilities={caps} />
      )}
      <VisualBoxFormaChrome layout={layout} />
    </>
  );
}
