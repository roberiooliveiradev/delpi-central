import { Bot } from "lucide-react";

import { DEFAULT_AGENT_ICON, normalizeAgentIcon } from "./chatAgentIcon";
import { resolveLucideIcon } from "../../utils/lucideIconResolver";

import "./ChatAgentIcon.css";

type ChatAgentIconProps = {
  icon?: string | null;
  size?: number;
  className?: string;
};

export function ChatAgentIcon({
  icon,
  size = 15,
  className,
}: ChatAgentIconProps) {
  const iconName = normalizeAgentIcon(icon);
  const Icon = resolveLucideIcon(iconName) ?? resolveLucideIcon(DEFAULT_AGENT_ICON) ?? Bot;

  return <Icon size={size} className={className} aria-hidden="true" />;
}
