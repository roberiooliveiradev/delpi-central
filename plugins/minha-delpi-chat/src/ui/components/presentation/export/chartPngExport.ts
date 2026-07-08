import { readMdcCssVar } from "../../../theme/mdcCssVars";
import { chatAlert } from "../../../utils/chatNativeDialogs";
import {
  exportSvgElementToPng,
  rasterizeSvgElement,
} from "@delpi/plugin-ui";

export function resolveChartExportTarget(root: HTMLElement | null): {
  container: HTMLElement;
  svg: SVGSVGElement;
  width: number;
  height: number;
} | null {
  if (!root) {
    return null;
  }

  const container = root.classList.contains("mdc-rich-chart__container")
    ? root
    : root.querySelector<HTMLElement>(".mdc-rich-chart__container");

  if (!container) {
    return null;
  }

  const svg =
    container.querySelector<SVGSVGElement>("svg.recharts-surface") ??
    container.querySelector<SVGSVGElement>("svg");

  if (!svg) {
    return null;
  }

  const bounds = container.getBoundingClientRect();
  const width = Math.max(1, Math.round(bounds.width) || 640);
  const height = Math.max(1, Math.round(bounds.height) || 280);

  return { container, svg, width, height };
}

function chartExportBackground(): string {
  return readMdcCssVar("--mdc-chart-export-bg", readMdcCssVar("--mdc-card-bg", "#ffffff"));
}

export function rasterizeChartElement(root: HTMLElement | null): Promise<string | null> {
  const target = resolveChartExportTarget(root);

  if (!target) {
    return Promise.resolve(null);
  }

  return rasterizeSvgElement(target.svg, {
    width: target.width,
    height: target.height,
    backgroundColor: chartExportBackground(),
  });
}

export function exportChartElementToPng(
  root: HTMLElement | null,
  title: string,
): void {
  const target = resolveChartExportTarget(root);

  if (!target) {
    chatAlert("Não encontrei o gráfico para exportar como PNG.");
    return;
  }

  exportSvgElementToPng(target.svg, {
    width: target.width,
    height: target.height,
    backgroundColor: chartExportBackground(),
    filename: title || "grafico",
    onError: () => {
      chatAlert("Não encontrei o gráfico para exportar como PNG.");
    },
  });
}
