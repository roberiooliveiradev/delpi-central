import { formatInteger } from "../utils/format";
import { EmptyHint } from "./ui";

export type BarListTone = "accent" | "success" | "warning" | "danger" | "muted";

export type BarListBucket = {
  key: string;
  label: string;
  value: number;
};

type BarListProps = {
  buckets: BarListBucket[];
  toneOf?: (bucket: BarListBucket) => BarListTone;
};

/** Lista de barras horizontais para rankings do painel (domínio kaizen). */
export function BarList({ buckets, toneOf }: BarListProps) {
  const max = Math.max(1, ...buckets.map((bucket) => bucket.value));
  if (buckets.length === 0) {
    return <EmptyHint>Sem dados.</EmptyHint>;
  }

  return (
    <ul className="kz-barlist">
      {buckets.map((bucket) => (
        <li className="kz-barlist__row" key={bucket.key}>
          <span className="kz-barlist__label" title={bucket.label}>
            {bucket.label}
          </span>
          <span className="kz-barlist__track">
            <span
              className={`kz-barlist__fill kz-barlist__fill--${toneOf?.(bucket) ?? "accent"}`}
              style={{ width: `${Math.round((bucket.value / max) * 100)}%` }}
            />
          </span>
          <span className="kz-barlist__value">{formatInteger(bucket.value)}</span>
        </li>
      ))}
    </ul>
  );
}
