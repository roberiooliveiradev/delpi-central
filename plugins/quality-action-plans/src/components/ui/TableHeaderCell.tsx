import { FieldLabel } from "@delpi/plugin-ui";

type TableHeaderCellProps = {
  label: string;
  hint?: string;
  className?: string;
  scope?: "col" | "row";
};

/** Cabeçalho de coluna com balão de ajuda (?), padrão das tabelas do plugin. */
export function TableHeaderCell({
  label,
  hint,
  className,
  scope = "col",
}: TableHeaderCellProps) {
  return (
    <th className={className} scope={scope}>
      {hint ? <FieldLabel label={label} hint={hint} className="pac-field__label-row" /> : label}
    </th>
  );
}
