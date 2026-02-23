// src/ui/icons/lucide.ts

import * as LucideIcons from "lucide-react";
import type { LucideProps } from "lucide-react";

type LucideIconComponent = React.FC<LucideProps>;

/**
 * Resolve um nome (string) para o componente do Lucide.
 * - Se não existir, cai num fallback seguro.
 */
export function getLucideIcon(name?: string | null): LucideIconComponent {
  const fallback = (LucideIcons as any).Package as LucideIconComponent;

  if (!name) return fallback;

  const Icon = (LucideIcons as any)[name] as LucideIconComponent | undefined;
  return Icon ?? fallback;
}