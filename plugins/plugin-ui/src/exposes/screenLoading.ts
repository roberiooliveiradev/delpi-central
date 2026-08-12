/**
 * Expose MF leve — só ScreenLoading (splash do public-hub).
 * Evita carregar `./index` (TipTap/recharts) e o crash `useMemo is not a function`.
 */
export {
  ScreenLoading,
  screenLoadingBemClasses,
  createDashboardScreenLoading,
  type ScreenLoadingClassNames,
  type ScreenLoadingProps,
  type ScreenLoadingTone,
  type ScreenLoadingVariant,
} from "../components/feedback/ScreenLoading";
