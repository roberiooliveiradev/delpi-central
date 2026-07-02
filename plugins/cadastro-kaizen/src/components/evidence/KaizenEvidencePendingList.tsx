import { FileText, X } from "lucide-react";
import { useEffect, useState } from "react";

import type { KaizenEvidenceStage } from "../../types/kaizen";
import { formatEvidenceFileSize, isImageFile } from "./kaizenEvidenceUtils";

export type KaizenPendingUpload = {
  id: string;
  file: File;
  stage: KaizenEvidenceStage;
  description: string;
};

type Props = {
  items: KaizenPendingUpload[];
  disabled?: boolean;
  onChange: (id: string, patch: Partial<KaizenPendingUpload>) => void;
  onRemove: (id: string) => void;
};

function PendingThumb({ file }: { file: File }) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!isImageFile(file)) return undefined;
    const url = URL.createObjectURL(file);
    setObjectUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  if (objectUrl) {
    return <img className="kz-pending__thumb" src={objectUrl} alt={file.name} />;
  }
  return (
    <div className="kz-pending__thumb kz-pending__thumb--file" aria-hidden="true">
      <FileText size={20} />
    </div>
  );
}

export function KaizenEvidencePendingList({ items, disabled = false, onChange, onRemove }: Props) {
  return (
    <ul className="kz-pending-list">
      {items.map((item) => (
        <li className="kz-pending" key={item.id}>
          <PendingThumb file={item.file} />
          <div className="kz-pending__body">
            <div className="kz-pending__head">
              <span className="kz-pending__name" title={item.file.name}>
                {item.file.name}
              </span>
              <span className="kz-pending__size">{formatEvidenceFileSize(item.file.size)}</span>
            </div>
            <div className="kz-pending__fields">
              <select
                className="kz-pending__stage"
                value={item.stage}
                disabled={disabled}
                aria-label={`Etapa de ${item.file.name}`}
                onChange={(event) =>
                  onChange(item.id, { stage: event.target.value as KaizenEvidenceStage })
                }
              >
                <option value="antes">Antes</option>
                <option value="depois">Depois</option>
                <option value="geral">Geral</option>
              </select>
              <input
                className="kz-pending__desc"
                placeholder="Descrição (opcional)"
                value={item.description}
                disabled={disabled}
                aria-label={`Descrição de ${item.file.name}`}
                onChange={(event) => onChange(item.id, { description: event.target.value })}
              />
            </div>
          </div>
          <button
            type="button"
            className="kz-pending__remove"
            disabled={disabled}
            aria-label={`Remover ${item.file.name} da fila`}
            onClick={() => onRemove(item.id)}
          >
            <X size={14} aria-hidden="true" />
          </button>
        </li>
      ))}
    </ul>
  );
}
