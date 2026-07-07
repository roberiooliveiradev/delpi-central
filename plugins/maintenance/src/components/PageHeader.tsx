import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { PageHeader as PluginPageHeader, pageHeaderBrandBemClasses } from "@delpi/plugin-ui";

import { MaintenanceNav } from "./MaintenanceNav";
import "./PageHeader.css";

type PageHeaderProps = {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  eyebrow?: string;
  currentPath?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
  actions?: ReactNode;
  showNav?: boolean;
  compact?: boolean;
};

const LABELS = {
  refresh: "Atualizar",
  refreshing: "Atualizando…",
};

export function PageHeader({
  title,
  subtitle,
  icon: Icon,
  eyebrow = "DELPI • Manutenção",
  filialScope,
  onNavigate,
  actions,
  showNav = true,
  compact = false,
}: PageHeaderProps) {
  return (
    <PluginPageHeader
      layout="brand"
      classNames={pageHeaderBrandBemClasses("dm")}
      labels={LABELS}
      compact={compact}
      icon={<Icon size={28} strokeWidth={1.75} />}
      eyebrow={eyebrow}
      title={title}
      subtitle={subtitle}
      nav={showNav ? <MaintenanceNav filialScope={filialScope} onNavigate={onNavigate} /> : null}
      actions={actions}
    />
  );
}
