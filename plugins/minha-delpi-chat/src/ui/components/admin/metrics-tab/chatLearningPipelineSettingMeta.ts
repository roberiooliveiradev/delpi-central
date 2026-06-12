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
    description: "Termos internos, confirmação, indexação RAG e pesquisa web.",
  },
  {
    id: "evaluation",
    title: "Regressão e promoção",
    description: "Casos de avaliação e bloqueio de promoção sem teste.",
  },
  {
    id: "finetuning",
    title: "Ajuste fino offline",
    description: "Captura de amostras positivas para datasets de fine-tuning.",
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
  | "learningTermConfirmationEnabled"
  | "learningGlossaryWebMeaning"
  | "learningGlossaryRagIndex"
  | "learningEvaluationEnabled"
  | "learningEvaluationBlockPromotion"
  | "learningEvaluationCaptureFromFeedback"
  | "learningFineTuningEnabled"
  | "learningFineTuningCapturePositiveFeedback",
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
  learningGlossaryWebMeaning: {
    title: "Significado via busca web",
    summary: "Pesquisa definição pública quando o termo é desconhecido internamente.",
    pros: ["Acelera glossário para siglas e conceitos de mercado."],
    cons: ["Depende de web search; significado pode ser genérico."],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "neutral",
    tip: "Webhook e limites de busca continuam no Docker.",
  },
  learningGlossaryRagIndex: {
    title: "Indexar glossário no RAG",
    summary: "Embute termos aprovados na base de conhecimento recuperável.",
    pros: ["Termos promovidos entram na busca híbrida."],
    cons: ["Reindexação adiciona carga no Postgres."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningEvaluationEnabled: {
    title: "Casos de regressão",
    summary: "Habilita criação e execução de casos na aba Regressão.",
    pros: ["Detecta quebra de roteamento após mudanças."],
    cons: ["Exige manutenção da suíte de casos."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningEvaluationBlockPromotion: {
    title: "Bloquear promoção sem regressão",
    summary: "Impede promover candidato se casos relacionados falharem.",
    pros: ["Evita vocabulário ruim em produção."],
    cons: ["Promoções manuais podem travar até corrigir casos."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningEvaluationCaptureFromFeedback: {
    title: "Captura de casos via feedback",
    summary: "Grava pergunta como caso de regressão em feedback negativo.",
    pros: ["Suíte cresce com falhas reais."],
    cons: ["Pode poluir regressão com perguntas one-off."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  learningFineTuningEnabled: {
    title: "Pipeline de ajuste fino",
    summary: "Permite captura e datasets para treino offline.",
    pros: ["Base para modelo especializado da empresa."],
    cons: ["Infra de treino (webhook, Ollama) fica no Docker."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "neutral",
  },
  learningFineTuningCapturePositiveFeedback: {
    title: "Captura em feedback positivo",
    summary: "Salva par pergunta/resposta quando o usuário aprova a resposta.",
    pros: ["Amostras de alta qualidade para fine-tuning."],
    cons: ["Volume baixo; requer curadoria na aba Ajuste fino."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "neutral",
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
