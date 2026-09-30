import { useRef, useState } from "react";

import {
  ActionButton,
  AnchoredPanelPortal,
  ContextMenuItem,
} from "@delpi/plugin-ui/index";

import type { BpmnEditorAdapter } from "../editor/BpmnEditorAdapter";
import { exportWorkingCopy } from "../data/api/bpmnModelerApi";
import { BPMNM_ROOT_CLASS } from "../ui/kit";

type Props = {
  modelId: string;
  adapter: BpmnEditorAdapter | null;
  getAccessToken?: () => string | undefined;
};

function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Export menu (P4 §26): `.bpmn` = artefato canônico do backend (nunca
 * o XML do editor); SVG via renderer; PNG rasterizado client-side.
 */
export function ExportMenu({ modelId, adapter, getAccessToken }: Props) {
  const anchorRef = useRef<HTMLDivElement | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const exportBpmn = async () => {
    setBusy(true);
    try {
      const xml = await exportWorkingCopy(modelId, { getAccessToken });
      download("modelo.bpmn", xml, "application/xml");
    } finally {
      setBusy(false);
      setOpen(false);
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
      setOpen(false);
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
        const a = document.createElement("a");
        a.href = pngUrl;
        a.download = "modelo.png";
        a.click();
        URL.revokeObjectURL(pngUrl);
      }, "image/png");
    } finally {
      setBusy(false);
      setOpen(false);
    }
  };

  return (
    <div ref={anchorRef} className="bpmnm-export-menu">
      <ActionButton
        type="button"
        disabled={busy}
        aria-expanded={open}
        title="Exportar modelo"
        onClick={() => setOpen((v) => !v)}
      >
        Exportar
      </ActionButton>
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        className="delpi-ui-context-menu"
        variant="bare"
        role="menu"
        aria-label="Exportar modelo"
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={6}
        onDismiss={() => setOpen(false)}
        portalScopeClassName={BPMNM_ROOT_CLASS}
      >
        <ContextMenuItem label=".bpmn (canônico)" onSelect={() => void exportBpmn()} />
        <ContextMenuItem label="SVG" disabled={!adapter} onSelect={() => void exportSvg()} />
        <ContextMenuItem label="PNG" disabled={!adapter} onSelect={() => void exportPng()} />
      </AnchoredPanelPortal>
    </div>
  );
}
