import type { ReactNode } from "react";
import "./Modal.css";

import { X } from "lucide-react";

type Props = {
  open: boolean;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
};

export const Modal = ({ open, title, children, footer, onClose }: Props) => {
  if (!open) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">{title ?? "Modal"}</div>
          <button className="modal-close" onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">{children}</div>

        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
};