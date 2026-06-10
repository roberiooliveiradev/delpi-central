import type { LucideIcon } from "lucide-react";
import {
  Award,
  Bell,
  Compass,
  Grid3x3,
  Home,
  Lock,
  Palette,
  Pin,
  Shield,
  Sparkles,
  Star,
  Trophy,
  User,
} from "lucide-react";

const ACHIEVEMENT_ICONS: Record<string, LucideIcon> = {
  "category-apps": Grid3x3,
  "category-home": Home,
  "category-notifications": Bell,
  "category-profile": User,
  "category-privacy": Shield,
  "category-personalization": Palette,
  "category-admin": Shield,
  "quest-first-favorite": Star,
  "quest-pin-master": Pin,
  "milestone-25": Compass,
  "milestone-50": Award,
  "milestone-75": Sparkles,
  "tour-master": Trophy,
};

export function resolvePortalTourAchievementIcon(
  achievementId: string,
  unlocked: boolean,
): LucideIcon {
  if (!unlocked) return Lock;
  return ACHIEVEMENT_ICONS[achievementId] ?? Award;
}
