import { useEffect, useRef, useState } from "react";

import {
  createBlock,
  frameStyle,
  parseComunicadoConfig,
  serializeComunicadoConfig,
  type ComunicadoBlock,
  type ComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, uploadPlaylistMedia, type MediaAsset } from "../api/tvDashboardApi";

type Props = {
  playlistId: string;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  labels?: Record<string, string>;
};

export function ComunicadoComposer({ playlistId, value, onChange, labels = {} }: Props) {
  const [config, setConfig] = useState<ComunicadoConfig>(() => parseComunicadoConfig(value));
  const [selectedId, setSelectedId] = useState<string | null>(config.blocks?.[0]?.id ?? null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadTargetRef = useRef<"block" | "background">("block");

  useEffect(() => {
    setConfig(parseComunicadoConfig(value));
  }, [value]);

  const selected = useMemo(
    () => config.blocks?.find((block) => block.id === selectedId) ?? null,
    [config.blocks, selectedId],
  );

  function commit(next: ComunicadoConfig) {
    setConfig(next);
    onChange(serializeComunicadoConfig(next));
  }

  function updateBlocks(blocks: ComunicadoBlock[]) {
    commit({ ...config, blocks });
  }

  function addBlock(type: ComunicadoBlock["type"]) {
    const block = createBlock(type, type === "heading" ? "Novo título" : type === "text" ? "Texto" : "");
    const blocks = [...(config.blocks ?? []), block];
    setSelectedId(block.id);
    updateBlocks(blocks);
  }

  function updateSelected(patch: Partial<ComunicadoBlock>) {
    if (!selected) return;
    const blocks = (config.blocks ?? []).map((block) =>
      block.id === selected.id ? ({ ...block, ...patch } as ComunicadoBlock) : block,
    );
    updateBlocks(blocks);
  }

  function removeSelected() {
    if (!selected) return;
    const blocks = (config.blocks ?? []).filter((block) => block.id !== selected.id);
    setSelectedId(blocks[0]?.id ?? null);
    updateBlocks(blocks);
  }

  async function handleUpload(file: File, target: "block" | "background") {
    setUploading(true);
    try {
      const asset: MediaAsset = await uploadPlaylistMedia(playlistId, file);
      const url = adminMediaUrl(playlistId, asset.id);
      if (target === "background") {
        commit({
          ...config,
          background: { type: "image", assetId: asset.id, url },
        });
        return;
      }
      if (!selected || (selected.type !== "image" && selected.type !== "video")) return;
      const blocks = (config.blocks ?? []).map((block) =>
        block.id === selected.id
          ? ({ ...block, assetId: asset.id, url } as ComunicadoBlock)
          : block,
      );
      updateBlocks(blocks);
    } finally {
      setUploading(false);
    }
  }

  function triggerUpload(target: "block" | "background") {
    uploadTargetRef.current = target;
    fileInputRef.current?.click();
  }

  const background = config.background ?? { type: "color", value: "#0f172a" };
  const bgPreviewStyle =
    background.type === "image" && (background.url || background.value)
      ? {
          backgroundImage: `url(${background.url ?? background.value})`,
          backgroundSize: "cover" as const,
          backgroundPosition: "center" as const,
        }
      : {
          backgroundColor: background.type === "color" ? background.value : "#0f172a",
        };

  return (
    <div className="td-composer">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = "";
          if (file) void handleUpload(file, uploadTargetRef.current);
        }}
      />

      <div className="td-composer__toolbar">
        <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("heading")}>
          {labels.comunicadoAddHeading ?? "Título"}
        </button>
        <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("text")}>
          {labels.comunicadoAddText ?? "Texto"}
        </button>
        <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("image")}>
          {labels.comunicadoAddImage ?? "Imagem"}
        </button>
        <button type="button" className="td-btn td-btn--sm" onClick={() => addBlock("video")}>
          {labels.comunicadoAddVideo ?? "Vídeo"}
        </button>
      </div>

      <div className="td-composer__layout">
        <div className="td-composer__canvas-wrap">
          <div className="td-composer__canvas" style={bgPreviewStyle}>
            {(config.blocks ?? []).map((block) => {
              const isSelected = block.id === selectedId;
              const style = {
                ...frameStyle(block.frame),
                ...(block.style?.fontSize ? { fontSize: `${Math.max(10, block.style.fontSize * 0.35)}px` } : {}),
                ...(block.style?.color ? { color: block.style.color } : {}),
                ...(block.style?.textAlign ? { textAlign: block.style.textAlign } : {}),
              };
              return (
                <button
                  key={block.id}
                  type="button"
                  className={`td-composer__block${isSelected ? " td-composer__block--selected" : ""}`}
                  style={style}
                  onClick={() => setSelectedId(block.id)}
                >
                  {block.type === "heading" ? (
                    <strong>{block.content || "Título"}</strong>
                  ) : block.type === "text" ? (
                    <span>{block.content || "Texto"}</span>
                  ) : block.type === "image" ? (
                    block.url ? (
                      <img src={block.url} alt="" />
                    ) : (
                      <span className="td-composer__placeholder">Imagem</span>
                    )
                  ) : block.url ? (
                    <video src={block.url} muted playsInline />
                  ) : (
                    <span className="td-composer__placeholder">Vídeo</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <aside className="td-composer__panel">
          <h4>{labels.comunicadoBackground ?? "Fundo"}</h4>
          <div className="td-field">
            <label htmlFor="td-bg-color">Cor</label>
            <input
              id="td-bg-color"
              type="color"
              value={background.type === "color" ? background.value : "#0f172a"}
              onChange={(e) =>
                commit({ ...config, background: { type: "color", value: e.target.value } })
              }
            />
          </div>
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={uploading}
            onClick={() => triggerUpload("background")}
          >
            {labels.comunicadoUpload ?? "Enviar arquivo"} (fundo)
          </button>

          <h4>{labels.comunicadoBlocks ?? "Elementos"}</h4>
          {!selected ? (
            <p className="td-subtitle">Selecione um elemento no slide.</p>
          ) : (
            <>
              <p className="td-subtitle">Tipo: {selected.type}</p>
              {(selected.type === "heading" || selected.type === "text") && (
                <div className="td-field">
                  <label htmlFor="td-block-content">Conteúdo</label>
                  <textarea
                    id="td-block-content"
                    rows={3}
                    value={selected.content}
                    onChange={(e) => updateSelected({ content: e.target.value } as Partial<ComunicadoBlock>)}
                  />
                </div>
              )}
              {(selected.type === "image" || selected.type === "video") && (
                <button
                  type="button"
                  className="td-btn td-btn--sm"
                  disabled={uploading}
                  onClick={() => triggerUpload("block")}
                >
                  {uploading ? "Enviando…" : labels.comunicadoUpload ?? "Enviar arquivo"}
                </button>
              )}
              <div className="td-composer__grid">
                {(["x", "y", "w", "h"] as const).map((key) => (
                  <div className="td-field" key={key}>
                    <label htmlFor={`td-frame-${key}`}>{key.toUpperCase()} %</label>
                    <input
                      id={`td-frame-${key}`}
                      type="number"
                      min={0}
                      max={100}
                      value={selected.frame[key]}
                      onChange={(e) =>
                        updateSelected({
                          frame: { ...selected.frame, [key]: Number(e.target.value) },
                        } as Partial<ComunicadoBlock>)
                      }
                    />
                  </div>
                ))}
              </div>
              {(selected.type === "heading" || selected.type === "text") && (
                <>
                  <div className="td-field">
                    <label htmlFor="td-font-size">Tamanho</label>
                    <input
                      id="td-font-size"
                      type="number"
                      min={12}
                      max={120}
                      value={selected.style?.fontSize ?? 32}
                      onChange={(e) =>
                        updateSelected({
                          style: { ...selected.style, fontSize: Number(e.target.value) },
                        } as Partial<ComunicadoBlock>)
                      }
                    />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-font-color">Cor do texto</label>
                    <input
                      id="td-font-color"
                      type="color"
                      value={selected.style?.color ?? "#ffffff"}
                      onChange={(e) =>
                        updateSelected({
                          style: { ...selected.style, color: e.target.value },
                        } as Partial<ComunicadoBlock>)
                      }
                    />
                  </div>
                </>
              )}
              <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={removeSelected}>
                Remover elemento
              </button>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
