import { useRef, useState } from "react";
import { Camera, CheckCircle2, ImagePlus } from "lucide-react";

import type { NcAttachment, NcAttachmentType } from "../api/audit5sApi";
import { NcAttachmentPreview } from "./NcAttachmentPreview";

type Props = {
  ncId: string | null;
  before?: NcAttachment;
  after?: NcAttachment;
  disabled: boolean;
  uploadingType: NcAttachmentType | null;
  onUpload: (type: NcAttachmentType, file: File) => Promise<void>;
};

function EvidenceSlot({
  label,
  hint,
  type,
  ncId,
  attachment,
  disabled,
  uploading,
  onSelect,
}: {
  label: string;
  hint: string;
  type: NcAttachmentType;
  ncId: string | null;
  attachment?: NcAttachment;
  disabled: boolean;
  uploading: boolean;
  onSelect: (type: NcAttachmentType, file: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <article className="a5s-nc-evidence__slot">
      <div className="a5s-nc-evidence__slot-head">
        <strong>{label}</strong>
        {attachment ? (
          <span className="a5s-nc-evidence__slot-badge">
            <CheckCircle2 size={14} aria-hidden />
            Anexada
          </span>
        ) : null}
      </div>
      <p className="a5s-nc-evidence__hint">{hint}</p>

      {attachment && ncId ? (
        <NcAttachmentPreview ncId={ncId} attachment={attachment} label={label} />
      ) : (
        <div className="a5s-nc-evidence__placeholder" aria-hidden>
          <Camera size={28} />
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="a5s-nc-evidence__input"
        disabled={disabled || !ncId || uploading}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onSelect(type, file);
          event.target.value = "";
        }}
      />
      <button
        type="button"
        className="a5s-btn a5s-btn--ghost a5s-btn--small"
        disabled={disabled || !ncId || uploading}
        onClick={() => inputRef.current?.click()}
      >
        <ImagePlus size={15} aria-hidden />
        {uploading ? "Enviando..." : attachment ? "Substituir foto" : "Anexar foto"}
      </button>
    </article>
  );
}

export function AuditNcEvidenceSection({
  ncId,
  before,
  after,
  disabled,
  uploadingType,
  onUpload,
}: Props) {
  const [error, setError] = useState<string | null>(null);

  const handleSelect = async (type: NcAttachmentType, file: File) => {
    setError(null);
    try {
      await onUpload(type, file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao anexar evidência.");
    }
  };

  return (
    <section className="a5s-nc-evidence" aria-label="Evidências fotográficas">
      <div className="a5s-nc-evidence__head">
        <h4>Evidências da ação corretiva</h4>
        <p>Anexe a foto do antes e do depois para finalizar a ação.</p>
      </div>

      {!ncId ? (
        <p className="a5s-nc-evidence__hint a5s-nc-evidence__hint--block">
          Salve o plano de ação (descrição, causa, ação, responsável e prazo) para habilitar o
          envio de evidências.
        </p>
      ) : null}

      <div className="a5s-nc-evidence__grid">
        <EvidenceSlot
          label="Foto do antes"
          hint={
            before
              ? "Situação observada na auditoria (pode ter vindo da avaliação)."
              : "Situação observada na auditoria."
          }
          type="before"
          ncId={ncId}
          attachment={before}
          disabled={disabled}
          uploading={uploadingType === "before"}
          onSelect={(type, file) => void handleSelect(type, file)}
        />
        <EvidenceSlot
          label="Foto do depois"
          hint="Situação após a ação corretiva."
          type="after"
          ncId={ncId}
          attachment={after}
          disabled={disabled}
          uploading={uploadingType === "after"}
          onSelect={(type, file) => void handleSelect(type, file)}
        />
      </div>

      {error ? <p className="a5s-nc-evidence__error">{error}</p> : null}
    </section>
  );
}
