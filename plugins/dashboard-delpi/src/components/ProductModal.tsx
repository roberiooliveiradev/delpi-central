// src/components/ProductModal.tsx
interface Props {
  product: any
  onClose: () => void
}

function formatLabel(key: string) {

  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, l => l.toUpperCase())

}

export const ProductModal: React.FC<Props> = ({
  product,
  onClose
}) => {

  if (!product) return null

  return (

    <div style={overlayStyle}>

      <div style={modalStyle}>

        <h2>{product.description}</h2>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2,1fr)",
            gap: 12
          }}
        >

          {Object.entries(product)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([key, value]) => {

              if (!value) return null

              return (
                <div key={key}>
                  <strong>{formatLabel(key)}:</strong> {String(value)}
                </div>
              )

            })}

        </div>

        <button onClick={onClose}>Fechar</button>

      </div>

    </div>
  )
}

const overlayStyle = {
  position: "fixed" as const,
  inset: 0,
  background: "rgba(0,0,0,0.5)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center"
}

const modalStyle = {
  background: "#fff",
  padding: 24,
  borderRadius: 8,
  width: 700,
  maxHeight: "80vh",
  overflow: "auto"
}