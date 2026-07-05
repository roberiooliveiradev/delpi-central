import { useEffect, useState } from "react";

import type { BranchScope, NativeScreenCatalogItem, Slide } from "../api/tvDashboardApi";
import { BranchField } from "./BranchField";

type Props = {
  open: boolean;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  defaultDurationSec: number;
  onClose: () => void;
  onSave: (payload: {
    title: string;
    durationSec: number;
    nativeConfig?: Record<string, unknown>;
    externalUrl?: string;
  }) => void;
};

export function EditSlideModal({
  open,
  slide,
  catalog,
  branchScope,
  defaultDurationSec,
  onClose,
  onSave,
}: Props) {
  const [title, setTitle] = useState("");
  const [durationSec, setDurationSec] = useState(defaultDurationSec);
  const [externalUrl, setExternalUrl] = useState("");
  const [headline, setHeadline] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [branch, setBranch] = useState("");
  const [periodDays, setPeriodDays] = useState(30);

  useEffect(() => {
    if (!slide || !open) return;
    setTitle(slide.title);
    setDurationSec(slide.durationSec ?? defaultDurationSec);
    setExternalUrl(slide.externalUrl ?? "");
    const cfg = slide.nativeConfig ?? {};
    setHeadline(String(cfg.headline ?? "Comunicado"));
    setSubtitle(String(cfg.subtitle ?? ""));
    setBranch(String(cfg.branch ?? ""));
    setPeriodDays(Number(cfg.periodDays ?? 30));
  }, [slide, open, defaultDurationSec]);

  if (!open || !slide) return null;

  const screenKey = slide.nativeScreenKey ?? "";
  const catalogItem = catalog.find((item) => item.key === screenKey);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (slide.slideType === "external") {
      if (!externalUrl.trim()) return;
      onSave({ title: title.trim() || slide.title, durationSec, externalUrl: externalUrl.trim() });
      onClose();
      return;
    }
    const nativeConfig: Record<string, unknown> = {};
    if (screenKey === "custom_message") {
      nativeConfig.headline = headline;
      nativeConfig.subtitle = subtitle;
    } else {
      if (branch.trim()) nativeConfig.branch = branch.trim();
      nativeConfig.periodDays = periodDays;
      if (screenKey === "quality_ppm_summary") {
        nativeConfig.ppmType = slide.nativeConfig?.ppmType ?? "internal";
      }
    }
    onSave({
      title: title.trim() || slide.title,
      durationSec,
      nativeConfig,
    });
    onClose();
  }

  return (
    <div className="td-modal-backdrop" role="presentation" onClick={onClose}>
      <div className="td-modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3>Editar tela</h3>
        <form onSubmit={handleSubmit}>
          <div className="td-field">
            <label htmlFor="td-edit-title">Título</label>
            <input id="td-edit-title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          {slide.slideType === "external" ? (
            <div className="td-field">
              <label htmlFor="td-edit-url">URL (https://)</label>
              <input id="td-edit-url" value={externalUrl} onChange={(e) => setExternalUrl(e.target.value)} required />
            </div>
          ) : screenKey === "custom_message" ? (
            <>
              <div className="td-field">
                <label htmlFor="td-edit-headline">Comunicado</label>
                <input id="td-edit-headline" value={headline} onChange={(e) => setHeadline(e.target.value)} />
              </div>
              <div className="td-field">
                <label htmlFor="td-edit-subtitle">Subtítulo</label>
                <input id="td-edit-subtitle" value={subtitle} onChange={(e) => setSubtitle(e.target.value)} />
              </div>
            </>
          ) : screenKey !== "supplies_stock_value" ? (
            <>
              <BranchField
                id="td-edit-branch"
                label="Filial (opcional)"
                scope={branchScope}
                value={branch}
                onChange={setBranch}
              />
              <div className="td-field">
                <label htmlFor="td-edit-period">Período (dias)</label>
                <input
                  id="td-edit-period"
                  type="number"
                  min={1}
                  max={365}
                  value={periodDays}
                  onChange={(e) => setPeriodDays(Number(e.target.value))}
                />
              </div>
            </>
          ) : (
            <BranchField
              id="td-edit-branch-stock"
              label="Filial (opcional)"
              scope={branchScope}
              value={branch}
              onChange={setBranch}
            />
          )}
          {catalogItem ? (
            <p className="td-subtitle" style={{ marginTop: 0 }}>
              Tela nativa: {catalogItem.label}
            </p>
          ) : null}
          <div className="td-field">
            <label htmlFor="td-edit-duration">Duração (s)</label>
            <input
              id="td-edit-duration"
              type="number"
              min={5}
              max={600}
              value={durationSec}
              onChange={(e) => setDurationSec(Number(e.target.value))}
            />
          </div>
          <div className="td-modal-actions">
            <button type="button" className="td-btn" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="td-btn td-btn--primary">
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
