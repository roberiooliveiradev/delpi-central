export type CulturaDelpiContent = {
  proposito: string;
  missao: string;
  visao: string;
  valores: string[];
  updatedAt: string | null;
  updatedByUserId: string | null;
  updatedByName: string | null;
};

export type UpdateCulturaDelpiContentPayload = {
  proposito: string;
  missao: string;
  visao: string;
  valores: string[];
};
