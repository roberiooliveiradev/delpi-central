import { Keyboard, PenLine, Upload } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { blobFromSignatureImageFile } from "./blobFromSignatureImageFile";
import { centerSignaturePngBlob } from "./centerSignaturePngBlob";
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
    uploadInvalidType?: string;
    uploadFailed?: string;
    previewTitle?: string;
    modesHelp?: string;
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
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadBusy, setUploadBusy] = useState(false);
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

  async function publish(blob: Blob | null) {
    if (previewUrl) {
      try {
        URL.revokeObjectURL(previewUrl);
      } catch {
        /* jsdom */
      }
    }
    if (!blob) {
      setPreviewUrl(null);
      onChange?.(null);
      return;
    }
    const centered = await centerSignaturePngBlob(blob);
    let nextUrl: string | null = null;
    try {
      nextUrl = URL.createObjectURL(centered);
    } catch {
      nextUrl = null;
    }
    setPreviewUrl(nextUrl);
    onChange?.(centered);
  }

  function selectMode(next: SignatureCaptureMode) {
    setMode(next);
    setUploadError(null);
  }

  async function applyTyped() {
    if (disabled) return;
    setUploadError(null);
    const blob = await blobFromTypedName(typedName, width, height);
    await publish(blob);
  }

  async function handleUpload(file: File | null) {
    if (disabled || !file) return;
    setUploadBusy(true);
    setUploadError(null);
    try {
      const blob = await blobFromSignatureImageFile(file, width, height);
      if (!blob) {
        setUploadError(
          labels?.uploadInvalidType ||
            "Arquivo inválido. Envie uma imagem PNG ou JPEG da assinatura.",
        );
        return;
      }
      await publish(blob);
    } catch {
      setUploadError(
        labels?.uploadFailed ||
          "Não foi possível ler a imagem. Tente outro PNG ou JPEG.",
      );
    } finally {
      setUploadBusy(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  return (
    <div className={["delpi-ui-signature-capture", className].filter(Boolean).join(" ")}>
      <div className="delpi-ui-signature-capture__modes-row">
        <div
          className="delpi-ui-signature-capture__modes"
          role="tablist"
          aria-label="Modo de assinatura"
          title={
            labels?.modesHelp ||
            "Desenhar: traço manuscrito. Digitar: gera assinatura em fonte script. Upload: PNG ou JPEG da assinatura."
          }
        >
          {availableModes.includes("draw") ? (
            <button
              type="button"
              role="tab"
              aria-selected={mode === "draw"}
              className={["delpi-ui-signature-capture__mode", mode === "draw" ? "is-active" : ""]
                .filter(Boolean)
                .join(" ")}
              onClick={() => selectMode("draw")}
              disabled={disabled}
              data-testid="signature-capture-mode-draw"
            >
              <PenLine size={16} aria-hidden />
              <span>{labels?.modeDraw || "Desenhar"}</span>
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
              onClick={() => selectMode("type")}
              disabled={disabled}
              data-testid="signature-capture-mode-type"
            >
              <Keyboard size={16} aria-hidden />
              <span>{labels?.modeType || "Digitar"}</span>
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
              onClick={() => selectMode("upload")}
              disabled={disabled}
              data-testid="signature-capture-mode-upload"
            >
              <Upload size={16} aria-hidden />
              <span>{labels?.modeUpload || "Upload"}</span>
            </button>
          ) : null}
        </div>
      </div>

      {mode === "draw" ? (
        <SignaturePad
          {...padProps}
          disabled={disabled}
          onChange={(blob) => {
            setUploadError(null);
            void publish(blob);
          }}
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
            className="delpi-ui-action-btn delpi-ui-action-btn--primary"
            disabled={disabled || !typedName.trim()}
            onClick={() => void applyTyped()}
            data-testid="signature-capture-type-apply"
          >
            <PenLine size={16} aria-hidden />
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
            accept="image/png,image/jpeg,.png,.jpg,.jpeg"
            disabled={disabled || uploadBusy}
            onChange={(event) => void handleUpload(event.target.files?.[0] ?? null)}
            data-testid="signature-capture-upload-input"
          />
          {uploadBusy ? (
            <p className="delpi-ui-signature-capture__upload-hint" data-testid="signature-capture-upload-busy">
              Processando imagem…
            </p>
          ) : null}
          {uploadError ? (
            <p
              className="delpi-ui-signature-capture__upload-error"
              role="alert"
              data-testid="signature-capture-upload-error"
            >
              {uploadError}
            </p>
          ) : null}
        </div>
      ) : null}

      {showPreview ? (
        <div className="delpi-ui-signature-capture__preview">
          <div className="delpi-ui-signature-capture__preview-title-row">
            <p
              className="delpi-ui-signature-capture__preview-title"
              title="A prévia mostra como o nome e o traço aparecem juntos antes de salvar."
            >
              {labels?.previewTitle || "Prévia"}
            </p>
          </div>
          <div className="delpi-ui-signature-capture__preview-card">
            {displayName || typedName ? (
              <strong className="delpi-ui-signature-capture__preview-name">
                {(displayName || typedName).trim()}
              </strong>
            ) : null}
            {previewUrl ? (
              <div className="delpi-ui-signature-capture__paper">
                <img
                  src={previewUrl}
                  alt="Prévia da assinatura"
                  className="delpi-ui-signature-capture__preview-image"
                />
              </div>
            ) : (
              <span className="delpi-ui-signature-capture__preview-empty">Sem assinatura ainda</span>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
