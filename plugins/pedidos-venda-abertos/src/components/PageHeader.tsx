import { ClipboardList } from "lucide-react";

import { PageHeader as PluginPageHeader, pageHeaderTitleRowBemClasses } from "@delpi/plugin-ui/index";

type PageHeaderProps = {
  loading: boolean;
  onRefresh: () => void;
  totalLoaded: number;
};

const LABELS = {
  refresh: "Atualizar",
  refreshing: "Atualizando…",
};

export function PageHeader({ loading, onRefresh, totalLoaded }: PageHeaderProps) {
  const subtitle =
    totalLoaded > 0
      ? `Consulta operacional de carteira em aberto · ${totalLoaded.toLocaleString("pt-BR")} linha(s) carregadas`
      : "Consulta operacional de carteira em aberto";

  return (
    <PluginPageHeader
      layout="titleRow"
      classNames={pageHeaderTitleRowBemClasses("pva")}
      labels={LABELS}
      icon={<ClipboardList size={28} strokeWidth={1.75} />}
      title="Pedidos de Venda em Aberto"
      subtitle={subtitle}
      onRefresh={onRefresh}
      refreshing={loading}
    />
  );
}
