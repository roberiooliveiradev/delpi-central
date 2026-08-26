import { Settings, LineChart } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { MaintenancePageHero } from "../../app/maintenanceUi";
import { StateBox } from "../../components/data";

type PlaceholderPageProps = {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  phase: string;
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function PlaceholderPage({
  title,
  subtitle,
  icon: Icon,
  phase,
}: PlaceholderPageProps) {
  return (
    <>
      <MaintenancePageHero
        eyebrow="DELPI • MANUTENÇÃO"
        title={
          <>
            <Icon size={28} strokeWidth={1.75} aria-hidden />
            {title}
          </>
        }
        description={subtitle}
      />

      <section className="dm-page-stack">
        <section className="dm-card">
          <StateBox>Entrega prevista na {phase} do roadmap.</StateBox>
        </section>
      </section>
    </>
  );
}

export { Settings as ConfigIcon, LineChart as ReportIcon };
