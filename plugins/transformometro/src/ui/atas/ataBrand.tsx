import logoTransformaMaisUrl from "../../assets/logoTransformaMaisDelpi.svg";

/** Logo Transforma+ Delpi embutida no bundle do MFE (não depende de /public do remote). */
export function transformaMaisLogoSrc(): string {
  return logoTransformaMaisUrl;
}

/** Faixa de 4 cores da marca (mesmo padrão do header de inspeções-entrada). */
export function AtaBrandBar({ className = "" }: { className?: string }) {
  return (
    <div
      className={`tm-ata-brand-bar${className ? ` ${className}` : ""}`}
      aria-hidden="true"
    >
      <span />
      <span />
      <span />
      <span />
    </div>
  );
}
