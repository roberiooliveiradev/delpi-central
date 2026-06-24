import type { ReactNode } from "react";
import { ClipboardList } from "lucide-react";

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
};

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <header className="pac-page-header">
      <div className="pac-page-header__brand">
        <div className="pac-header__icon" aria-hidden>
          <ClipboardList size={26} />
        </div>
        <div>
          <p className="pac-eyebrow">PAC Qualidade DELPI</p>
          <h1>{title}</h1>
          {subtitle ? <span className="pac-page-subtitle">{subtitle}</span> : null}
        </div>
      </div>
      {actions ? <div className="pac-header-actions">{actions}</div> : null}
    </header>
  );
}
