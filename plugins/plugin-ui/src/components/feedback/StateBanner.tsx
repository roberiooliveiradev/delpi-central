import type { ReactNode } from "react";

export type StateBannerVariant = "default" | "error" | "success";

export type StateBannerClassNames = {
  root: string;
  error: string;
  success: string;
};

export type StateBannerProps = {
  children: ReactNode;
  variant?: StateBannerVariant;
  className?: string;
  classNames: StateBannerClassNames;
};

export function stateBannerBemClasses(prefix: string): StateBannerClassNames {
  const root = `${prefix}-state`;
  return {
    root,
    error: `${root} ${root}--error`,
    success: `${root} ${root}--success`,
  };
}

export const stateBannerKaizenClasses = stateBannerBemClasses;

function resolveStateBannerClass(
  variant: StateBannerVariant,
  classNames: StateBannerClassNames,
  className?: string,
): string {
  const base =
    variant === "error"
      ? classNames.error
      : variant === "success"
        ? classNames.success
        : classNames.root;

  return [base, className].filter(Boolean).join(" ");
}

/** Banner inline de feedback (carregando, erro, sucesso). */
export function StateBanner({
  children,
  variant = "default",
  className,
  classNames,
}: StateBannerProps) {
  return (
    <div className={resolveStateBannerClass(variant, classNames, className)}>{children}</div>
  );
}

export type DashboardStateBannerProps = Omit<StateBannerProps, "classNames">;

export function createDashboardStateBanner(config: { classNames: StateBannerClassNames }) {
  return function DashboardStateBanner(props: DashboardStateBannerProps) {
    return <StateBanner classNames={config.classNames} {...props} />;
  };
}
