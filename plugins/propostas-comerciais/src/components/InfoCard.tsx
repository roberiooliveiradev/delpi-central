import type { ReactNode } from "react";

import { createInfoGrid, createPanelCard } from "@delpi/plugin-ui/index";

const PanelCard = createPanelCard("pc");

type InfoCardProps = {
  title: string;
  children: ReactNode;
  highlight?: boolean;
};

export function InfoCard({ title, children, highlight = false }: InfoCardProps) {
  return (
    <PanelCard title={title} highlight={highlight}>
      {children}
    </PanelCard>
  );
}

export const InfoGrid = createInfoGrid("pc");
