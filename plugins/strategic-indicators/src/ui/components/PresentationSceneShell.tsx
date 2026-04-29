import type { ReactNode } from "react";
import "./PresentationSceneShell.css";

type PresentationMode = "meeting" | "tv" | "slide";

type PresentationSceneShellProps = {
  mode: PresentationMode;
  children: ReactNode;
};

export function PresentationSceneShell({
  mode,
  children,
}: PresentationSceneShellProps) {
  return (
    <section
      className={`si-presentation-scene-shell si-presentation-scene-shell--${mode}`}
    >
      <div className="si-presentation-scene-shell__inner">{children}</div>
    </section>
  );
}