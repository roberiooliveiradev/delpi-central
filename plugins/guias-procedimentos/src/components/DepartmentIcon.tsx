import { BookOpen } from "lucide-react";

import { resolveLucideIcon } from "../utils/lucideIcons.ts";

type DepartmentIconProps = {
  /** Identificador Lucide em kebab-case (ex.: book-open). */
  icon: string;
  size?: number;
};

export function DepartmentIcon({
  icon,
  size = 28,
}: DepartmentIconProps) {
  const Icon = resolveLucideIcon(icon) ?? BookOpen;
  return <Icon size={size} strokeWidth={1.75} aria-hidden="true" />;
}
