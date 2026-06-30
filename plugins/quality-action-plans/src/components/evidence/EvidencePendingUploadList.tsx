import type { PlanAction } from "../../types/actionPlan";
import {
  EvidencePendingUploadItem,
  type EvidencePendingUpload,
} from "./EvidencePendingUploadItem";

type Props = {
  items: EvidencePendingUpload[];
  actions: PlanAction[];
  lockActionId?: boolean;
  disabled?: boolean;
  onChange: (id: string, patch: Partial<EvidencePendingUpload>) => void;
  onRemove: (id: string) => void;
};

export function EvidencePendingUploadList({
  items,
  actions,
  lockActionId = false,
  disabled = false,
  onChange,
  onRemove,
}: Props) {
  if (!items.length) {
    return null;
  }

  return (
    <section className="pac-evidence-pending-queue" aria-label="Arquivos ainda não anexados">
      <header className="pac-evidence-pending-queue__header">
        <div>
          <h4 className="pac-evidence-pending-queue__title">
            Ainda não anexados ({items.length})
          </h4>
          <p className="pac-muted pac-evidence-pending-queue__hint">
            Cards em grade — expanda para tipo, seção 8D e vínculo. Use o olho para prévia local.
          </p>
        </div>
      </header>
      <div className="pac-evidence-pending-queue__list">
        {items.map((item, index) => (
          <EvidencePendingUploadItem
            key={item.id}
            item={item}
            actions={actions}
            lockActionId={lockActionId}
            disabled={disabled}
            defaultExpanded={items.length === 1 && index === 0}
            onChange={onChange}
            onRemove={onRemove}
          />
        ))}
      </div>
    </section>
  );
}
