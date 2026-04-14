import { ChevronLeft, ChevronRight } from "lucide-react";

type PresentationEdgeNavigationProps = {
  onPrevious: () => void;
  onNext: () => void;
  previousDisabled?: boolean;
  nextDisabled?: boolean;
};

export function PresentationEdgeNavigation({
  onPrevious,
  onNext,
  previousDisabled = false,
  nextDisabled = false,
}: PresentationEdgeNavigationProps) {
  return (
    <>
      <div className="si-presentation-edge-nav si-presentation-edge-nav--left">
        <button
          type="button"
          className="si-presentation-edge-nav__button"
          onClick={onPrevious}
          disabled={previousDisabled}
          aria-label="Cena anterior"
          title="Cena anterior"
        >
          <ChevronLeft size={22} />
        </button>
      </div>

      <div className="si-presentation-edge-nav si-presentation-edge-nav--right">
        <button
          type="button"
          className="si-presentation-edge-nav__button"
          onClick={onNext}
          disabled={nextDisabled}
          aria-label="Próxima cena"
          title="Próxima cena"
        >
          <ChevronRight size={22} />
        </button>
      </div>
    </>
  );
}