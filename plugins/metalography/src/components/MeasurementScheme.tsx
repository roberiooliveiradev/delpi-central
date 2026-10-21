export function MeasurementScheme() {
  return (
    <figure className="mg-scheme" aria-label="Esquema das cotas CH, CB, AV, GH-E e GH-D">
      <svg viewBox="0 0 320 180" role="img">
        <title>Esquema das cinco medições da seção transversal</title>
        <rect x="90" y="48" width="140" height="84" rx="8" className="mg-scheme__body" />
        <path d="M70 90 H90 M230 90 H250" className="mg-scheme__dim" />
        <path d="M160 28 V48 M160 132 V152" className="mg-scheme__dim" />
        <text x="16" y="94">GH-E</text>
        <text x="258" y="94">GH-D</text>
        <text x="148" y="22">CH</text>
        <text x="168" y="168">CB</text>
        <text x="148" y="96">AV</text>
      </svg>
      <figcaption>Cotas da seção: altura, largura, vazios e rebarbas.</figcaption>
    </figure>
  );
}
