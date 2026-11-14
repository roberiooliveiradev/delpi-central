/** Fixtures de teste do questionário oficial (espelha o contrato da commercial-api). */
const DIMENSION_KEYS = [
  "quality",
  "delivery_deadline",
  "service",
  "agility",
  "communication",
  "technical_support",
  "commercial_support",
  "flexibility",
  "reliability",
  "partnership",
] as const;

export function rawQuestionnaire(): Record<string, unknown> {
  const dimensions = DIMENSION_KEYS.map((key, index) => ({
    order: index + 1,
    key,
    title: key,
    prompt: `Pergunta ${index + 1} (${key})`,
    kind: "dimension",
    allows_not_applicable: true,
    required: true,
    scale_min: 1,
    scale_max: 5,
  }));
  return {
    questionnaire_version: "test-v1",
    scale_1_5_labels: {
      "1": "Muito insatisfeito",
      "2": "Insatisfeito",
      "3": "Neutro",
      "4": "Satisfeito",
      "5": "Muito satisfeito",
    },
    items: [
      ...dimensions,
      {
        order: 11,
        key: "overall_score",
        title: "Satisfação geral",
        prompt: "Pergunta 11 (geral)",
        kind: "overall",
        allows_not_applicable: false,
        required: true,
        scale_min: 1,
        scale_max: 5,
      },
      {
        order: 12,
        key: "recommendation_score",
        title: "Recomendação",
        prompt: "Pergunta 12 (recomendação)",
        kind: "recommendation",
        allows_not_applicable: false,
        required: true,
        scale_min: 0,
        scale_max: 10,
      },
      ...(["strengths", "improvements", "unmet_needs"] as const).map((key, index) => ({
        order: 13 + index,
        key,
        title: key,
        prompt: `Pergunta ${13 + index} (${key})`,
        kind: "open",
        allows_not_applicable: false,
        required: false,
      })),
    ],
  };
}
