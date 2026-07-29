import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";

import {
  applyPlaylistDeckImport,
  previewPlaylistDeckImport,
  type DeckImportPreview,
} from "../api/tvDashboardApi";
import { HostContainedDialog } from "./ui/Modal";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

type Props = {
  open: boolean;
  onClose: () => void;
  onImported: (playlistId: string) => void;
};

export function DeckImportModal({ open, onClose, onImported }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<DeckImportPreview | null>(null);
  const [nameOverride, setNameOverride] = useState("");
  const [bindingPolicy, setBindingPolicy] = useState<"lenient" | "strict">("lenient");

  const reset = useCallback(() => {
    setPreview(null);
    setNameOverride("");
    setBindingPolicy("lenient");
    setBusy(false);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const handleClose = useCallback(() => {
    reset();
    onClose();
  }, [onClose, reset]);

  const handleFile = useCallback(async (file: File | null) => {
    if (!file) return;
    setBusy(true);
    setPreview(null);
    try {
      const report = await previewPlaylistDeckImport(file);
      setPreview(report);
      setNameOverride(report.playlistName || "");
      if (!report.valid) {
        tvDashboardNotice(report.errors[0] || "Pacote inválido.");
      }
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao ler o pacote.");
    } finally {
      setBusy(false);
    }
  }, []);

  const handleApply = useCallback(async () => {
    const token = preview?.importToken;
    if (!token || !preview?.valid) return;
    setBusy(true);
    try {
      const playlist = await applyPlaylistDeckImport({
        importToken: token,
        nameOverride: nameOverride.trim() || undefined,
        activateAfterImport: false,
        bindingPolicy,
      });
      tvDashboardNotice("Programação importada.");
      reset();
      onClose();
      onImported(playlist.id);
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao importar pacote.");
    } finally {
      setBusy(false);
    }
  }, [bindingPolicy, nameOverride, onClose, onImported, preview, reset]);

  const warnings = preview?.warnings ?? [];
  const canApply = Boolean(preview?.valid && preview.importToken);

  return (
    <HostContainedDialog
      open={open}
      onClose={handleClose}
      title="Importar pacote"
      className="td-modal--deck-import"
      footer={
        <div className="td-modal-actions td-modal-actions--end">
          <button type="button" className="td-btn td-btn--ghost" disabled={busy} onClick={handleClose}>
            Cancelar
          </button>
          <button
            type="button"
            className="td-btn td-btn--primary"
            disabled={busy || !canApply}
            onClick={() => void handleApply()}
          >
            {busy ? "Processando…" : "Importar"}
          </button>
        </div>
      }
    >
      <div className="td-deck-import">
        <p className="td-deck-import__hint">
          Selecione um arquivo <code>.delpi-tv-deck</code> exportado de outra conta ou
          programação. O preview valida mídias, checksums e fontes de dados.
        </p>

        <div className="td-deck-import__upload">
          <input
            ref={inputRef}
            type="file"
            accept=".delpi-tv-deck,application/zip,.zip"
            disabled={busy}
            className="td-sr-only"
            onChange={(event) => {
              const file = event.target.files?.[0] ?? null;
              void handleFile(file);
            }}
          />
          <button
            type="button"
            className="td-btn td-btn--secondary"
            disabled={busy}
            onClick={() => inputRef.current?.click()}
          >
            <Upload size={16} aria-hidden="true" />
            Escolher arquivo
          </button>
        </div>

        {preview ? (
          <div className="td-deck-import__report">
            <dl className="td-deck-import__stats">
              <div>
                <dt>Nome</dt>
                <dd>{preview.playlistName || "—"}</dd>
              </div>
              <div>
                <dt>Telas</dt>
                <dd>{preview.stats?.slideCount ?? 0}</dd>
              </div>
              <div>
                <dt>Seções</dt>
                <dd>{preview.stats?.sectionCount ?? 0}</dd>
              </div>
              <div>
                <dt>Mídias</dt>
                <dd>{preview.stats?.mediaCount ?? 0}</dd>
              </div>
              <div>
                <dt>Bindings</dt>
                <dd>{preview.stats?.bindingCount ?? 0}</dd>
              </div>
            </dl>

            {preview.errors.length > 0 ? (
              <ul className="td-deck-import__errors" aria-label="Erros">
                {preview.errors.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}

            {warnings.length > 0 ? (
              <ul className="td-deck-import__warnings" aria-label="Avisos">
                {warnings.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}

            {canApply ? (
              <>
                <label className="td-deck-import__field">
                  <span>Nome da programação</span>
                  <input
                    type="text"
                    value={nameOverride}
                    maxLength={200}
                    disabled={busy}
                    onChange={(event) => setNameOverride(event.target.value)}
                  />
                </label>
                <label className="td-deck-import__field">
                  <span>Política de bindings</span>
                  <select
                    value={bindingPolicy}
                    disabled={busy}
                    onChange={(event) =>
                      setBindingPolicy(event.target.value as "lenient" | "strict")
                    }
                  >
                    <option value="lenient">Permissiva (importa com avisos)</option>
                    <option value="strict">Rígida (bloqueia se houver avisos)</option>
                  </select>
                </label>
              </>
            ) : null}
          </div>
        ) : null}
      </div>
    </HostContainedDialog>
  );
}
