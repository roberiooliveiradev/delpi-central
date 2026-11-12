import {
  Activity,
  Boxes,
  ClipboardList,
  Database,
  History,
  LayoutGrid,
  Network,
  NotebookPen,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import type { Capabilities } from "../../api/itPortalApi";

export type ServerSectionId =
  | "overview"
  | "inventory"
  | "services"
  | "databases"
  | "networks"
  | "integrations"
  | "actions"
  | "notes"
  | "history";

type SectionDefinition = {
  id: ServerSectionId;
  label: string;
  description: string;
  icon: LucideIcon;
  canView?: (capabilities: Capabilities) => boolean;
};

const SECTIONS: readonly SectionDefinition[] = [
  { id: "overview", label: "Visão geral", description: "Cadastro e operação", icon: LayoutGrid },
  { id: "inventory", label: "Coleta automática", description: "Indicadores do host", icon: Activity },
  {
    id: "services",
    label: "Serviços",
    description: "Aplicações hospedadas",
    icon: Boxes,
    canView: (caps) => caps.can_view_services,
  },
  {
    id: "databases",
    label: "Bancos de dados",
    description: "Instâncias vinculadas",
    icon: Database,
    canView: (caps) => caps.can_view_databases,
  },
  {
    id: "networks",
    label: "Redes",
    description: "Vínculos de rede",
    icon: Network,
    canView: (caps) => caps.can_view_networks,
  },
  {
    id: "integrations",
    label: "Integrações",
    description: "Sistemas conectados",
    icon: Workflow,
    canView: (caps) => caps.can_view_integrations,
  },
  {
    id: "actions",
    label: "Planos de ação",
    description: "Pendências e melhorias",
    icon: ClipboardList,
    canView: (caps) => caps.can_view_action_plans,
  },
  { id: "notes", label: "Notas técnicas", description: "Registros da equipe", icon: NotebookPen },
  { id: "history", label: "Histórico", description: "Auditoria e alterações", icon: History },
];

export function availableServerSections(capabilities: Capabilities): SectionDefinition[] {
  return SECTIONS.filter((section) => !section.canView || section.canView(capabilities));
}

export function ServerSectionNavigation({
  sections,
  active,
  onSelect,
}: {
  sections: SectionDefinition[];
  active: ServerSectionId;
  onSelect: (section: ServerSectionId) => void;
}) {
  return (
    <div className="itp-server-workspace">
      <div className="itp-server-workspace__intro">
        <div>
          <p className="itp-server-workspace__eyebrow">Explorar servidor</p>
          <h2 className="itp-server-workspace__title">O que você quer consultar?</h2>
        </div>
        <p className="itp-server-workspace__hint">Escolha uma área. Apenas o conteúdo selecionado será exibido.</p>
      </div>
      <nav className="itp-server-launcher" aria-label="Seções deste servidor">
        {sections.map((section) => {
          const Icon = section.icon;
          const selected = active === section.id;
          return (
            <button
              key={section.id}
              type="button"
              className={`itp-server-launcher__item${selected ? " is-active" : ""}`}
              aria-pressed={selected}
              aria-controls="itp-server-active-panel"
              onClick={() => onSelect(section.id)}
            >
              <span className="itp-server-launcher__icon">
                <Icon size={24} strokeWidth={1.7} aria-hidden="true" />
              </span>
              <span className="itp-server-launcher__label">{section.label}</span>
              <span className="itp-server-launcher__description">{section.description}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
