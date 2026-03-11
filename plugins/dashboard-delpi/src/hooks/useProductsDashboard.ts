// src/hooks/useProductsDashboard.ts

import { useEffect, useState } from "react"
import { DelpiApi } from "../data/delpiApi"
import type { Product } from "../data/delpiApi"

export function useProductsDashboard(api: DelpiApi) {

  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  const [filters, setFilters] = useState({
    code: "",
    group: "",
    description: ""
  })

  const [sort, setSort] = useState<{
    sort?: string
    direction?: "asc" | "desc"
  }>({
    sort: "code",
    direction: "asc"
  })

  useEffect(() => {

    const load = async () => {

      try {

        setLoading(true)

        const res = await api.searchProducts({
          page,
          pageSize,
          code: filters.code || undefined,
          group: filters.group || undefined,
          description: filters.description || undefined,
          sort: sort.sort,
          direction: sort.direction
        })

        const data = res.data

        setProducts(data.items)
        setTotal(data.total)
        setTotalPages(data.total_pages)

      } catch (err) {

        console.error(err)

      } finally {

        setLoading(false)

      }

    }

    load()

  }, [page, pageSize, filters, sort])

  return {
    products,
    loading,

    page,
    pageSize,
    total,
    totalPages,

    setPage,
    setPageSize,

    filters,
    setFilters,

    sort,
    setSort
  }
}