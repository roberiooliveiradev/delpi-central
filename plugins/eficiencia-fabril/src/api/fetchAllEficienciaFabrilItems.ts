import type {
  EficienciaFabrilFilterParams,
  EficienciaFabrilItem,
} from "../types/eficienciaFabril";
import { getEficienciaFabrilAppointments } from "./eficienciaFabrilApi";

export type EficienciaFabrilListFilterParams = Omit<
  EficienciaFabrilFilterParams,
  "page" | "page_size"
>;

export async function fetchAllEficienciaFabrilItems(
  params: EficienciaFabrilListFilterParams,
  signal?: AbortSignal
): Promise<EficienciaFabrilItem[]> {
  return getEficienciaFabrilAppointments(params, signal);
}
