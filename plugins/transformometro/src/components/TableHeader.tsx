import { HelpTooltip } from "@delpi/plugin-ui";

/** Cabeçalho de coluna em tabelas HTML nativas (fora do DataTable). */
export function TableHeader({ label, hint }: { label: string; hint?: string }) {
  return (
    <span className="ds-table__header-cell">
      {label}
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}
    </span>
  );
}
