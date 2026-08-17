import type { LucideIcon } from "lucide-react";
import {
  Bot,
  Boxes,
  Briefcase,
  Building2,
  Calculator,
  Car,
  CircuitBoard,
  ClipboardList,
  Cog,
  Cpu,
  Factory,
  Fan,
  FlaskConical,
  Gauge,
  Hammer,
  HardHat,
  HeartHandshake,
  Landmark,
  Laptop,
  Leaf,
  Monitor,
  Package,
  Radio,
  Ruler,
  ShieldCheck,
  Tags,
  Truck,
  Users,
  Warehouse,
  Wrench,
  Zap,
} from "lucide-react";

/** Catálogo Lucide compartilhado (CC + categorias CAPEX). Alinhado à API. */
export const LUCIDE_ICON_CATALOG: ReadonlyArray<{
  key: string;
  label: string;
  Icon: LucideIcon;
}> = [
  { key: "tags", label: "Categoria", Icon: Tags },
  { key: "building-2", label: "Edifício", Icon: Building2 },
  { key: "users", label: "Pessoas", Icon: Users },
  { key: "laptop", label: "TI", Icon: Laptop },
  { key: "monitor", label: "Computadores", Icon: Monitor },
  { key: "cpu", label: "Sistemas", Icon: Cpu },
  { key: "circuit-board", label: "Eletrônica", Icon: CircuitBoard },
  { key: "factory", label: "Fábrica", Icon: Factory },
  { key: "cog", label: "Automação", Icon: Cog },
  { key: "bot", label: "Robótica", Icon: Bot },
  { key: "wrench", label: "Manutenção", Icon: Wrench },
  { key: "hammer", label: "Ferramentas", Icon: Hammer },
  { key: "hard-hat", label: "Engenharia", Icon: HardHat },
  { key: "flask-conical", label: "Laboratório", Icon: FlaskConical },
  { key: "gauge", label: "Metrologia", Icon: Gauge },
  { key: "ruler", label: "Medição", Icon: Ruler },
  { key: "shield-check", label: "Qualidade", Icon: ShieldCheck },
  { key: "warehouse", label: "Armazém", Icon: Warehouse },
  { key: "package", label: "Materiais", Icon: Package },
  { key: "boxes", label: "Estoque", Icon: Boxes },
  { key: "truck", label: "Logística", Icon: Truck },
  { key: "car", label: "Veículos", Icon: Car },
  { key: "zap", label: "Energia", Icon: Zap },
  { key: "fan", label: "Climatização", Icon: Fan },
  { key: "leaf", label: "Sustentabilidade", Icon: Leaf },
  { key: "radio", label: "Telecom", Icon: Radio },
  { key: "calculator", label: "Financeiro", Icon: Calculator },
  { key: "heart-handshake", label: "RH", Icon: HeartHandshake },
  { key: "clipboard-list", label: "Processos", Icon: ClipboardList },
  { key: "landmark", label: "Institucional", Icon: Landmark },
  { key: "briefcase", label: "Negócios", Icon: Briefcase },
];

/** @deprecated use LUCIDE_ICON_CATALOG */
export const COST_CENTER_ICON_CATALOG = LUCIDE_ICON_CATALOG;

const BY_KEY = new Map(LUCIDE_ICON_CATALOG.map((item) => [item.key, item]));

export function resolveLucideIcon(
  iconKey?: string | null,
  fallback: LucideIcon = Tags,
): LucideIcon {
  if (!iconKey) return fallback;
  return BY_KEY.get(iconKey)?.Icon ?? fallback;
}

export function resolveCostCenterIcon(iconKey?: string | null): LucideIcon {
  return resolveLucideIcon(iconKey, Building2);
}

export function resolveCapexCategoryIcon(iconKey?: string | null): LucideIcon {
  return resolveLucideIcon(iconKey, Tags);
}
