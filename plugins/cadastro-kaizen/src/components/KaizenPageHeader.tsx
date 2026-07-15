import type { ReactNode } from "react";
import { ArrowLeft, Sparkles } from "lucide-react";

import { PageHeader, pageHeaderBrandBemClasses } from "./ui";

const LABELS = {
  refresh: "Atualizar",
  refreshing: "Atualizando…",
};

const EYEBROW = "DELPI • Qualidade • Cadastro";

type KaizenPageHeaderProps = {
  title: string;
  subtitle: string;
  actions?: ReactNode;
  nav?: ReactNode;
  showBack?: boolean;
  onBack?: () => void;
};

export function KaizenPageHeader({
  title,
  subtitle,
  actions,
  nav,
  showBack,
  onBack,
}: KaizenPageHeaderProps) {
  const mergedActions =
    showBack && onBack ? (
      <>
        <button type="button" className="kz-ghost-btn" onClick={onBack}>
          <ArrowLeft size={16} aria-hidden="true" />
          Voltar
        </button>
        {actions}
      </>
    ) : (
      actions
    );

  return (
    <PageHeader
      layout="brand"
      classNames={pageHeaderBrandBemClasses("kz")}
      labels={LABELS}
      icon={<Sparkles size={28} strokeWidth={1.75} />}
      eyebrow={EYEBROW}
      title={title}
      subtitle={subtitle}
      nav={nav}
      actions={mergedActions}
    />
  );
}
