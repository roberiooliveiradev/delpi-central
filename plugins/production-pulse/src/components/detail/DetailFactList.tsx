import type { ReactNode } from "react";

export type DetailFact = {
  label: string;
  value: ReactNode;
};

type DetailFactListProps = {
  facts: DetailFact[];
};

/** Lista leve label/valor — alternativa a paredes densas de dl. */
export function DetailFactList({ facts }: DetailFactListProps) {
  if (facts.length === 0) return null;
  return (
    <dl className="pp-detail-dl pp-detail-dl--facts">
      {facts.map((fact) => (
        <div key={fact.label}>
          <dt>{fact.label}</dt>
          <dd>{fact.value}</dd>
        </div>
      ))}
    </dl>
  );
}
