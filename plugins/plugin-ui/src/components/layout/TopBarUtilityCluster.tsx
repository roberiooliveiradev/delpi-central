import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type TopBarUtilityClusterClassNames = {
  root: string;
};

export type TopBarUtilityClusterProps = {
  children: ReactNode;
  classNames: TopBarUtilityClusterClassNames;
  className?: string;
};

export function topBarUtilityClusterBemClasses(prefix: string): TopBarUtilityClusterClassNames {
  return {
    root: delpiUiClass(`${prefix}-topbar-utility`, "delpi-ui-topbar-utility"),
  };
}

/** Agrupa Buscar + Favoritos no slot secondary da TopBar. */
export function TopBarUtilityCluster({
  children,
  classNames,
  className,
}: TopBarUtilityClusterProps) {
  return <div className={[classNames.root, className].filter(Boolean).join(" ")}>{children}</div>;
}

export type DashboardTopBarUtilityClusterProps = Omit<TopBarUtilityClusterProps, "classNames">;

export function createDashboardTopBarUtilityCluster(config: { prefix: string }) {
  const classNames = topBarUtilityClusterBemClasses(config.prefix);
  return function DashboardTopBarUtilityCluster(props: DashboardTopBarUtilityClusterProps) {
    return <TopBarUtilityCluster classNames={classNames} {...props} />;
  };
}
