import { useEffect, useState } from "react";

import { HostContainedDialog } from "./ui/Modal";
import type { ExportPdfScope } from "../utils/exportPlaylistPdf";

export type ExportPdfDialogGenerateOptions = {
  scope: ExportPdfScope;
  pixelRatio: 1 | 2;
};

type Props = {
  open: boolean;
  onClose: () => void;
  onGenerate: (options: ExportPdfDialogGenerateOptions) => Promise<void>;
  activeSlideCount: number;
  hasCurrentSlide: boolean;
  progressLabel?: string | null;
  busy?: boolean;
};

/** Diálogo de impressão/PDF — escopo programação ou slide atual. */
export function ExportPdfDialog({
  open,
  onClose,
  onGenerate,
  activeSlideCount,
  hasCurrentSlide,
  progressLabel = null,
  busy = false,
}: Props) {
  const [scope, setScope] = useState<ExportPdfScope>("playlist");
  const [pixelRatio, setPixelRatio] = useState<1 | 2>(2);

  useEffect(() => {
    if (!open) return;
    setScope(hasCurrentSlide ? "current" : "playlist");
    setPixelRatio(2);
  }, [open, hasCurrentSlide]);

  async function submit() {
    if (busy) return;
    if (scope === "current" && !hasCurrentSlide) return;
    if (scope === "playlist" && activeSlideCount <= 0) return;
    await onGenerate({ scope, pixelRatio });
  }

  return (
    <HostContainedDialog
      open={open}
      title="Exportar PDF"
      onClose={busy ? () => undefined : onClose}
      className="td-modal--export-pdf"
    >
      <div className="td-export-pdf-dialog">
        <fieldset className="td-export-pdf-dialog__fieldset" disabled={busy}>
          <legend className="td-export-pdf-dialog__legend">Escopo</legend>
          <label className="td-export-pdf-dialog__option">
            <input
              type="radio"
              name="td-export-pdf-scope"
              checked={scope === "playlist"}
              onChange={() => setScope("playlist")}
            />
            Programação ({activeSlideCount} tela{activeSlideCount === 1 ? "" : "s"} ativa
            {activeSlideCount === 1 ? "" : "s"})
          </label>
          <label className="td-export-pdf-dialog__option">
            <input
              type="radio"
              name="td-export-pdf-scope"
              checked={scope === "current"}
              disabled={!hasCurrentSlide}
              onChange={() => setScope("current")}
            />
            Slide atual
          </label>
        </fieldset>

        <fieldset className="td-export-pdf-dialog__fieldset" disabled={busy}>
          <legend className="td-export-pdf-dialog__legend">Qualidade</legend>
          <label className="td-export-pdf-dialog__option">
            <input
              type="radio"
              name="td-export-pdf-quality"
              checked={pixelRatio === 1}
              onChange={() => setPixelRatio(1)}
            />
            1× (mais rápido)
          </label>
          <label className="td-export-pdf-dialog__option">
            <input
              type="radio"
              name="td-export-pdf-quality"
              checked={pixelRatio === 2}
              onChange={() => setPixelRatio(2)}
            />
            2× (mais nítido)
          </label>
        </fieldset>

        {progressLabel ? (
          <p className="td-export-pdf-dialog__progress" role="status">
            {progressLabel}
          </p>
        ) : null}

        <div className="td-export-pdf-dialog__actions">
          <button
            type="button"
            className="td-btn td-btn--ghost"
            onClick={onClose}
            disabled={busy}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="td-btn"
            onClick={() => void submit()}
            disabled={
              busy ||
              (scope === "current" && !hasCurrentSlide) ||
              (scope === "playlist" && activeSlideCount <= 0)
            }
          >
            {busy ? "Gerando…" : "Gerar PDF"}
          </button>
        </div>
      </div>
    </HostContainedDialog>
  );
}
