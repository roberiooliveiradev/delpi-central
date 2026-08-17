import { useEffect, useId, useRef, useState } from "react";
import { ImagePlus, Trash2, Upload } from "lucide-react";

import { CostCenterIconPicker } from "./CostCenterIconPicker";
import { CapexCategoryVisual } from "./CapexCategoryVisual";

type CategoryVisualPickerProps = {
  label: string;
  categoryId?: string | null;
  iconKey?: string | null;
  hasCustomIcon?: boolean;
  busy?: boolean;
  /** Só Lucide — usado na criação antes de existir id. */
  onSelectLucide: (iconKey: string | null) => void;
  onUploadFile?: (file: File) => void | Promise<void>;
  onClearImage?: () => void | Promise<void>;
  /** Arquivo pendente na criação (ainda sem categoryId). */
  pendingFile?: File | null;
  pendingFileName?: string | null;
  onPickPendingFile?: (file: File | null) => void;
};

export function CategoryVisualPicker({
  label,
  categoryId,
  iconKey,
  hasCustomIcon = false,
  busy = false,
  onSelectLucide,
  onUploadFile,
  onClearImage,
  pendingFile = null,
  pendingFileName,
  onPickPendingFile,
}: CategoryVisualPickerProps) {
  const inputId = useId();
  const fileRef = useRef<HTMLInputElement>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [pendingPreviewUrl, setPendingPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!pendingFile) {
      setPendingPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(pendingFile);
    setPendingPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [pendingFile]);

  function validateFile(file: File): string | null {
    const okMime = ["image/png", "image/jpeg", "image/webp", "image/gif"].includes(
      file.type,
    );
    if (!okMime) return "Use PNG, JPEG, WebP ou GIF.";
    if (file.size > 2 * 1024 * 1024) return "Imagem deve ter no máximo 2 MB.";
    return null;
  }

  async function handleFileChange(file: File | null) {
    setLocalError(null);
    if (!file) {
      onPickPendingFile?.(null);
      return;
    }
    const err = validateFile(file);
    if (err) {
      setLocalError(err);
      return;
    }
    if (categoryId && onUploadFile) {
      await onUploadFile(file);
      return;
    }
    onPickPendingFile?.(file);
  }

  const displayName = pendingFileName ?? pendingFile?.name ?? null;

  return (
    <div className="po-cat-visual-picker">
      <div className="po-cat-visual-picker__preview" aria-hidden="true">
        {pendingPreviewUrl ? (
          <img
            src={pendingPreviewUrl}
            alt=""
            width={36}
            height={36}
            style={{ objectFit: "contain", borderRadius: 8 }}
          />
        ) : (
          <CapexCategoryVisual
            categoryId={categoryId}
            iconKey={iconKey}
            hasCustomIcon={hasCustomIcon}
            size={36}
            alt=""
          />
        )}
      </div>
      <div className="po-cat-visual-picker__controls">
        <div className="po-cat-visual-picker__row">
          <span className="po-cat-visual-picker__label">Catálogo Lucide</span>
          <CostCenterIconPicker
            iconKey={iconKey}
            label={label}
            busy={busy}
            onSelect={onSelectLucide}
          />
        </div>
        <div className="po-cat-visual-picker__row">
          <span className="po-cat-visual-picker__label">Imagem</span>
          <div className="po-cat-visual-picker__upload-actions">
            <input
              ref={fileRef}
              id={inputId}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif,.png,.jpg,.jpeg,.webp,.gif"
              className="po-sr-only"
              disabled={busy}
              onChange={(e) => {
                const file = e.target.files?.[0] ?? null;
                void handleFileChange(file);
                e.target.value = "";
              }}
            />
            <button
              type="button"
              className="po-btn po-btn--secondary po-btn--sm"
              disabled={busy}
              onClick={() => fileRef.current?.click()}
            >
              {categoryId ? (
                <>
                  <Upload size={14} aria-hidden="true" />
                  Importar
                </>
              ) : (
                <>
                  <ImagePlus size={14} aria-hidden="true" />
                  Escolher
                </>
              )}
            </button>
            {(hasCustomIcon || displayName) && onClearImage ? (
              <button
                type="button"
                className="po-btn po-btn--secondary po-btn--sm"
                disabled={busy}
                onClick={() => void onClearImage()}
              >
                <Trash2 size={14} aria-hidden="true" />
                Remover
              </button>
            ) : null}
            {displayName && !categoryId ? (
              <button
                type="button"
                className="po-btn po-btn--secondary po-btn--sm"
                disabled={busy}
                onClick={() => onPickPendingFile?.(null)}
              >
                <Trash2 size={14} aria-hidden="true" />
                Limpar
              </button>
            ) : null}
          </div>
        </div>
        {displayName ? (
          <p className="po-muted po-cat-visual-picker__hint">
            Arquivo pendente: {displayName} (será enviado ao salvar)
          </p>
        ) : null}
        {hasCustomIcon ? (
          <p className="po-muted po-cat-visual-picker__hint">
            Imagem customizada em uso (prioridade sobre o Lucide).
          </p>
        ) : (
          <p className="po-muted po-cat-visual-picker__hint">
            PNG, JPEG, WebP ou GIF · até 2 MB.
          </p>
        )}
        {localError ? (
          <p className="po-cat-visual-picker__error" role="alert">
            {localError}
          </p>
        ) : null}
      </div>
    </div>
  );
}
