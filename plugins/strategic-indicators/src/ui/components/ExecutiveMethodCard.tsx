type ExecutiveMethodCardProps = {
  igd: number;
  igdExact: number;
};

export function ExecutiveMethodCard({
  igd,
  igdExact,
}: ExecutiveMethodCardProps) {
  return (
    <section className="si-method-card">
      <div className="si-method-card__header">
        <h3 className="si-method-card__title">Como o IGD é formado</h3>
        <span className="si-method-card__subtitle">metodologia executiva</span>
      </div>

      <p className="si-method-card__text">
        O IGD consolida os IDDs departamentais em uma única nota de 0 a 10.
        Cada área participa com um peso oficial e a soma ponderada resulta no
        índice global do período.
      </p>

      <div className="si-method-card__formula">
        IGD = (FIN × 15%) + (RH × 15%) + (COM × 17%) + (PRO × 17%) + (QUA × 14%)
        + (SUP × 12%) + (ENG × 10%)
      </div>

      <div className="si-method-card__footer">
        <div className="si-method-card__pill">
          <span className="si-method-card__pill-label">Resultado exato</span>
          <strong className="si-method-card__pill-value">
            {igdExact.toFixed(3)}
          </strong>
        </div>

        <div className="si-method-card__pill">
          <span className="si-method-card__pill-label">Exibição no painel</span>
          <strong className="si-method-card__pill-value">
            {igd.toFixed(1)}
          </strong>
        </div>
      </div>
    </section>
  );
}