import { useState } from "react";

import type { BpmnEditorAdapter } from "../editor/BpmnEditorAdapter";

function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadUrl(filename: string, url: string) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
}

export type ExportActions = {
  busy: boolean;
  exportBpmn: () => Promise<void>;
  exportSvg: () => Promise<void>;
  exportPng: () => Promise<void>;
};

/**
 * Export actions (P4 §26): `.bpmn` = artefato canônico do backend (nunca
 * o XML do editor); SVG via renderer; PNG rasterizado client-side.
 * Consumido pelo menu "Mais ações" do editor e pelo menu contextual da
 * biblioteca — nunca reimplementar download paralelo.
 */
export function useExportActions(
  adapter: BpmnEditorAdapter | null,
  /** Export server-side do artefato canônico — fornecido pelo DocumentHost. */
  exportBpmnXml: () => Promise<string>,
): ExportActions {
  const [busy, setBusy] = useState(false);

  const exportBpmn = async () => {
    setBusy(true);
    try {
      const xml = await exportBpmnXml();
      download("modelo.bpmn", xml, "application/xml");
    } finally {
      setBusy(false);
    }
  };

  const exportSvg = async () => {
    if (!adapter) return;
    setBusy(true);
    try {
      const svg = await adapter.exportSvg();
      download("modelo.svg", svg, "image/svg+xml");
    } finally {
      setBusy(false);
    }
  };

  const exportPng = async () => {
    if (!adapter) return;
    setBusy(true);
    try {
      const svg = await adapter.exportSvg();
      const image = new Image();
      const url = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" }));
      await new Promise<void>((resolve, reject) => {
        image.onload = () => resolve();
        image.onerror = () => reject(new Error("svg rasterization failed"));
        image.src = url;
      });
      const canvas = document.createElement("canvas");
      canvas.width = image.width || 1200;
      canvas.height = image.height || 800;
      canvas.getContext("2d")?.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const pngUrl = URL.createObjectURL(blob);
        downloadUrl("modelo.png", pngUrl);
        URL.revokeObjectURL(pngUrl);
      }, "image/png");
    } finally {
      setBusy(false);
    }
  };

  return { busy, exportBpmn, exportSvg, exportPng };
}
