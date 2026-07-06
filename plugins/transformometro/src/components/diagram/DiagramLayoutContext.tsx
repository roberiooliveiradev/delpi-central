import { createContext, useContext } from "react";

export type DiagramEditorLayout = "default" | "fill";

const DiagramLayoutContext = createContext<DiagramEditorLayout>("default");

export function DiagramLayoutProvider({
  layout,
  children,
}: {
  layout: DiagramEditorLayout;
  children: React.ReactNode;
}) {
  return (
    <DiagramLayoutContext.Provider value={layout}>{children}</DiagramLayoutContext.Provider>
  );
}

export function useDiagramEditorLayout(): DiagramEditorLayout {
  return useContext(DiagramLayoutContext);
}
