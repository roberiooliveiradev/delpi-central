import { ComunicadoFormatRibbon } from "./ComunicadoFormatRibbon";
import { ComunicadoInsertRibbon } from "./ComunicadoInsertRibbon";
import { DeckRibbonShell } from "./deck/DeckRibbonShell";

type Labels = Record<string, string>;

/** Ribbon legado (modo embutido) — insert + format em sequência. */
export function ComunicadoEditorRibbon({ labels = {} }: { labels?: Labels }) {
  return (
    <DeckRibbonShell embedded>
      <ComunicadoInsertRibbon labels={labels} />
      <ComunicadoFormatRibbon labels={labels} />
    </DeckRibbonShell>
  );
}
