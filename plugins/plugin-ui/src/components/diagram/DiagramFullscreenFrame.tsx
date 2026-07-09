import type { ReactNode } from "react";

import { DiagramLayoutProvider } from "./DiagramLayoutContext";

type Props = {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  enabled?: boolean;
};

/** Área de trabalho do diagrama — layout inline (sem modal de tela cheia). */
export function DiagramFullscreenFrame({ children }: Props) {
  return (
    <DiagramLayoutProvider layout="default">
      <div className="tm-diagram-workspace">
        <div className="tm-diagram-workspace__body">{children}</div>
      </div>
    </DiagramLayoutProvider>
  );
}
