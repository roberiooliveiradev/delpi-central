import type { ReactNode } from "react";

type PageTransitionProps = {
  transitionKey: string;
  children: ReactNode;
};

export function PageTransition({ transitionKey, children }: PageTransitionProps) {
  return (
    <div key={transitionKey} className="dm-page-transition">
      {children}
    </div>
  );
}
