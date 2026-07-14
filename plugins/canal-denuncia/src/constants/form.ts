export const MIN_DESCRIPTION_LENGTH = 10;
export const MAX_DESCRIPTION_LENGTH = 8000;

export const SUCCESS_MESSAGE =
  "Denúncia enviada com sucesso. A Ouvidoria recebeu seu relato para análise.";

export const ERROR_MESSAGE =
  "Não foi possível enviar a denúncia. Aguarde alguns instantes e tente novamente.";

export const PRIVACY_NOTICE =
  "Seu relato será enviado de forma anônima à Ouvidoria, sem nome, e-mail ou identificação pessoal no conteúdo da denúncia. A mensagem parte do remetente canal-denuncia@delpi.com.br — não do seu e-mail pessoal. Evite incluir no texto informações que possam identificá-lo caso deseje preservar sua identidade.";

export const RESPONSIBILITY_NOTICE =
  "Use este canal de forma responsável e forneça informações suficientes para que a Ouvidoria possa compreender o ocorrido.";

export const FLOW_STEPS = [
  {
    title: "Escreva o relato",
    description:
      "Descreva o ocorrido com clareza. Não é necessário informar nome ou e-mail.",
  },
  {
    title: "Envio anônimo",
    description:
      "Ao confirmar, o sistema registra o relato sem vínculo de identidade no conteúdo.",
  },
  {
    title: "E-mail da Ouvidoria",
    description:
      "A notificação sai de canal-denuncia@delpi.com.br para ouvidoria@delpi.com.br.",
  },
  {
    title: "Análise responsável",
    description:
      "A Ouvidoria analisa o caso com sigilo e trata o relato de forma adequada.",
  },
] as const;
