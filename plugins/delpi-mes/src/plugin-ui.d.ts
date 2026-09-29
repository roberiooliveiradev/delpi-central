declare module "@delpi/plugin-ui/index" {
  import type { ReactNode } from "react";

  export type EmptyStateClassNames = { root: string; withTitle: boolean };
  export function emptyStatePanelBemClasses(prefix: string): EmptyStateClassNames;
  export function EmptyState(props: {
    title?: string;
    message?: string;
    classNames: EmptyStateClassNames;
    defaultTitle?: string;
    defaultMessage: string;
    children?: ReactNode;
    role?: "status" | "alert";
  }): ReactNode;
}
