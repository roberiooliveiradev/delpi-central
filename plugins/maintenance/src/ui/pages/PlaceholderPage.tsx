import { Settings, LineChart } from "lucide-react";

import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";

type PlaceholderPageProps = {
  title: string;
  subtitle: string;
  icon: typeof Settings;
  phase: string;
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function PlaceholderPage({
  title,
  subtitle,
  icon,
  phase,
  pathname,
  onNavigate,
}: PlaceholderPageProps) {
  return (
    <MaintenanceShell>
      <PageHeader
        title={title}
        subtitle={subtitle}
        icon={icon}
        currentPath={pathname}
        onNavigate={onNavigate}
      />
      <section className="dm-card">
        <p className="dm-state-box">Entrega prevista na {phase} do roadmap.</p>
      </section>
    </MaintenanceShell>
  );
}

export { Settings as ConfigIcon, LineChart as ReportIcon };
