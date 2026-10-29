import { EngineeringLoadingActivityCard } from "../../../ui/engineeringUi";
import type {
  DashboardLoadingActivityCardProps,
  LoadingActivityCardTone,
  LoadingActivityCardVariant,
} from "@delpi/plugin-ui/index";

export type { LoadingActivityCardTone, LoadingActivityCardVariant };

/** Loading canônico do Portal Engenharia. */
export const LoadingActivityCard = EngineeringLoadingActivityCard;

export type LoadingActivityCardProps = DashboardLoadingActivityCardProps;
