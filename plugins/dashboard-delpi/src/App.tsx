// src/App.tsx
import { DelpiApi } from "./data/delpiApi";
import { useProductsDashboard } from "./hooks/useProductsDashboard";
import { ProductsRevenueChart } from "./components/ProductsRevenueChart";

interface Props {
  token: string;
}

function App({ token }: Props) {
  const api = new DelpiApi(token);
  const { products, loading } =
    useProductsDashboard(api);

  return (
    <div style={{ padding: 24 }}>
      <h1>Dashboard DELPI</h1>

      {loading ? (
        <div>Carregando dados...</div>
      ) : (
        <>
          <h3>Preço por Produto</h3>
          <ProductsRevenueChart products={products} />
        </>
      )}
    </div>
  );
}

export default App;