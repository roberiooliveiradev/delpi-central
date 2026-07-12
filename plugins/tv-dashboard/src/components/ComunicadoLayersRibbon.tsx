import { ComunicadoLayersPanel } from "./deck/ComunicadoLayersPanel";

/** Aba Camadas na top bar — mesmo conteúdo do painel lateral. */
export function ComunicadoLayersRibbon() {
  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--inspector">
      <div className="td-deck-ribbon__inspector">
        <ComunicadoLayersPanel pane={false} />
      </div>
    </div>
  );
}
