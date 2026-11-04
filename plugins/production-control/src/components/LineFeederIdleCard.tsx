import { PackageSearch } from "lucide-react";

import { copy } from "../content/copy";

type Props = {
  onCollect: () => void;
  disabled?: boolean;
};

/**
 * Estado inicial do Alimentador — cartão Liquid Glass com orientação
 * mínima e CTA Coletar no centro (antes da primeira consulta).
 */
export function LineFeederIdleCard({ onCollect, disabled = false }: Props) {
  const texts = copy.lineFeeder;

  return (
    <section className="ppc-feeder-idle" aria-label={texts.emptyTitle} role="status">
      <div className="ppc-feeder-idle__card">
        <span className="ppc-feeder-idle__glyph" aria-hidden="true">
          <PackageSearch size={22} strokeWidth={1.6} />
        </span>
        <h2 className="ppc-feeder-idle__title">{texts.emptyTitle}</h2>
        <p className="ppc-feeder-idle__body">{texts.emptyGuidance}</p>
        <button
          type="button"
          className="ppc-feeder-idle__cta"
          onClick={onCollect}
          disabled={disabled}
        >
          <PackageSearch size={18} strokeWidth={1.85} aria-hidden />
          <span>{texts.collectAction}</span>
        </button>
      </div>
    </section>
  );
}
