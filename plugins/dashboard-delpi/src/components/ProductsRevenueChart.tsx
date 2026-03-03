// src/components/ProductsRevenueChart.tsx

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { Product } from "../data/delpiApi";

interface Props {
  products: Product[];
}

export const ProductsRevenueChart: React.FC<Props> = ({
  products,
}) => {
  const chartData = products.map((p) => ({
    name: p.description,
    price: p.sale_price ?? 0,
  }));

  return (
    <div style={{ height: 400 }}>
      <ResponsiveContainer>
        <BarChart data={chartData}>
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12 }}
          />
          <YAxis />
          <Tooltip />
          <Bar dataKey="price" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};