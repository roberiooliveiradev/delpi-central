import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import type { Slide } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DECK_HOME_ACTION_KEYTIPS } from "../utils/deckKeyTips";
import { DeckKeyTip } from "./DeckKeyTip";
import { DeckRibbonLargeButton } from "./deck/DeckRibbonLargeButton";

type Props = {
  slides: Slide[];
  selectedSlideId: string | null;
  onAdd: () => void;
  onSelect: (slideId: string) => void;
};

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const K = DECK_HOME_ACTION_KEYTIPS;

/**
 * Controles de slides no filmstrip (acima das prévias): nova tela + anterior/próximo.
 */
export function SlideFilmstripControls({
  slides,
  selectedSlideId,
  onAdd,
  onSelect,
}: Props) {
  const selectedIndex = selectedSlideId
    ? slides.findIndex((slide) => slide.id === selectedSlideId)
    : -1;

  function goTo(offset: number) {
    if (!slides.length) return;
    const base = selectedIndex >= 0 ? selectedIndex : 0;
    const next = (base + offset + slides.length) % slides.length;
    onSelect(slides[next]!.id);
  }

  return (
    <div className="td-deck-filmstrip__controls" aria-label="Controles de slides">
      <DeckRibbonLargeButton
        icon={Plus}
        label="Nova tela"
        hint={H.newSlide}
        primary
        keyTip={K.newSlide}
        onClick={onAdd}
      />
      <div className="td-deck-filmstrip__slide-nav" role="group" aria-label="Trocar slide">
        <DeckKeyTip letter={K.prevSlide} scope="actions">
          <HintAction hint={H.prevSlide} ariaLabel="Ajuda: Anterior">
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--icon td-deck-filmstrip__slide-nav-btn"
              disabled={slides.length < 2}
              onClick={() => goTo(-1)}
              aria-label="Slide anterior"
            >
              <ChevronLeft size={16} aria-hidden="true" />
            </button>
          </HintAction>
        </DeckKeyTip>
        <span className="td-deck-filmstrip__counter" aria-live="polite">
          {slides.length ? `${Math.max(selectedIndex, 0) + 1} / ${slides.length}` : "0 / 0"}
        </span>
        <DeckKeyTip letter={K.nextSlide} scope="actions">
          <HintAction hint={H.nextSlide} ariaLabel="Ajuda: Próximo">
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--icon td-deck-filmstrip__slide-nav-btn"
              disabled={slides.length < 2}
              onClick={() => goTo(1)}
              aria-label="Próximo slide"
            >
              <ChevronRight size={16} aria-hidden="true" />
            </button>
          </HintAction>
        </DeckKeyTip>
      </div>
    </div>
  );
}
