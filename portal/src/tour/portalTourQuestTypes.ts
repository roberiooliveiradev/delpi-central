export type PortalTourQuestScope =
  | "sidebar"
  | "launcher"
  | "home"
  | "notifications"
  | "profile"
  | "privacy"
  | "admin";

export type PortalTourQuestCategory =
  | "apps"
  | "home"
  | "notifications"
  | "profile"
  | "privacy"
  | "personalization"
  | "admin";

export type PortalTourQuest = {
  id: string;
  title: string;
  hint: string;
  steps: string[];
  unlockHint?: string;
  actionSelector: string;
  highlightSelector?: string;
  scope: PortalTourQuestScope;
  category: PortalTourQuestCategory;
  optional?: boolean;
  /** XP simbólico ao concluir (padrão: 10 obrigatório, 5 opcional). */
  xpReward?: number;
  isAvailable?: () => boolean;
};

export type PortalTourQuestContext = {
  canAccessAdmin: boolean;
};

export const PORTAL_TOUR_CATEGORY_LABELS: Record<
  PortalTourQuestCategory,
  string
> = {
  apps: "Apps e favoritos",
  home: "Página inicial",
  notifications: "Notificações",
  profile: "Perfil e RBAC",
  privacy: "Privacidade",
  personalization: "Personalização",
  admin: "Administração",
};

export const PORTAL_TOUR_CATEGORY_ORDER: PortalTourQuestCategory[] = [
  "apps",
  "home",
  "notifications",
  "profile",
  "privacy",
  "personalization",
  "admin",
];
