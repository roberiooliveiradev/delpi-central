import {
  BadgeCheck,
  BarChart3,
  ClipboardList,
  Factory,
  Folder,
  Lightbulb,
  Microscope,
  Package,
  Target,
  Wrench,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  DEFAULT_PROJECT_ICON,
  normalizeProjectIcon,
  type ProjectIconName,
} from "./chatProjectIcon";

import "./ChatProjectIcon.css";

const PROJECT_ICON_COMPONENTS: Record<ProjectIconName, LucideIcon> = {
  folder: Folder,
  "bar-chart-3": BarChart3,
  factory: Factory,
  microscope: Microscope,
  "badge-check": BadgeCheck,
  target: Target,
  package: Package,
  lightbulb: Lightbulb,
  wrench: Wrench,
  "clipboard-list": ClipboardList,
};

type ChatProjectIconProps = {
  icon?: string | null;
  size?: number;
  className?: string;
};

export function ChatProjectIcon({
  icon,
  size = 15,
  className,
}: ChatProjectIconProps) {
  const iconName = normalizeProjectIcon(icon);
  const Icon = PROJECT_ICON_COMPONENTS[iconName] ?? PROJECT_ICON_COMPONENTS[DEFAULT_PROJECT_ICON];

  return <Icon size={size} className={className} aria-hidden="true" />;
}
