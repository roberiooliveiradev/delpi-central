import { useState } from "react";

import type { NativeScreenCatalogItem } from "../api/tvDashboardApi";

type Props = {
  open: boolean;
  catalog: NativeScreenCatalogItem[];
  onClose: () => void;
  onAddNative: (payload: {
    screenKey: string;
    title: string;
    nativeConfig: Record<string, unknown>;
    durationSec: number;
  }) => void;
  onAddExternal: (payload: { title: string; externalUrl: string; durationSec: number }) => void;
};

export function AddSlideModal({ open, catalog, onClose, onAddNative, onAddExternal }: Props) {
  const [mode, setMode] = useState<"native" | "external">("native");
  const [screenKey, setScreenKey] = useState("");
  const [title, setTitle] = useState("");
  const [durationSec, setDurationSec] = useState(30);
  const [externalUrl, setExternalUrl] = useState("");
  const [headline, setHeadline] = useState("Comunicado");
  const [subtitle, setSubtitle] = useState("");
  const [branch, setBranch] = useState("");
  const [periodDays, setPeriodDays] = useState(30);

  if (!open) return null;

  const selected = catalog.find((item) => item.key === screenKey) ?? catalog[0];

  function resetNativeDefaults(item: NativeScreenCatalogItem) {
    setScreenKey(item.key);
    setTitle(item.label);
    setDurationSec(item.defaultDurationSec);
    if (item.key === "custom_message") {
      setHeadline("Comunicado");
      setSubtitle("");
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (mode === "external") {
      if (!externalUrl.trim()) return;
      onAddExternal({ title: title.trim() || "Link externo", externalUrl: externalUrl.trim(), durationSec });
      onClose();
      return;
    }
    const item = selected;
    if (!item) return;
    const nativeConfig: Record<string, unknown> = {};
    if (item.key === "custom_message") {
      nativeConfig.headline = headline;
      nativeConfig.subtitle = subtitle;
    } else {
      if (branch.trim()) nativeConfig.branch = branch.trim();
      nativeConfig.periodDays = periodDays;
      if (item.key === "quality_ppm_summary") nativeConfig.ppmType = "internal";
    }
    onAddNative({
      screenKey: item.key,
      title: title.trim() || item.label,
      nativeConfig,
      durationSec,
    });
    onClose();
  }

  return (
    <div className="td-modal-backdrop" role="presentation" onClick={onClose}>
      <div className="td-modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3>Adicionar tela</h3>
        <div className="td-modal-tabs">
          <button type="button" className={mode === "native" ? "td-tab td-tab--active" : "td-tab"} onClick={() => setMode("native")}>
            Nativa DELPI
          </button>
          <button type="button" className={mode === "external" ? "td-tab td-tab--active" : "td-tab"} onClick={() => setMode("external")}>
            Link externo
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          {mode === "native" ? (
            <>
              <div className="td-field">
                <label htmlFor="td-screen-key">Tela nativa</label>
                <select
                  id="td-screen-key"
                  value={screenKey || catalog[0]?.key || ""}
                  onChange={(e) => resetNativeDefaults(catalog.find((c) => c.key === e.target.value) ?? catalog[0])}
                >
                  {catalog.map((item) => (
                    <option key={item.key} value={item.key}>{item.label}</option>
                  ))}
                </select>
              </div>
              <div className="td-field">
                <label htmlFor="td-slide-title">Título</label>
                <input id="td-slide-title" value={title || selected?.label || ""} onChange={(e) => setTitle(e.target.value)} />
              </div>
              {selected?.key === "custom_message" ? (
                <>
                  <div className="td-field">
                    <label htmlFor="td-headline">Comunicado</label>
                    <input id="td-headline" value={headline} onChange={(e) => setHeadline(e.target.value)} />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-subtitle">Subtítulo</label>
                    <input id="td-subtitle" value={subtitle} onChange={(e) => setSubtitle(e.target.value)} />
                  </div>
                </>
              ) : selected?.key !== "supplies_stock_value" ? (
                <>
                  <div className="td-field">
                    <label htmlFor="td-branch">Filial (opcional)</label>
                    <input id="td-branch" value={branch} onChange={(e) => setBranch(e.target.value)} placeholder="Ex.: 01" />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-period">Período (dias)</label>
                    <input id="td-period" type="number" min={1} max={365} value={periodDays} onChange={(e) => setPeriodDays(Number(e.target.value))} />
                  </div>
                </>
              ) : (
                <div className="td-field">
                  <label htmlFor="td-branch-stock">Filial (opcional)</label>
                  <input id="td-branch-stock" value={branch} onChange={(e) => setBranch(e.target.value)} />
                </div>
              )}
            </>
          ) : (
            <>
              <div className="td-field">
                <label htmlFor="td-ext-title">Título</label>
                <input id="td-ext-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Power BI, site..." />
              </div>
              <div className="td-field">
                <label htmlFor="td-ext-url">URL (https://)</label>
                <input id="td-ext-url" value={externalUrl} onChange={(e) => setExternalUrl(e.target.value)} placeholder="https://..." required />
              </div>
            </>
          )}
          <div className="td-field">
            <label htmlFor="td-slide-duration">Duração (s)</label>
            <input id="td-slide-duration" type="number" min={5} max={600} value={durationSec} onChange={(e) => setDurationSec(Number(e.target.value))} />
          </div>
          <div className="td-modal-actions">
            <button type="button" className="td-btn" onClick={onClose}>Cancelar</button>
            <button type="submit" className="td-btn td-btn--primary">Adicionar</button>
          </div>
        </form>
      </div>
    </div>
  );
}
