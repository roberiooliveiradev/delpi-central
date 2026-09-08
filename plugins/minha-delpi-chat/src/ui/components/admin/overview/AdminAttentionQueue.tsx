import { ADMIN_ATTENTION } from "../../../../content/adminAttentionContent";
import type { AttentionItem } from "./attentionQueue";
import type { AdminNavState } from "../../../../navigation/adminNavigation";

type AdminAttentionQueueProps = {
  items: AttentionItem[];
  onOpen: (nav: AdminNavState) => void;
};

function severityLabel(severity: AttentionItem["severity"]): string {
  if (severity === "critical") {
    return ADMIN_ATTENTION.severityCritical;
  }
  if (severity === "warning") {
    return ADMIN_ATTENTION.severityWarning;
  }
  return ADMIN_ATTENTION.severityInfo;
}

export function AdminAttentionQueue({ items, onOpen }: AdminAttentionQueueProps) {
  return (
    <article className="mdc-admin-attention-queue" aria-label={ADMIN_ATTENTION.sectionTitle}>
      <header className="mdc-admin-attention-queue__header">
        <h3>{ADMIN_ATTENTION.sectionTitle}</h3>
        <p className="mdc-chat-muted">{ADMIN_ATTENTION.sectionDescription}</p>
      </header>

      {items.length === 0 ? (
        <p className="mdc-admin-attention-queue__empty">{ADMIN_ATTENTION.empty}</p>
      ) : (
        <ul className="mdc-admin-attention-queue__list">
          {items.map((item) => (
            <li key={item.id} className={`mdc-admin-attention-queue__item is-${item.severity}`}>
              <div className="mdc-admin-attention-queue__body">
                <span
                  className={`mdc-admin-attention-queue__badge is-${item.severity}`}
                >
                  {severityLabel(item.severity)}
                </span>
                <strong>{item.title}</strong>
                <p>{item.detail}</p>
              </div>
              <button type="button" onClick={() => onOpen(item.nav)}>
                {ADMIN_ATTENTION.openAction}
              </button>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
