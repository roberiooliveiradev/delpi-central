import type { ReactNode } from "react";
import { ClipboardList } from "lucide-react";

import { PageHeader as PluginPageHeader, pageHeaderPacBrandBemClasses } from "@delpi/plugin-ui/index";

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
};

const LABELS = {
  refresh: "Atualizar",
  refreshing: "Atualizando…",
};

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <PluginPageHeader
      layout="brand"
      classNames={pageHeaderPacBrandBemClasses("pac")}
      labels={LABELS}
      icon={<ClipboardList size={26} />}
      eyebrow="PAC Qualidade DELPI"
      title={title}
      subtitle={subtitle}
      actions={actions}
    />
  );
}
