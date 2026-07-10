import type { ReactNode } from "react";
import { Gauge } from "lucide-react";

import { PageHeader as PluginPageHeader, pageHeaderBrandBemClasses } from "@delpi/plugin-ui/index";

import { TransformometroNav } from "./TransformometroNav";
import "./PageHeader.css";

type PageHeaderProps = {
  title: string;
  subtitle: string;
  currentPath?: string;
  onNavigate: (path: string) => void;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
};

const LABELS = {
  refresh: "Atualizar",
  refreshing: "Atualizando…",
};

export function PageHeader({
  title,
  subtitle,
  currentPath,
  onNavigate,
  onRefresh,
  refreshing = false,
  actions,
}: PageHeaderProps) {
  return (
    <PluginPageHeader
      layout="brand"
      classNames={pageHeaderBrandBemClasses("ds")}
      labels={LABELS}
      icon={<Gauge size={28} strokeWidth={1.75} />}
      eyebrow="DELPI • Transformômetro"
      title={title}
      subtitle={subtitle}
      nav={<TransformometroNav currentPath={currentPath} onNavigate={onNavigate} />}
      actions={actions}
      onRefresh={onRefresh}
      refreshing={refreshing}
    />
  );
}
