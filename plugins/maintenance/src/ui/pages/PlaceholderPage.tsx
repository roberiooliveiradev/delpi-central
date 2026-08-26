import { Settings, LineChart } from "lucide-react";

import { StateBox } from "../../components/data";
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
    <div className="dm-page-stack">
      <PageHeader
        title={title}
        subtitle={subtitle}
        icon={icon}
        currentPath={pathname}
        onNavigate={onNavigate}
      />
      <section className="dm-card">
        <StateBox>Entrega prevista na {phase} do roadmap.</StateBox>
      </section>
    </div>
  );
}

export { Settings as ConfigIcon, LineChart as ReportIcon };
