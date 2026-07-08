import { exportSvgElementToPng } from "@delpi/plugin-ui";

export function exportImpactEffortMatrixPlotPng(
  container: HTMLElement | null | undefined,
  filename: string,
  onError?: () => void
): void {
  const svg = container?.querySelector("svg");
  if (!(svg instanceof SVGSVGElement)) {
    onError?.();
    return;
  }

  const rect = svg.getBoundingClientRect();
  exportSvgElementToPng(svg, {
    width: Math.max(Math.round(rect.width) || 640, 640),
    height: Math.max(Math.round(rect.height) || 480, 480),
    scale: 2,
    filename,
    onError,
  });
}
