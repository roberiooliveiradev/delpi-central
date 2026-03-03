// src/components/ProductsRevenueChart.tsx

import React, { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { Product } from "../data/delpiApi";

interface Props {
  products: Product[];
}

export const ProductsRevenueChart: React.FC<Props> = ({
  products,
}) => {
  // 🔥 useMemo evita recalcular a cada render desnecessário
  const chartData = useMemo(() => {
    return products.map((p) => ({
      name: p.description,
      price: Number(p.sale_price ?? 0),
    }));
  }, [products]);

  return (
    <div style={{ height: 400 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="name"
            tick={{ fontSize: 12 }}
            interval={0}
            angle={-25}
            textAnchor="end"
            height={70}
          />

          <YAxis />
            <Tooltip
              formatter={(value) => {
                const numericValue =
                  typeof value === "number"
                    ? value
                    : Number(value ?? 0);

                return new Intl.NumberFormat("pt-BR", {
                  style: "currency",
                  currency: "BRL",
                }).format(numericValue);
              }}
            />
          <Bar dataKey="price" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};