interface Props {
  product: any;
  onClose: () => void;
}

export const ProductModal: React.FC<Props> = ({
  product,
  onClose,
}) => {
  if (!product) return null;

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <h2>{product.description}</h2>
        <p><strong>Código:</strong> {product.code}</p>
        <p><strong>Grupo:</strong> {product.group_code}</p>
        <p><strong>Tipo:</strong> {product.type}</p>
        <p><strong>Unidade:</strong> {product.unit}</p>

        <button onClick={onClose}>Fechar</button>
      </div>
    </div>
  );
};

const overlayStyle = {
  position: "fixed" as const,
  inset: 0,
  background: "rgba(0,0,0,0.5)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const modalStyle = {
  background: "#fff",
  padding: 24,
  borderRadius: 8,
  width: 500,
};