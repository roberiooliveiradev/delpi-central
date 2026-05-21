import { StatusBadge } from "./StatusBadge";
import "./IgdHeroCard.css";

export const IGD_HERO_DESCRIPTION =
  "O IGD consolida a performance dos principais departamentos da empresa em uma nota única de 0 a 10, apresentada no painel estratégico.";

type IgdHeroCardProps = {
  igd: number;
  igdExact: number;
  classification: string;
  strongestDepartment: string;
  watchDepartment: string;
};

export function IgdHeroCard({
  igd,
  igdExact,
  classification,
  strongestDepartment,
  watchDepartment,
}: IgdHeroCardProps) {
  return (
    <section className="si-igd-hero">
      <div className="si-igd-hero__content">
        <p className="si-igd-hero__eyebrow">Índice Global Delpi</p>

        <div className="si-igd-hero__headline">
          <div>
            <h2 className="si-igd-hero__value">IGD: {igd.toFixed(1)}</h2>
            <p className="si-igd-hero__exact">
              cálculo consolidado: {igdExact.toFixed(3)}
            </p>
          </div>

          <StatusBadge label={classification} variant="warning" />
        </div>

        <p className="si-igd-hero__description">{IGD_HERO_DESCRIPTION}</p>

        <div className="si-igd-hero__highlights">
          <div className="si-igd-hero__highlight">
            <span className="si-igd-hero__highlight-label">Melhor nota</span>
            <strong className="si-igd-hero__highlight-value">
              {strongestDepartment}
            </strong>
          </div>

          <div className="si-igd-hero__highlight">
            <span className="si-igd-hero__highlight-label">Maior atenção</span>
            <strong className="si-igd-hero__highlight-value">
              {watchDepartment}
            </strong>
          </div>

          <div className="si-igd-hero__highlight">
            <span className="si-igd-hero__highlight-label">Faixa atual</span>
            <strong className="si-igd-hero__highlight-value">
              {classification}
            </strong>
          </div>
        </div>
      </div>
    </section>
  );
}