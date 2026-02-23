// src/components/PaginationControls.tsx

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
    <div style={{ display: "flex", gap: 10, marginTop: 15 }}>
      <button onClick={onPrev} disabled={page <= 1}>
        ◀ Anterior
      </button>

      <span>
        Página {page} de {totalPages}
      </span>

      <button onClick={onNext} disabled={page >= totalPages}>
        Próxima ▶
      </button>
    </div>
  );
};