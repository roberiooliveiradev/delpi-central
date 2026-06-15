import type { EficienciaFabrilEfficiencyBand } from "../constants/efficiencyBands";
import type { EficienciaFabrilShift } from "../constants/shifts";
import type { AppointmentsSortColumn, SortDirection } from "../utils/appointmentsTableSort";

export type EficienciaFabrilFilterParams = {
  date_start: string;
  date_end: string;
  branch?: string;
  ops?: string[];
  employees?: string[];
  work_centers?: string[];
  shifts?: EficienciaFabrilShift[];
  efficiency_bands?: EficienciaFabrilEfficiencyBand[];
  status_ok_only?: boolean;
  sort_by?: AppointmentsSortColumn;
  sort_dir?: SortDirection;
  page?: number;
  page_size?: number;
};

export type EficienciaFabrilSummary = {
  weighted_efficiency_pct: number | null;
  total_mod_result: number | null;
  total_mod_profit: number | null;
  total_mod_loss: number | null;
  total_hours_gained_lost: number | null;
  /** Total de apontamentos exibidos na tabela (filtros aplicados). */
  table_appointment_count: number;
  /** Apontamentos com eficiência acima do limite (status Verificar na tabela). */
  verify_appointment_count: number;
  /** Apontamentos na faixa válida com eficiência abaixo de 50%. */
  low_efficiency_appointment_count: number;
};

export type EfficiencyByDay = {
  date: string;
  efficiency_pct: number | null;
  appointment_count: number;
};

export type ModResultByDay = {
  date: string;
  profit: number | null;
  loss: number | null;
  net_result: number | null;
};

export type EfficiencyByOperator = {
  operator_name: string | null;
  operator_code: string | null;
  operator_login: string | null;
  efficiency_pct: number | null;
  appointment_count: number;
  mod_result: number | null;
};

export type HoursByWorkCenter = {
  work_center: string | null;
  real_hours: number | null;
  planned_hours: number | null;
  appointment_count: number;
};

export type EfficiencyByWorkCenter = {
  work_center: string | null;
  efficiency_pct: number | null;
  appointment_count: number;
};

export type ModResultByWorkCenter = {
  work_center: string | null;
  mod_result: number | null;
  appointment_count: number;
};

export type EficienciaFabrilCharts = {
  efficiency_by_day: EfficiencyByDay[];
  mod_result_by_day: ModResultByDay[];
  efficiency_by_operator: EfficiencyByOperator[];
  efficiency_by_work_center: EfficiencyByWorkCenter[];
  mod_result_by_work_center: ModResultByWorkCenter[];
  hours_by_work_center: HoursByWorkCenter[];
};

export type EficienciaFabrilItem = {
  appointment_id?: number | null;
  filial: string | null;
  op: string | null;
  produto: string | null;
  descricao_produto: string | null;
  centro_trabalho: string | null;
  operacao: string | null;
  cod_operador: string | null;
  login_operador: string | null;
  nome_operador: string | null;
  data_producao: string | null;
  hora_inicio: string | null;
  hora_final: string | null;
  qtd_apontada: number | null;
  unidade: string | null;
  tempo_real_horas: number | null;
  tempo_previsto_horas: number | null;
  eficiencia_percentual: number | null;
  valor_mod_hora: number | null;
  tempo_ganho_perdido_horas: number | null;
  resultado_mod: number | null;
  lucro_mod: number | null;
  prejuizo_mod: number | null;
  status_resultado_mod: string | null;
  status_registro: string | null;
};

export type EficienciaFabrilPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type EficienciaFabrilDashboardData = {
  summary: EficienciaFabrilSummary;
  charts: EficienciaFabrilCharts;
  items: EficienciaFabrilItem[];
  pagination: EficienciaFabrilPagination;
};
