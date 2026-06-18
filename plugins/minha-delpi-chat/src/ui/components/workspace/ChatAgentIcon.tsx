import {
  Bot,
  Box,
  Brain,
  ChartLine,
  MessageSquare,
  Search,
  Shield,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  DEFAULT_AGENT_ICON,
  normalizeAgentIcon,
  type AgentIconName,
} from "./chatAgentIcon";

import "./ChatAgentIcon.css";

const AGENT_ICON_COMPONENTS: Record<AgentIconName, LucideIcon> = {
  bot: Bot,
  sparkles: Sparkles,
  brain: Brain,
  "message-square": MessageSquare,
  search: Search,
  "chart-line": ChartLine,
  shield: Shield,
  zap: Zap,
  box: Box,
  users: Users,
};

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
  const Icon = AGENT_ICON_COMPONENTS[iconName] ?? AGENT_ICON_COMPONENTS[DEFAULT_AGENT_ICON];

  return <Icon size={size} className={className} aria-hidden="true" />;
}
