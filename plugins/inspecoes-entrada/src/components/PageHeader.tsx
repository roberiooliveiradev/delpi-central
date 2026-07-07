import { ClipboardCheck } from "lucide-react";

import { PageHeader as PluginPageHeader, pageHeaderTitleRowBemClasses } from "@delpi/plugin-ui";

type PageHeaderProps = {
  loading: boolean;
  branch: string;
  total: number;
  onRefresh: () => void;
};

const LABELS = {
  refresh: "Atualizar",
  refreshing: "Atualizando…",
};

export function PageHeader({ loading, branch, total, onRefresh }: PageHeaderProps) {
  const subtitle =
    total > 0
      ? `Inspeções de entrada — filial ${branch} · ${total.toLocaleString("pt-BR")} registro(s)`
      : `Inspeções de entrada — filial ${branch}`;

  return (
    <PluginPageHeader
      layout="titleRow"
      classNames={pageHeaderTitleRowBemClasses("ie")}
      labels={LABELS}
      icon={<ClipboardCheck size={28} strokeWidth={1.75} />}
      title="Histórico de Inspeções"
      subtitle={subtitle}
      onRefresh={onRefresh}
      refreshing={loading}
    />
  );
}
