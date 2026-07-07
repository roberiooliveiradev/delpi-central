import { useEffect, useMemo, useRef, useState } from "react";

import {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_SHAPE_KINDS,
  ComunicadoBlockView,
  createBlock,
  createShapeBlock,
  frameStyle,
  nextZIndex,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, uploadPlaylistMedia, type MediaAsset } from "../api/tvDashboardApi";
import { enrichComunicadoConfigForEditor } from "./slideCardPreview";
import { useCanvasBlockInteraction } from "./useCanvasBlockInteraction";

type Props = {
  playlistId: string;
  value: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
  labels?: Record<string, string>;
};

const FONT_SCALE = 0.35;

export function ComunicadoComposer({ playlistId, value, onChange, labels = {} }: Props) {
  const [config, setConfig] = useState<ComunicadoConfig>(() =>
    enrichComunicadoConfigForEditor(value, playlistId),
  );
  const [selectedId, setSelectedId] = useState<string | null>(config.blocks?.[0]?.id ?? null);
  const [uploading, setUploading] = useState(false);
  const [shapeMenuOpen, setShapeMenuOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadTargetRef = useRef<"block" | "background">("block");

  useEffect(() => {
    setConfig(enrichComunicadoConfigForEditor(value, playlistId));
  }, [value, playlistId]);

  const blocks = useMemo(() => sortBlocksByZIndex(config.blocks ?? []), [config.blocks]);

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

  const handleUpdateFrame = (blockId: string, frame: ComunicadoBlock["frame"]) => {
    const nextBlocks = (config.blocks ?? []).map((block) =>
      block.id === blockId ? { ...block, frame } : block,
    );
    updateBlocks(nextBlocks);
  };

  const { canvasRef, startDrag } = useCanvasBlockInteraction({ onUpdateFrame: handleUpdateFrame });

  function addBlock(type: ComunicadoBlock["type"]) {
    const block = createBlock(
      type,
      type === "heading" ? "Novo título" : type === "text" ? "Texto" : "",
    );
    block.style = { ...block.style, zIndex: nextZIndex(config.blocks ?? []) };
    const nextBlocks = [...(config.blocks ?? []), block];
    setSelectedId(block.id);
    updateBlocks(nextBlocks);
  }

  function addShape(shape: ComunicadoShapeKind) {
    const block = createShapeBlock(shape);
    block.style = { ...block.style, zIndex: nextZIndex(config.blocks ?? []) };
    const nextBlocks = [...(config.blocks ?? []), block];
    setSelectedId(block.id);
    setShapeMenuOpen(false);
    updateBlocks(nextBlocks);
  }

  function updateSelected(patch: Partial<ComunicadoBlock>) {
    if (!selected) return;
    const nextBlocks = (config.blocks ?? []).map((block) =>
      block.id === selected.id ? ({ ...block, ...patch } as ComunicadoBlock) : block,
    );
    updateBlocks(nextBlocks);
  }

  function updateSelectedStyle(patch: NonNullable<ComunicadoBlock["style"]>) {
    if (!selected) return;
    updateSelected({ style: { ...selected.style, ...patch } } as Partial<ComunicadoBlock>);
  }

  function removeSelected() {
    if (!selected) return;
    const nextBlocks = (config.blocks ?? []).filter((block) => block.id !== selected.id);
    setSelectedId(nextBlocks[0]?.id ?? null);
    updateBlocks(nextBlocks);
  }

  function moveLayer(direction: "up" | "down") {
    if (!selected) return;
    const currentZ = selected.style?.zIndex ?? 1;
    const delta = direction === "up" ? 1 : -1;
    updateSelectedStyle({ zIndex: Math.max(1, currentZ + delta) });
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
      const nextBlocks = (config.blocks ?? []).map((block) =>
        block.id === selected.id
          ? ({ ...block, assetId: asset.id, url } as ComunicadoBlock)
          : block,
      );
      updateBlocks(nextBlocks);
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

  const isTextBlock = selected?.type === "heading" || selected?.type === "text";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isShapeBlock = selected?.type === "shape";

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
        <div className="td-composer__toolbar-group">
          <span className="td-composer__toolbar-label">Inserir</span>
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
          <div className="td-composer__dropdown">
            <button
              type="button"
              className="td-btn td-btn--sm"
              onClick={() => setShapeMenuOpen((open) => !open)}
            >
              {labels.comunicadoAddShape ?? "Forma"}
            </button>
            {shapeMenuOpen ? (
              <div className="td-composer__dropdown-menu" role="menu">
                {COMUNICADO_SHAPE_KINDS.map((item) => (
                  <button
                    key={item.kind}
                    type="button"
                    role="menuitem"
                    className="td-composer__dropdown-item"
                    onClick={() => addShape(item.kind)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="td-composer__layout">
        <div className="td-composer__canvas-wrap">
          <div ref={canvasRef} className="td-composer__canvas" style={bgPreviewStyle}>
            {blocks.map((block) => {
              const isSelected = block.id === selectedId;
              return (
                <div
                  key={block.id}
                  className={`td-composer__block-wrap${isSelected ? " td-composer__block-wrap--selected" : ""}`}
                  style={frameStyle(block.frame)}
                  onPointerDown={(event) => {
                    setSelectedId(block.id);
                    startDrag(event, block, "move");
                  }}
                >
                  <ComunicadoBlockView
                    block={block}
                    fontScale={FONT_SCALE}
                    interactive
                    embedded
                    className={isSelected ? "td-composer__block--selected" : ""}
                  />
                  {isSelected ? (
                    <>
                      <button
                        type="button"
                        className="td-composer__resize td-composer__resize--se"
                        aria-label="Redimensionar"
                        onPointerDown={(event) => startDrag(event, block, "resize-se")}
                      />
                      <button
                        type="button"
                        className="td-composer__resize td-composer__resize--e"
                        aria-label="Redimensionar largura"
                        onPointerDown={(event) => startDrag(event, block, "resize-e")}
                      />
                      <button
                        type="button"
                        className="td-composer__resize td-composer__resize--s"
                        aria-label="Redimensionar altura"
                        onPointerDown={(event) => startDrag(event, block, "resize-s")}
                      />
                    </>
                  ) : null}
                </div>
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
            <p className="td-subtitle">Selecione um elemento no slide ou arraste para posicionar.</p>
          ) : (
            <>
              <p className="td-subtitle">Tipo: {selected.type}</p>

              {isTextBlock && (
                <>
                  <div className="td-field">
                    <label htmlFor="td-block-content">Conteúdo</label>
                    <textarea
                      id="td-block-content"
                      rows={3}
                      value={selected.content}
                      onChange={(e) => updateSelected({ content: e.target.value } as Partial<ComunicadoBlock>)}
                    />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-block-link">Link (URL)</label>
                    <input
                      id="td-block-link"
                      type="url"
                      placeholder="https://..."
                      value={selected.href ?? ""}
                      onChange={(e) =>
                        updateSelected({
                          href: e.target.value.trim() || undefined,
                          linkTarget: "_blank",
                        } as Partial<ComunicadoBlock>)
                      }
                    />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-font-family">Fonte</label>
                    <select
                      id="td-font-family"
                      value={selected.style?.fontFamily ?? COMUNICADO_FONT_FAMILIES[0]}
                      onChange={(e) => updateSelectedStyle({ fontFamily: e.target.value })}
                    >
                      {COMUNICADO_FONT_FAMILIES.map((font) => (
                        <option key={font} value={font}>
                          {font.split(",")[0]}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="td-composer__format-row">
                    <button
                      type="button"
                      className={`td-btn td-btn--sm${selected.style?.fontWeight === "bold" ? " td-btn--active" : ""}`}
                      onClick={() =>
                        updateSelectedStyle({
                          fontWeight: selected.style?.fontWeight === "bold" ? "normal" : "bold",
                        })
                      }
                    >
                      N
                    </button>
                    <button
                      type="button"
                      className={`td-btn td-btn--sm${selected.style?.fontStyle === "italic" ? " td-btn--active" : ""}`}
                      onClick={() =>
                        updateSelectedStyle({
                          fontStyle: selected.style?.fontStyle === "italic" ? "normal" : "italic",
                        })
                      }
                    >
                      I
                    </button>
                    <button
                      type="button"
                      className={`td-btn td-btn--sm${selected.style?.textDecoration === "underline" ? " td-btn--active" : ""}`}
                      onClick={() =>
                        updateSelectedStyle({
                          textDecoration:
                            selected.style?.textDecoration === "underline" ? "none" : "underline",
                        })
                      }
                    >
                      S
                    </button>
                    {(["left", "center", "right"] as const).map((align) => (
                      <button
                        key={align}
                        type="button"
                        className={`td-btn td-btn--sm${selected.style?.textAlign === align ? " td-btn--active" : ""}`}
                        onClick={() => updateSelectedStyle({ textAlign: align })}
                      >
                        {align === "left" ? "Esq" : align === "center" ? "C" : "Dir"}
                      </button>
                    ))}
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-font-size">Tamanho</label>
                    <input
                      id="td-font-size"
                      type="number"
                      min={12}
                      max={120}
                      value={selected.style?.fontSize ?? 32}
                      onChange={(e) => updateSelectedStyle({ fontSize: Number(e.target.value) })}
                    />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-font-color">Cor do texto</label>
                    <input
                      id="td-font-color"
                      type="color"
                      value={selected.style?.color ?? "#ffffff"}
                      onChange={(e) => updateSelectedStyle({ color: e.target.value })}
                    />
                  </div>
                </>
              )}

              {isShapeBlock && (
                <>
                  <div className="td-field">
                    <label htmlFor="td-shape-content">Texto na forma</label>
                    <input
                      id="td-shape-content"
                      type="text"
                      value={selected.content ?? ""}
                      onChange={(e) => updateSelected({ content: e.target.value } as Partial<ComunicadoBlock>)}
                    />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-shape-fill">Preenchimento</label>
                    <input
                      id="td-shape-fill"
                      type="color"
                      value={selected.style?.fill ?? "#089bdb"}
                      onChange={(e) => updateSelectedStyle({ fill: e.target.value })}
                    />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-shape-stroke">Contorno</label>
                    <input
                      id="td-shape-stroke"
                      type="color"
                      value={selected.style?.stroke ?? "#ffffff"}
                      onChange={(e) => updateSelectedStyle({ stroke: e.target.value })}
                    />
                  </div>
                  <div className="td-field">
                    <label htmlFor="td-shape-stroke-width">Espessura</label>
                    <input
                      id="td-shape-stroke-width"
                      type="number"
                      min={0}
                      max={20}
                      value={selected.style?.strokeWidth ?? 2}
                      onChange={(e) => updateSelectedStyle({ strokeWidth: Number(e.target.value) })}
                    />
                  </div>
                </>
              )}

              {isMediaBlock && (
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

              <div className="td-composer__format-row">
                <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("up")}>
                  Trazer frente
                </button>
                <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("down")}>
                  Enviar fundo
                </button>
              </div>

              <div className="td-field">
                <label htmlFor="td-rotation">Rotação (°)</label>
                <input
                  id="td-rotation"
                  type="number"
                  min={-180}
                  max={180}
                  value={selected.style?.rotation ?? 0}
                  onChange={(e) => updateSelectedStyle({ rotation: Number(e.target.value) })}
                />
              </div>

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
