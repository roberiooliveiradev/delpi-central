import { DECK_COLOR_SURFACE, DECK_TABLE_DEFAULTS } from "@delpi/plugin-ui/index";
import {
  mergeChartPartsWithOptions,
  mergeComunicadoChartOptions,
  mergeTablePartsWithOptions,
  upsertChartPartState,
  upsertTablePartState,
  type ComunicadoChartViewBlock,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

/**
 * GLPI #1606: os gráficos têm DUAS superfícies independentes (chartArea e
 * plotArea). Alterar somente chartOptions.backgroundColor deixa o plot branco.
 * O patch usa as mesmas partes persistidas no editor, no preview e na TV.
 */
export function isChartBackgroundTransparent(block: ComunicadoChartViewBlock): boolean {
  const chartFill = block.chartParts?.chartArea?.style?.fill ?? block.chartOptions?.backgroundColor;
  const plotFill = block.chartParts?.plotArea?.style?.fill;
  return chartFill === "transparent" && plotFill === "transparent";
}

export function chartBackgroundTransparencyPatch(
  block: ComunicadoChartViewBlock,
  transparent: boolean,
) {
  const color = transparent ? "transparent" : DECK_COLOR_SURFACE;
  const chartOptions = mergeComunicadoChartOptions({
    ...block.chartOptions,
    backgroundColor: color,
  });
  // Projetar primeiro e fixar as duas pinturas por último. Outras partes
  // (séries, título, legenda, textos, eixos) são preservadas.
  const merged = mergeChartPartsWithOptions(block.chartParts, chartOptions);
  const chartArea = upsertChartPartState(merged, { kind: "chartArea" }, {
    style: { fill: color },
  });
  const chartParts = upsertChartPartState(chartArea, { kind: "plotArea" }, {
    style: { fill: color },
  });
  return { chartOptions, chartParts };
}

/**
 * A moldura da tabela é a autoridade de "sem fundo". O renderer aplica
 * a classe de fundo transparente a cabeçalho/células sem destruir as cores
 * previamente escolhidas, que voltam ao desativar a opção.
 */
export function isTableBackgroundTransparent(block: ComunicadoTableViewBlock): boolean {
  return block.tableParts?.frame?.style?.fill === "transparent";
}

export function tableBackgroundTransparencyPatch(
  block: ComunicadoTableViewBlock,
  transparent: boolean,
) {
  const merged = mergeTablePartsWithOptions(block.tableParts, block.tableOptions);
  const tableParts = upsertTablePartState(merged, { kind: "frame" }, {
    style: { fill: transparent ? "transparent" : DECK_TABLE_DEFAULTS.frameFill },
  });
  return { tableParts };
}
