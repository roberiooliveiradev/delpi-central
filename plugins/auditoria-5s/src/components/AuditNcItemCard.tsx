import { ChevronDown } from "lucide-react";

import type { NcAttachmentMap, NcAttachmentType } from "../api/audit5sApi";
import {
  ncStatusLabel,
  ncStatusVariant,
  sensoAccentClass,
  sensoName,
} from "../constants/audit5s";
import type { NcFormState, NcTreatmentItem } from "../utils/auditNc";
import { formatNcScore } from "../utils/auditNc";
import { AuditNcItemEditor } from "./AuditNcItemEditor";

type Props = {
  auditId: string;
  item: NcTreatmentItem;
  form: NcFormState;
  attachmentsByNcId: NcAttachmentMap;
  disabled: boolean;
  expanded: boolean;
  saving: boolean;
  savedFlash: boolean;
  finalizing: boolean;
  uploadingType: NcAttachmentType | null;
  onToggle: () => void;
  onChange: (patch: Partial<NcFormState>) => void;
  onBlurSave: (patch?: Partial<NcFormState>) => void;
  onUpload: (type: NcAttachmentType, file: File) => Promise<void>;
  onFinalize: () => void;
};

function scoreTone(score: number): string {
  if (score <= 1) return "low";
  if (score <= 3) return "mid";
  return "high";
}

export function AuditNcItemCard({
  auditId,
  item,
  form,
  attachmentsByNcId,
  disabled,
  expanded,
  saving,
  savedFlash,
  finalizing,
  uploadingType,
  onToggle,
  onChange,
  onBlurSave,
  onUpload,
  onFinalize,
}: Props) {
  const sensoLabel = sensoName(item.sensoOrder, item.sensoName);
  const status = item.nc?.status ?? "open";

  return (
    <article className={`a5s-nc-item ${expanded ? "a5s-nc-item--expanded" : ""}`}>
      <button type="button" className="a5s-nc-item__header" onClick={onToggle}>
        <div className="a5s-nc-item__header-main">
          <span className={`a5s-nc-senso ${sensoAccentClass(item.sensoOrder)}`}>
            SENSO {item.sensoOrder} · {sensoLabel}
          </span>
          <strong className="a5s-nc-item__title">{item.criterionDescription}</strong>
        </div>
        <div className="a5s-nc-item__header-side">
          <span className={`a5s-status-badge a5s-status-badge--${ncStatusVariant(status)}`}>
            {ncStatusLabel(status)}
          </span>
          <span className={`a5s-nc-item__score a5s-nc-item__score--${scoreTone(item.score)}`}>
            Nota {formatNcScore(item.score)}
          </span>
          <ChevronDown size={18} className={expanded ? "a5s-nc-item__chevron--open" : undefined} aria-hidden />
        </div>
      </button>

      {expanded ? (
        <AuditNcItemEditor
          auditId={auditId}
          item={item}
          form={form}
          attachmentsByNcId={attachmentsByNcId}
          disabled={disabled}
          saving={saving}
          savedFlash={savedFlash}
          finalizing={finalizing}
          uploadingType={uploadingType}
          onChange={onChange}
          onBlurSave={onBlurSave}
          onUpload={onUpload}
          onFinalize={onFinalize}
        />
      ) : null}
    </article>
  );
}
