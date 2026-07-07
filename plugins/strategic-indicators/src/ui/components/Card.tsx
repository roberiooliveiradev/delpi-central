import { createContentCard } from "@delpi/plugin-ui";

import "./Card.css";

export const Card = createContentCard("si", { titleLevel: 3 });

export type { DashboardContentCardProps as CardProps } from "@delpi/plugin-ui";
