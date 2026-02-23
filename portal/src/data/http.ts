// src/data/http.ts

export type AnyPaginated<T> =
  | { data: T[]; pagination: any }                 // body direto
  | { data: { data: T[]; pagination: any } };      // axios-like

export function unwrapPaginated<T>(res: AnyPaginated<T> | any): T[] {
  // body direto: { data: [], pagination: {} }
  if (res?.data && Array.isArray(res.data) && res.pagination) return res.data;

  // axios-like: { data: { data: [], pagination: {} } }
  if (res?.data?.data && Array.isArray(res.data.data)) return res.data.data;

  return [];
}