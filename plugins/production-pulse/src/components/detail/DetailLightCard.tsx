import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { PpSectionCard } from "../../app/productionPulseUi";

type DetailLightCardProps = {
  icon: LucideIcon;
  title: string;
  hint?: string;
  children: ReactNode;
};

/** Card leve de detalhe: ícone + título + conteúdo enxuto (sem visual carregado). */
export function DetailLightCard({ icon: Icon, title, hint, children }: DetailLightCardProps) {
  return (
    <PpSectionCard
      title={
        <span className="pp-detail-section-title">
          <Icon size={16} className="pp-detail-card-icon" aria-hidden />
          {title}
        </span>
      }
      hint={hint}
    >
      {children}
    </PpSectionCard>
  );
}
