import { httpPostJson } from "./httpClient";

const DENUNCIAS_URL = "/apps/api-delpi/canal-denuncia/denuncias";

export type CreateAnonymousDenunciaResult = {
  id: string;
  createdAt: string;
};

export async function createAnonymousDenuncia(input: {
  description: string;
}): Promise<CreateAnonymousDenunciaResult> {
  return httpPostJson<CreateAnonymousDenunciaResult>(DENUNCIAS_URL, {
    description: input.description,
  });
}
