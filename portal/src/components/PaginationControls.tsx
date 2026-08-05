// src/components/PaginationControls.tsx

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "../ui-kit";

type Props = {
  page: number;
  totalPages: number;
  onNext: () => void;
  onPrev: () => void;
};

export const PaginationControls = ({
  page,
  totalPages,
  onNext,
  onPrev,
}: Props) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        marginTop: 15,
      }}
    >
      <Button
        size="sm"
        onClick={onPrev}
        disabled={page <= 1}
        icon={<ChevronLeft size={16} />}
      >
        Anterior
      </Button>

      <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
        Página {page} de {totalPages}
      </span>

      <Button size="sm" onClick={onNext} disabled={page >= totalPages}>
        Próxima
        <ChevronRight size={16} />
      </Button>
    </div>
  );
};
