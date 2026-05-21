import type { PropsWithChildren, ReactNode } from "react";
import "./AdminInlineToolPanel.css";

type AdminInlineToolPanelProps = PropsWithChildren<{
  title: string;
  description?: string;
  open: boolean;
  onClose: () => void;
  footer?: ReactNode;
}>;

export function AdminInlineToolPanel({
  title,
  description,
  open,
  onClose,
  footer,
  children,
}: AdminInlineToolPanelProps) {
  if (!open) return null;

  return (
    <section className="si-admin-inline-tool" aria-label={title}>
      <div className="si-admin-inline-tool__header">
        <div>
          <h4 className="si-admin-inline-tool__title">{title}</h4>
          {description ? (
            <p className="si-admin-inline-tool__description">{description}</p>
          ) : null}
        </div>

        <button
          type="button"
          className="si-settings-editor__button si-settings-editor__button--secondary"
          onClick={onClose}
        >
          Fechar
        </button>
      </div>

      <div className="si-admin-inline-tool__body">{children}</div>

      {footer ? <div className="si-admin-inline-tool__footer">{footer}</div> : null}
    </section>
  );
}
