import type { AdminBundleNumberMeta, AdminBundleSectionMeta } from "./ChatAdminBundleSettingsPanel";
import type { ChatIntelligenceSettingMeta } from "./chatIntelligenceSettingMeta";

export const CHAT_LEARNING_PIPELINE_SECTIONS: AdminBundleSectionMeta[] = [
  {
    id: "master",
    title: "Pipeline de aprendizagem",
    description: "Interruptor geral e captura de sinais do usuário.",
  },
  {
    id: "typing",
    title: "Correção de digitação",
    description: "Sugestões antes do envio e fuzzy match no vocabulário aprendido.",
  },
  {
    id: "glossary",
    title: "Glossário vivo",
    description: "Termos internos, confirmação e injeção no contexto do turno.",
  },
];

export const CHAT_LEARNING_PIPELINE_TOGGLE_META: Record<
  | "learningEnabled"
  | "typingCorrectionEnabled"
  | "typingCorrectionFuzzyEnabled"
  | "learningApplyVocabulary"
  | "learningCaptureFromFeedback"
  | "learningCaptureFromTurn"
  | "learningAutoApproveEnabled"
  | "learningGlossaryRetrieval"
  | "learningGlossaryCapture"
  | "learningTermConfirmationEnabled",
  ChatIntelligenceSettingMeta
> = {
  learningEnabled: {
    title: "Aprendizagem contínua",
    summary: "Habilita captura, vocabulário e glossário derivados do uso real.",
    pros: ["O chat evolui com correções e termos da empresa."],
    cons: ["Exige revisão na admin de candidatos e vocabulário."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
    tip: "Desligar congela o pipeline; dados já promovidos permanecem.",
  },
  typingCorrectionEnabled: {
    title: "Correção de digitação",
    summary: "Sugere correções antes de enviar a mensagem (endpoint /meta).",
    pros: ["Reduz erros de SKU e siglas internas."],
    cons: ["Chamada extra na digitação; pode sugerir termo errado."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  typingCorrectionFuzzyEnabled: {
    title: "Fuzzy no léxico de correção",
    summary: "Aceita pequenos typos via distância de edição no vocabulário fixo.",
    pros: ["Captura variações como fabrril → fabril."],
    cons: ["Pode corrigir para palavra parecida mas incorreta."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "neutral",
  },
  learningApplyVocabulary: {
    title: "Aplicar vocabulário aprendido",
    summary: "Normaliza a mensagem do usuário com regras já aprovadas.",
    pros: ["Melhora roteamento e busca com jargão interno."],
    cons: ["Regra ruim aprovada distorce intenção até ser revertida."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningCaptureFromFeedback: {
    title: "Captura via feedback negativo",
    summary: "Cria candidatos quando o usuário marca resposta ruim.",
    pros: ["Sinal forte de gap de entendimento."],
    cons: ["Volume alto exige triagem na aba Candidatos."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningCaptureFromTurn: {
    title: "Captura no turno",
    summary: 'Detecta definições explícitas ("quando eu falar X é Y").',
    pros: ["Aprende glossário sem passar pelo feedback."],
    cons: ["Falsos positivos em frases coloquiais."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningAutoApproveEnabled: {
    title: "Auto-aprovação de candidatos",
    summary: "Promove automaticamente candidatos de baixo risco e alta confiança.",
    pros: ["Menos fila manual para typos óbvios."],
    cons: ["Risco de promover normalização incorreta sem revisão."],
    speedWhenEnabled: "fast",
    qualityWhenEnabled: "lower",
    tip: "Use com confiança mínima alta (ex.: 0,95).",
  },
  learningGlossaryRetrieval: {
    title: "Injetar glossário no contexto",
    summary: "Busca termos aprendidos relevantes à mensagem antes do LLM.",
    pros: ["Respostas alinhadas ao vocabulário da empresa."],
    cons: ["Termos errados no glossário contaminam o prompt."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningGlossaryCapture: {
    title: "Captura de termos para glossário",
    summary: 'Detecta perguntas "o que é X?" e novos termos desconhecidos.',
    pros: ["Constrói base de significados internos."],
    cons: ["Perguntas genéricas podem gerar ruído."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningTermConfirmationEnabled: {
    title: "Confirmação de termo desconhecido",
    summary: "Pede confirmação ao usuário antes de registrar significado novo.",
    pros: ["Evita gravar termo errado sem validação humana."],
    cons: ["Mais um passo na conversa."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
};

export const CHAT_LEARNING_PIPELINE_NUMBER_META: Record<
  "learningAutoApproveMinConfidence",
  AdminBundleNumberMeta
> = {
  learningAutoApproveMinConfidence: {
    title: "Confiança mínima para auto-aprovação",
    summary: "Só candidatos com score ≥ este valor são auto-aprovados (0 a 1).",
    pros: ["Reduz promoções arriscadas."],
    cons: ["Valor alto deixa mais itens na fila manual."],
    speedNote: "Não altera latência do chat.",
    qualityNote: "Valor maior = menos erros promovidos automaticamente.",
    min: 0.5,
    max: 1,
    step: 0.01,
  },
};
