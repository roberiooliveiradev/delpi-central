import type { ReactNode } from "react";

type PageTransitionProps = {
  transitionKey: string;
  children: ReactNode;
};

/** Re-monta o conteúdo ao trocar rota e dispara animação de entrada. */
export function PageTransition({ transitionKey, children }: PageTransitionProps) {
  return (
    <div key={transitionKey} className="tm-page-transition">
      {children}
    </div>
  );
}
