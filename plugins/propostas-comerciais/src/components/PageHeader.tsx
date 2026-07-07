import type { ReactNode } from "react";
import { FileText } from "lucide-react";

import { PageHeader as PluginPageHeader, pageHeaderTitleRowBemClasses } from "@delpi/plugin-ui";

type PageHeaderProps = {
  title: string;
  subtitle: string;
  loading?: boolean;
  onRefresh?: () => void;
  actions?: ReactNode;
};

const LABELS = {
  refresh: "Atualizar",
  refreshing: "Atualizando…",
};

export function PageHeader({
  title,
  subtitle,
  loading = false,
  onRefresh,
  actions,
}: PageHeaderProps) {
  return (
    <PluginPageHeader
      layout="titleRow"
      classNames={pageHeaderTitleRowBemClasses("pc")}
      labels={LABELS}
      icon={<FileText size={28} strokeWidth={1.75} />}
      title={title}
      subtitle={subtitle}
      actions={actions}
      onRefresh={onRefresh}
      refreshing={loading}
    />
  );
}
