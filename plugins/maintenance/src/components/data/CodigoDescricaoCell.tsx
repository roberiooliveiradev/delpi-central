type CodigoDescricaoCellProps = {
  codigo: string;
  descricao?: string | null;
};

export function CodigoDescricaoCell({ codigo, descricao }: CodigoDescricaoCellProps) {
  const label = descricao?.trim();
  if (!label || label === codigo.trim()) {
    return <span>{codigo}</span>;
  }

  return (
    <span className="dm-datatable__codigo-descricao">
      <span className="dm-datatable__codigo-descricao__codigo">{codigo}</span>
      <span className="dm-datatable__codigo-descricao__descricao">{label}</span>
    </span>
  );
}
