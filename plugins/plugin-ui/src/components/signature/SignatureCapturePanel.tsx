import { useEffect, useMemo, useRef, useState } from "react";

import { SignaturePad, type SignaturePadProps } from "./SignaturePad";

export type SignatureCaptureMode = "draw" | "type" | "upload";

export type SignatureCapturePanelProps = {
  disabled?: boolean;
  displayName?: string;
  showPreview?: boolean;
  modes?: SignatureCaptureMode[];
  onChange?: (blob: Blob | null) => void;
  className?: string;
  padProps?: Omit<SignaturePadProps, "onChange" | "disabled" | "labels">;
  labels?: {
    modeDraw?: string;
    modeType?: string;
    modeUpload?: string;
    typePlaceholder?: string;
    typeApply?: string;
    uploadHint?: string;
    previewTitle?: string;
    pad?: SignaturePadProps["labels"];
  };
};

async function blobFromTypedName(text: string, width = 640, height = 220): Promise<Blob | null> {
  const trimmed = text.trim();
  if (!trimmed) return null;
  const canvas = document.createElement("canvas");
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#0f172a";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const fontSize = Math.max(28, Math.min(56, Math.floor(width / Math.max(8, trimmed.length * 0.55))));
  ctx.font = `italic ${fontSize}px "Segoe Script", "Brush Script MT", "Apple Chancery", cursive`;
  ctx.fillText(trimmed, width / 2, height / 2);
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), "image/png");
  });
}

async function blobFromImageFile(file: File, width = 640, height = 220): Promise<Blob | null> {
  if (!file.type.startsWith("image/")) return null;
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement("canvas");
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    bitmap.close();
    return null;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const scale = Math.min(width / bitmap.width, height / bitmap.height);
  const drawW = bitmap.width * scale;
  const drawH = bitmap.height * scale;
  const dx = (width - drawW) / 2;
  const dy = (height - drawH) / 2;
  ctx.drawImage(bitmap, dx, dy, drawW, drawH);
  bitmap.close();
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), "image/png");
  });
}

export function SignatureCapturePanel({
  disabled = false,
  displayName,
  showPreview = true,
  modes = ["draw", "type", "upload"],
  onChange,
  className,
  padProps,
  labels,
}: SignatureCapturePanelProps) {
  const [mode, setMode] = useState<SignatureCaptureMode>(modes[0] ?? "draw");
  const [typedName, setTypedName] = useState(displayName ?? "");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const width = padProps?.width ?? 640;
  const height = padProps?.height ?? 220;

  const availableModes = useMemo(
    () => modes.filter((item, index) => modes.indexOf(item) === index),
    [modes],
  );

  useEffect(() => {
    if (displayName != null) setTypedName(displayName);
  }, [displayName]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function publish(blob: Blob | null) {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(blob ? URL.createObjectURL(blob) : null);
    onChange?.(blob);
  }

  async function applyTyped() {
    if (disabled) return;
    const blob = await blobFromTypedName(typedName, width, height);
    publish(blob);
  }

  async function handleUpload(file: File | null) {
    if (disabled || !file) return;
    const blob = await blobFromImageFile(file, width, height);
    publish(blob);
  }

  return (
    <div className={["delpi-ui-signature-capture", className].filter(Boolean).join(" ")}>
      <div className="delpi-ui-signature-capture__modes" role="tablist" aria-label="Modo de assinatura">
        {availableModes.includes("draw") ? (
          <button
            type="button"
            role="tab"
            aria-selected={mode === "draw"}
            className={["delpi-ui-signature-capture__mode", mode === "draw" ? "is-active" : ""]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setMode("draw")}
            disabled={disabled}
            data-testid="signature-capture-mode-draw"
          >
            {labels?.modeDraw || "Desenhar"}
          </button>
        ) : null}
        {availableModes.includes("type") ? (
          <button
            type="button"
            role="tab"
            aria-selected={mode === "type"}
            className={["delpi-ui-signature-capture__mode", mode === "type" ? "is-active" : ""]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setMode("type")}
            disabled={disabled}
            data-testid="signature-capture-mode-type"
          >
            {labels?.modeType || "Digitar"}
          </button>
        ) : null}
        {availableModes.includes("upload") ? (
          <button
            type="button"
            role="tab"
            aria-selected={mode === "upload"}
            className={["delpi-ui-signature-capture__mode", mode === "upload" ? "is-active" : ""]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setMode("upload")}
            disabled={disabled}
            data-testid="signature-capture-mode-upload"
          >
            {labels?.modeUpload || "Upload"}
          </button>
        ) : null}
      </div>

      {mode === "draw" ? (
        <SignaturePad
          {...padProps}
          disabled={disabled}
          onChange={publish}
          labels={labels?.pad}
        />
      ) : null}

      {mode === "type" ? (
        <div className="delpi-ui-signature-capture__type">
          <input
            type="text"
            className="delpi-ui-signature-capture__type-input"
            value={typedName}
            disabled={disabled}
            placeholder={labels?.typePlaceholder || "Digite o nome para assinar"}
            onChange={(event) => setTypedName(event.target.value)}
            data-testid="signature-capture-type-input"
          />
          <button
            type="button"
            className="delpi-ui-signature-capture__type-apply"
            disabled={disabled || !typedName.trim()}
            onClick={() => void applyTyped()}
            data-testid="signature-capture-type-apply"
          >
            {labels?.typeApply || "Gerar assinatura"}
          </button>
        </div>
      ) : null}

      {mode === "upload" ? (
        <div className="delpi-ui-signature-capture__upload">
          <p className="delpi-ui-signature-capture__upload-hint">
            {labels?.uploadHint || "Envie PNG ou JPEG da assinatura"}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg"
            disabled={disabled}
            onChange={(event) => void handleUpload(event.target.files?.[0] ?? null)}
            data-testid="signature-capture-upload-input"
          />
        </div>
      ) : null}

      {showPreview ? (
        <div className="delpi-ui-signature-capture__preview">
          <p className="delpi-ui-signature-capture__preview-title">
            {labels?.previewTitle || "Prévia"}
          </p>
          <div className="delpi-ui-signature-capture__preview-card">
            {displayName || typedName ? (
              <strong className="delpi-ui-signature-capture__preview-name">
                {(displayName || typedName).trim()}
              </strong>
            ) : null}
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Prévia da assinatura"
                className="delpi-ui-signature-capture__preview-image"
              />
            ) : (
              <span className="delpi-ui-signature-capture__preview-empty">Sem assinatura ainda</span>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
