import { DiagramLayoutProvider } from "./DiagramLayoutContext";

type Props = {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  enabled?: boolean;
};

/** Área de trabalho do diagrama — layout expandido inline (sem modal de tela cheia). */
export function DiagramFullscreenFrame({ children }: Props) {
  return (
    <DiagramLayoutProvider layout="fill">
      <div className="tm-diagram-workspace tm-diagram-workspace--embedded">
        <div className="tm-diagram-workspace__body">{children}</div>
      </div>
    </DiagramLayoutProvider>
  );
}
