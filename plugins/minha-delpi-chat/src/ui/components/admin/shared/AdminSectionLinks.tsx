import { ArrowRight } from "lucide-react";

import "./AdminSectionLinks.css";

export type AdminSectionLinkItem = {
  label: string;
  onClick: () => void;
};

type AdminSectionLinksProps = {
  items: AdminSectionLinkItem[];
};

export function AdminSectionLinks({ items }: AdminSectionLinksProps) {
  if (!items.length) {
    return null;
  }

  return (
    <nav className="mdc-admin-section-links" aria-label="Atalhos relacionados">
      {items.map((item) => (
        <button key={item.label} type="button" className="mdc-admin-section-links__btn" onClick={item.onClick}>
          <span>{item.label}</span>
          <ArrowRight size={14} aria-hidden />
        </button>
      ))}
    </nav>
  );
}
