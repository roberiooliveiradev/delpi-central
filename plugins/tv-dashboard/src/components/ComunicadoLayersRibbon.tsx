import { ComunicadoLayersPanel } from "./deck/ComunicadoLayersPanel";

/** Aba Camadas na top bar — mesmo conteúdo do painel lateral, grade 1fr/1fr. */
export function ComunicadoLayersRibbon() {
  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--inspector">
      <ComunicadoLayersPanel layout="ribbon" />
    </div>
  );
}
