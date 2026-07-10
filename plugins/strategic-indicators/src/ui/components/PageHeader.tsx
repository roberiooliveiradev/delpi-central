import type { ReactNode } from "react";

import { PageHeader as PluginPageHeader, pageHeaderStackBemClasses } from "@delpi/plugin-ui/index";

import "./PageHeader.css";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  badge?: ReactNode;
  actions?: ReactNode;
};

const LABELS = {
  refresh: "Atualizar",
  refreshing: "Atualizando…",
};

export function PageHeader({
  eyebrow,
  title,
  description,
  badge,
  actions,
}: PageHeaderProps) {
  return (
    <PluginPageHeader
      layout="stack"
      classNames={pageHeaderStackBemClasses("si")}
      labels={LABELS}
      eyebrow={eyebrow}
      title={title}
      subtitle={description}
      badge={badge}
      actions={actions}
    />
  );
}
