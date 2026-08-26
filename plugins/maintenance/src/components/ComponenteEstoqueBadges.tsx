import { DM_HELP } from "../content/helpTooltips";

type ComponenteEstoqueBadgesProps = {
  estoqueLocal01: number;
  estoqueLocal99: number;
  /** Quais locais exibir (tabela usa uma coluna por local). */
  show?: "both" | "local01" | "local99";
  /** `compact` para células estreitas; `inline` (padrão) na árvore. */
  layout?: "inline" | "compact";
};

function formatStock(value: number): string {
  return value.toLocaleString("pt-BR");
}

function StockBadge({
  label,
  title,
  value,
  hideLabel = false,
}: {
  label: string;
  title: string;
  value: number;
  hideLabel?: boolean;
}) {
  const tone = value > 0 ? "positive" : "zero";

  return (
    <span
      className={[
        "dm-componente-stock-badge",
        tone === "positive"
          ? "dm-componente-stock-badge--positive"
          : "dm-componente-stock-badge--zero",
      ].join(" ")}
      title={title}
    >
      {hideLabel ? null : <span className="dm-componente-stock-badge__label">{label}</span>}
      <span className="dm-componente-stock-badge__value">{formatStock(value)}</span>
    </span>
  );
}

export function ComponenteEstoqueBadges({
  estoqueLocal01,
  estoqueLocal99,
  show = "both",
  layout = "inline",
}: ComponenteEstoqueBadgesProps) {
  const ariaLabel =
    show === "local01"
      ? `Estoque almoxarifado 01: ${formatStock(estoqueLocal01)}`
      : show === "local99"
        ? `Estoque fábrica 99: ${formatStock(estoqueLocal99)}`
        : `Estoque almoxarifado 01: ${formatStock(estoqueLocal01)}; fábrica 99: ${formatStock(estoqueLocal99)}`;

  return (
    <div
      className={[
        "dm-componente-stock-badges",
        layout === "compact" ? "dm-componente-stock-badges--compact" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label={ariaLabel}
    >
      {show === "both" || show === "local01" ? (
        <StockBadge label="01" title={DM_HELP.miniAplicadores.estoque01} value={estoqueLocal01} />
      ) : null}
      {show === "both" || show === "local99" ? (
        <StockBadge label="99" title={DM_HELP.miniAplicadores.estoque99} value={estoqueLocal99} />
      ) : null}
    </div>
  );
}

/** Valor tabular para coluna única da tabela (rótulo já está no header). */
export function ComponenteEstoqueCell({
  local,
  value,
}: {
  local: "01" | "99";
  value: number;
}) {
  const title =
    local === "01" ? DM_HELP.miniAplicadores.estoque01 : DM_HELP.miniAplicadores.estoque99;

  return (
    <StockBadge label={local} title={title} value={value} hideLabel />
  );
}
