import { Clock, ShieldCheck } from "lucide-react";
import { useState, type ReactNode } from "react";

import { PUC_PREFIX } from "../../app/bemPrefix";
import { ActionButton } from "../../components/actions/ActionButton";
import {
  FormCard,
  FormHeaderCard,
  FormIntroCard,
  FormButton,
  FormLogo,
  FormNotice,
  FormPageLayout,
  FormProgress,
  FormResultPanel,
  FormReviewSection,
  FormStepFooter,
  FormThemeToggle,
  NotApplicableOption,
  QuestionAnswerStack,
  QuestionCard,
  QuestionTextAnswer,
  QuestionnaireThemeScope,
  RatingScale,
  type RatingScaleValue,
} from "../../components/forms/questionnaire";
import type { CatalogEntryDraft } from "../types";

const P = PUC_PREFIX;

/** Logotipo neutro (losango) para as demos — qualquer `src` de imagem serve. */
const DEMO_LOGO =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 40"><rect x="2" y="4" width="32" height="32" rx="9" fill="#1f6feb"/><text x="44" y="26" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#1f2937">Marca</text></svg>`,
  );

const DEMO_LOGO_DARK =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 40"><rect x="2" y="4" width="32" height="32" rx="9" fill="#1f6feb"/><text x="44" y="26" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#111827">Marca</text></svg>`,
  );

function DemoLogo({ dark }: { dark?: boolean }) {
  return (
    <FormLogo
      src={dark ? DEMO_LOGO_DARK : DEMO_LOGO}
      alt="Marca"
      size="md"
      prefix={P}
    />
  );
}

/** Superfície temática para demos de cartão (sem a página inteira). */
function Swatch({
  scheme,
  children,
}: {
  scheme: "auto" | "light" | "dark";
  children: ReactNode;
}) {
  return (
    <QuestionnaireThemeScope prefix={P} colorScheme={scheme}>
      <div className="puc-questionnaire-surface">{children}</div>
    </QuestionnaireThemeScope>
  );
}

/** Par claro × escuro lado a lado. */
function ThemedPair({ children }: { children: (dark: boolean) => ReactNode }) {
  return (
    <div className="puc-questionnaire-pair">
      <Swatch scheme="light">{children(false)}</Swatch>
      <Swatch scheme="dark">{children(true)}</Swatch>
    </div>
  );
}

const SCALE_MEANINGS = [
  "Muito insatisfeito",
  "Insatisfeito",
  "Neutro",
  "Satisfeito",
  "Muito satisfeito",
];

const scaleLabel = (n: number) => `${n} — ${SCALE_MEANINGS[n - 1]}`;

/** Escala 1–5 controlada para as demos (estado local, sem persistência). */
function Scale15Demo({
  initial = null,
  invalid = false,
}: {
  initial?: RatingScaleValue;
  invalid?: boolean;
}) {
  const [value, setValue] = useState<RatingScaleValue>(initial);
  return (
    <RatingScale
      prefix={P}
      name={`demo-15-${String(invalid)}-${String(initial)}`}
      min={1}
      max={5}
      value={value}
      onChange={setValue}
      optionLabel={scaleLabel}
      endLabels={{ min: "1 · Muito insatisfeito", max: "5 · Muito satisfeito" }}
      selectionCaption={(n) => `Sua nota: ${n} · ${SCALE_MEANINGS[n - 1]}`}
      notApplicable={{ label: "Não se aplica" }}
      invalid={invalid}
    />
  );
}

/** Escala 0–10 controlada (legenda acima, sem N/A). */
function Scale010Demo() {
  const [value, setValue] = useState<RatingScaleValue>(null);
  return (
    <RatingScale
      prefix={P}
      name="demo-010"
      min={0}
      max={10}
      value={value}
      onChange={setValue}
      optionLabel={(n) => `Nota ${n}`}
      endLabels={{ min: "0 · Nada provável", max: "10 · Extremamente provável" }}
      endLabelsPosition="above"
      narrowColumns={6}
      selectionCaption={(n) => `Sua nota: ${n}`}
    />
  );
}

/** Campo aberto controlado. */
function TextAnswerDemo({ initial = "" }: { initial?: string }) {
  const [value, setValue] = useState(initial);
  return (
    <QuestionTextAnswer
      prefix={P}
      label="Sua resposta"
      placeholder="Escreva sua resposta"
      value={value}
      onChange={setValue}
      maxLength={500}
    />
  );
}

function Frame({ children }: { children: ReactNode }) {
  return (
    <div className="puc-questionnaire-frame">
      <QuestionnaireThemeScope prefix={P} colorScheme="auto">
        {children}
      </QuestionnaireThemeScope>
    </div>
  );
}

function PageSample() {
  return (
    <FormPageLayout prefix={P}>
      <FormCard prefix={P}>
        <strong>Cartão de exemplo</strong>
        <span>
          Conteúdo neutro do kit — superfícies, bordas e texto seguem os
          tokens do tema.
        </span>
        <FormThemeToggle ariaLabel="Alternar tema" prefix={P} />
      </FormCard>
    </FormPageLayout>
  );
}

export const questionnaireCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "forms.QuestionnaireThemeScope",
    family: "forms",
    exportName: "QuestionnaireThemeScope",
    title: "QuestionnaireThemeScope",
    description:
      "Raiz temática do kit de formulário: resolve auto/light/dark, aplica data-color-scheme e expõe o tema da visita (sem persistência).",
    docAnchor: "questionnaire-theme-scope-e-formpagelayout",
    propsSummary: ["colorScheme", "prefix", "className", "children"],
    demos: [
      {
        id: "auto",
        label: "auto + alternar",
        render: () => (
          <Frame>
            <PageSample />
          </Frame>
        ),
      },
      {
        id: "fixed",
        label: "claro × escuro fixos",
        render: () => (
          <div className="puc-questionnaire-pair">
            <Swatch scheme="light">
              <FormCard prefix={P}>Esquema claro fixo.</FormCard>
            </Swatch>
            <Swatch scheme="dark">
              <FormCard prefix={P}>Esquema escuro fixo.</FormCard>
            </Swatch>
          </div>
        ),
      },
    ],
  },
  {
    id: "forms.FormPageLayout",
    family: "forms",
    exportName: "FormPageLayout",
    title: "FormPageLayout",
    description:
      "Página do kit de formulário: faixa da marca (compact/tall) + coluna sobreposta (16 px / máx. 760 px), quebra em 600 px.",
    docAnchor: "questionnaire-theme-scope-e-formpagelayout",
    propsSummary: ["band", "prefix", "className", "children"],
    demos: [
      {
        id: "bands",
        label: "compact × tall",
        render: () => (
          <div className="puc-questionnaire-pair">
            <Frame>
              <FormPageLayout prefix={P} band="compact">
                <FormCard prefix={P}>Faixa compacta.</FormCard>
              </FormPageLayout>
            </Frame>
            <Frame>
              <FormPageLayout prefix={P} band="tall">
                <FormCard prefix={P}>Faixa alta.</FormCard>
              </FormPageLayout>
            </Frame>
          </div>
        ),
      },
    ],
  },
  {
    id: "forms.FormCard",
    family: "forms",
    exportName: "FormCard",
    title: "FormCard",
    description:
      "Cartão base do kit: superfície, borda, raio 12, sombra, padding fluido; tone invalid (borda danger) e as=fieldset para a pergunta.",
    docAnchor: "cartoes-do-kit-de-formulario",
    propsSummary: ["as", "tone", "prefix", "className", "children", "aria-*"],
    demos: [
      {
        id: "tones",
        label: "default × invalid",
        render: () => (
          <ThemedPair>
            {(dark) => (
              <>
                <FormCard prefix={P}>
                  Cartão padrão {dark ? "escuro" : "claro"}.
                </FormCard>
                <FormCard prefix={P} tone="invalid">
                  Cartão em estado inválido.
                </FormCard>
              </>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormLogo",
    family: "forms",
    exportName: "FormLogo",
    title: "FormLogo",
    description:
      "Logo do formulário (34/40/44 px) com selo branco no tema escuro (--delpi-ui-form-logo-bg).",
    docAnchor: "cartoes-do-kit-de-formulario",
    propsSummary: ["src", "alt", "size", "prefix", "className"],
    demos: [
      {
        id: "sizes",
        label: "sm · md · lg",
        render: () => (
          <ThemedPair>
            {(dark) => (
              <div className="puc-questionnaire-inline">
                <FormLogo
                  src={dark ? DEMO_LOGO_DARK : DEMO_LOGO}
                  alt="Marca"
                  size="sm"
                  prefix={P}
                />
                <FormLogo
                  src={dark ? DEMO_LOGO_DARK : DEMO_LOGO}
                  alt="Marca"
                  size="md"
                  prefix={P}
                />
                <FormLogo
                  src={dark ? DEMO_LOGO_DARK : DEMO_LOGO}
                  alt="Marca"
                  size="lg"
                  prefix={P}
                />
              </div>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormThemeToggle",
    family: "forms",
    exportName: "FormThemeToggle",
    title: "FormThemeToggle",
    description:
      "Botão redondo 44×44 que alterna o tema da visita (lua/sol); some quando o escopo tem esquema fixo (canToggle=false).",
    docAnchor: "cartoes-do-kit-de-formulario",
    propsSummary: ["ariaLabel", "prefix", "className"],
    demos: [
      {
        id: "auto",
        label: "auto (clique alterna)",
        render: () => (
          <Swatch scheme="auto">
            <FormThemeToggle ariaLabel="Alternar tema" prefix={P} />
          </Swatch>
        ),
      },
      {
        id: "fixed",
        label: "esquema fixo (oculto)",
        render: () => (
          <ThemedPair>
            {() => (
              <>
                <FormCard prefix={P}>
                  <FormThemeToggle ariaLabel="Alternar tema" prefix={P} />
                  <span>Esquema fixo — sem botão.</span>
                </FormCard>
              </>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormProgress",
    family: "forms",
    exportName: "FormProgress",
    title: "FormProgress",
    description:
      "Barra de progresso (trilho 6 px, raio 3) com role=progressbar e aria-valuenow calculado; rótulo opcional.",
    docAnchor: "cartoes-do-kit-de-formulario",
    propsSummary: ["done", "total", "ariaLabel", "label", "prefix"],
    demos: [
      {
        id: "states",
        label: "0 · 25 · 100 %",
        render: () => (
          <ThemedPair>
            {() => (
              <FormCard prefix={P}>
                <FormProgress
                  done={0}
                  total={12}
                  ariaLabel="Progresso (0%)"
                  label="0 de 12"
                  prefix={P}
                />
                <FormProgress
                  done={3}
                  total={12}
                  ariaLabel="Progresso (25%)"
                  label="3 de 12"
                  prefix={P}
                />
                <FormProgress
                  done={12}
                  total={12}
                  ariaLabel="Progresso (100%)"
                  label="12 de 12"
                  prefix={P}
                />
              </FormCard>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormIntroCard",
    family: "forms",
    exportName: "FormIntroCard",
    title: "FormIntroCard",
    description:
      "Abertura do formulário: logo + ação, eyebrow, título, bloco de contexto, descrição, itens com ícone, ação e nota.",
    docAnchor: "cartoes-do-kit-de-formulario",
    propsSummary: [
      "logo",
      "headerAction",
      "eyebrow",
      "title",
      "context",
      "description",
      "items",
      "action",
      "footnote",
    ],
    demos: [
      {
        id: "full",
        label: "completa",
        render: () => (
          <ThemedPair>
            {(dark) => (
              <FormIntroCard
                prefix={P}
                logo={<DemoLogo dark={dark} />}
                headerAction={
                  <FormThemeToggle ariaLabel="Alternar tema" prefix={P} />
                }
                eyebrow="Avaliação"
                title="Conte como foi sua experiência"
                context={{ label: "Unidade", value: "Unidade Exemplo" }}
                description="Suas respostas levam cerca de 2 minutos."
                items={[
                  {
                    icon: <Clock size={18} />,
                    content: "Duração estimada: 2 minutos",
                  },
                  {
                    icon: <ShieldCheck size={18} />,
                    content: "Respostas anônimas",
                  },
                ]}
                action={<ActionButton variant="primary">Começar</ActionButton>}
                footnote="Você pode sair e retomar depois."
              />
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormHeaderCard",
    family: "forms",
    exportName: "FormHeaderCard",
    title: "FormHeaderCard",
    description:
      "Cabeçalho das etapas: logo + meta/ação, título, subtítulo, divisor, linha da etapa (progresso em texto, uma vez) e barra.",
    docAnchor: "cartoes-do-kit-de-formulario",
    propsSummary: [
      "logo",
      "meta",
      "headerAction",
      "title",
      "subtitle",
      "step",
      "progress",
    ],
    demos: [
      {
        id: "step",
        label: "etapa 3 de 12",
        render: () => (
          <ThemedPair>
            {(dark) => (
              <FormHeaderCard
                prefix={P}
                logo={<DemoLogo dark={dark} />}
                meta="Responda até 31/12/2026"
                headerAction={
                  <FormThemeToggle ariaLabel="Alternar tema" prefix={P} />
                }
                title="Avaliação do atendimento"
                subtitle="Respondendo por Unidade Exemplo"
                step={{
                  label: "Etapa 1 de 3 · Percepção geral",
                  progressLabel: "3 de 12",
                }}
                progress={{ done: 3, total: 12, ariaLabel: "Progresso" }}
              />
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.QuestionCard",
    family: "forms",
    exportName: "QuestionCard",
    title: "QuestionCard",
    description:
      "Quadro da pergunta (fieldset + legend visível): eyebrow, número, enunciado, obrigatória/opcional e erro com aria-describedby.",
    docAnchor: "cartoes-do-kit-de-formulario",
    propsSummary: [
      "eyebrow",
      "number",
      "prompt",
      "required",
      "requiredLabel",
      "optionalLabel",
      "error",
      "children",
    ],
    demos: [
      {
        id: "states",
        label: "normal · opcional · erro",
        render: () => (
          <ThemedPair>
            {() => (
              <>
                <QuestionCard
                  prefix={P}
                  eyebrow="Atendimento"
                  number={1}
                  prompt="Como você avalia o atendimento recebido?"
                  required
                  requiredLabel="obrigatória"
                >
                  <QuestionAnswerStack prefix={P}>
                    <Scale15Demo />
                  </QuestionAnswerStack>
                </QuestionCard>
                <QuestionCard
                  prefix={P}
                  number={2}
                  prompt="Deixe uma sugestão de melhoria."
                  optionalLabel="(opcional)"
                >
                  <QuestionAnswerStack prefix={P}>
                    <TextAnswerDemo />
                  </QuestionAnswerStack>
                </QuestionCard>
                <QuestionCard
                  prefix={P}
                  number={3}
                  prompt="Avalie a experiência como um todo."
                  required
                  requiredLabel="obrigatória"
                  error="Selecione uma opção para continuar."
                >
                  <QuestionAnswerStack prefix={P}>
                    <Scale15Demo invalid />
                  </QuestionAnswerStack>
                </QuestionCard>
              </>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.RatingScale",
    family: "forms",
    exportName: "RatingScale",
    title: "RatingScale",
    description:
      "Escala numérica genérica (1–5, 0–10…): grupo radio nativo exclusivo com N/A, teclado por setas, caption da nota e estado inválido.",
    docAnchor: "respostas-do-kit-de-formulario",
    propsSummary: [
      "name",
      "min",
      "max",
      "value",
      "onChange",
      "optionLabel",
      "endLabels",
      "endLabelsPosition",
      "narrowColumns",
      "selectionCaption",
      "notApplicable",
      "invalid",
      "describedBy",
      "disabled",
    ],
    demos: [
      {
        id: "states",
        label: "sem escolha · nota · N/A · erro",
        render: () => (
          <ThemedPair>
            {() => (
              <>
                <QuestionCard
                  prefix={P}
                  eyebrow="Atendimento"
                  number={1}
                  prompt="Como você avalia o atendimento?"
                  required
                  requiredLabel="obrigatória"
                >
                  <QuestionAnswerStack prefix={P}>
                    <Scale15Demo />
                  </QuestionAnswerStack>
                </QuestionCard>
                <QuestionCard
                  prefix={P}
                  number={2}
                  prompt="Como foi o prazo de entrega?"
                  required
                  requiredLabel="obrigatória"
                >
                  <QuestionAnswerStack prefix={P}>
                    <Scale15Demo initial={4} />
                  </QuestionAnswerStack>
                </QuestionCard>
                <QuestionCard
                  prefix={P}
                  number={3}
                  prompt="A equipe técnica atendeu ao combinado?"
                  required
                  requiredLabel="obrigatória"
                >
                  <QuestionAnswerStack prefix={P}>
                    <Scale15Demo initial="na" />
                  </QuestionAnswerStack>
                </QuestionCard>
                <QuestionCard
                  prefix={P}
                  number={4}
                  prompt="Avalie a comunicação durante o processo."
                  required
                  requiredLabel="obrigatória"
                  error="Selecione uma nota ou “Não se aplica”."
                >
                  <QuestionAnswerStack prefix={P}>
                    <Scale15Demo invalid />
                  </QuestionAnswerStack>
                </QuestionCard>
              </>
            )}
          </ThemedPair>
        ),
      },
      {
        id: "range-0-10",
        label: "0–10 (legenda acima, sem N/A)",
        render: () => (
          <ThemedPair>
            {() => (
              <QuestionCard
                prefix={P}
                number={5}
                prompt="Qual a chance de você indicar esta unidade?"
                required
                requiredLabel="obrigatória"
              >
                <QuestionAnswerStack prefix={P}>
                  <Scale010Demo />
                </QuestionAnswerStack>
              </QuestionCard>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.NotApplicableOption",
    family: "forms",
    exportName: "NotApplicableOption",
    title: "NotApplicableOption",
    description:
      "Pílula 'não se aplica' do MESMO grupo radio da escala: indicador de 18 px, estados normal/selecionado/inválido — nunca controle isolado.",
    docAnchor: "respostas-do-kit-de-formulario",
    propsSummary: [
      "name",
      "label",
      "checked",
      "onChange",
      "disabled",
      "invalid",
      "prefix",
    ],
    demos: [
      {
        id: "states",
        label: "normal · selecionada · inválida",
        render: () => (
          <ThemedPair>
            {() => (
              <div className="puc-questionnaire-inline">
                <NotApplicableOption
                  prefix={P}
                  name="demo-na-1"
                  label="Não se aplica"
                />
                <NotApplicableOption
                  prefix={P}
                  name="demo-na-2"
                  label="Não se aplica"
                  checked
                  onChange={() => {}}
                />
                <NotApplicableOption
                  prefix={P}
                  name="demo-na-3"
                  label="Não se aplica"
                  invalid
                />
              </div>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.QuestionTextAnswer",
    family: "forms",
    exportName: "QuestionTextAnswer",
    title: "QuestionTextAnswer",
    description:
      "Resposta aberta sobre o TextAreaField (intacto): mín. 96 px, fundo de campo, borda de controle; describedBy via role=group (R7).",
    docAnchor: "respostas-do-kit-de-formulario",
    propsSummary: [
      "label",
      "value",
      "onChange",
      "placeholder",
      "hint",
      "rows",
      "maxLength",
      "describedBy",
      "disabled",
      "id",
    ],
    demos: [
      {
        id: "states",
        label: "vazio · preenchido",
        render: () => (
          <ThemedPair>
            {() => (
              <>
                <QuestionCard
                  prefix={P}
                  number={6}
                  prompt="Conte algo que podemos melhorar."
                  optionalLabel="(opcional)"
                >
                  <QuestionAnswerStack prefix={P}>
                    <TextAnswerDemo />
                  </QuestionAnswerStack>
                </QuestionCard>
                <QuestionCard
                  prefix={P}
                  number={7}
                  prompt="Deixe um comentário livre."
                  optionalLabel="(opcional)"
                >
                  <QuestionAnswerStack prefix={P}>
                    <TextAnswerDemo initial="O atendimento foi claro e rápido durante todo o processo." />
                  </QuestionAnswerStack>
                </QuestionCard>
              </>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.QuestionAnswerStack",
    family: "forms",
    exportName: "QuestionAnswerStack",
    title: "QuestionAnswerStack",
    description:
      "Pilha da área de resposta do QuestionCard (R6): ritmo 12 px / 14 px (≥600) entre escala, legenda, N/A e campo — o gap do cartão não atravessa a legend.",
    docAnchor: "respostas-do-kit-de-formulario",
    propsSummary: ["prefix", "className", "children"],
    demos: [
      {
        id: "rhythm",
        label: "escala + campo na mesma pilha",
        render: () => (
          <ThemedPair>
            {() => (
              <QuestionCard
                prefix={P}
                number={8}
                prompt="Avalie e comente, se quiser detalhar."
                optionalLabel="(opcional)"
              >
                <QuestionAnswerStack prefix={P}>
                  <Scale15Demo />
                  <TextAnswerDemo />
                </QuestionAnswerStack>
              </QuestionCard>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormButton",
    family: "forms",
    exportName: "FormButton",
    title: "FormButton",
    description:
      "Botão do formulário sobre o ActionButton intacto (§8.7): visual escopado na raiz do kit vence por especificidade; busy mantém o foco.",
    docAnchor: "acoes-e-fechamento-do-kit-de-formulario-p4",
    propsSummary: [
      "variant",
      "busy",
      "busyLabel",
      "fullWidth",
      "type",
      "onClick",
      "children",
    ],
    demos: [
      {
        id: "variants",
        label: "primário · secundário · enviando",
        render: () => (
          <ThemedPair>
            {() => (
              <QuestionAnswerStack prefix={P}>
                <FormButton prefix={P} onClick={() => {}}>
                  Avançar
                </FormButton>
                <FormButton
                  prefix={P}
                  variant="secondary"
                  onClick={() => {}}
                >
                  Voltar
                </FormButton>
                <FormButton prefix={P} busy busyLabel="Enviando…">
                  Enviar respostas
                </FormButton>
              </QuestionAnswerStack>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormStepFooter",
    family: "forms",
    exportName: "FormStepFooter",
    title: "FormStepFooter",
    description:
      "Rodapé de ações: sticky na base abaixo de 600 px (exige ancestrais com overflow visible — verificação obrigatória do P6), mensagem role=status e botões Voltar/Avançar.",
    docAnchor: "acoes-e-fechamento-do-kit-de-formulario-p4",
    propsSummary: ["message", "back", "next", "prefix", "className"],
    demos: [
      {
        id: "sticky",
        label: "com e sem Voltar · mensagem · enviando (role no quadro)",
        render: () => (
          <ThemedPair>
            {() => (
              <div className="puc-form-footer-scroll">
                <QuestionAnswerStack prefix={P}>
                  <QuestionCard
                    prefix={P}
                    number={1}
                    prompt="Como você avalia a experiência?"
                    required
                    requiredLabel="obrigatória"
                  >
                    <Scale15Demo />
                  </QuestionCard>
                  <QuestionCard
                    prefix={P}
                    number={2}
                    prompt="Deixe uma sugestão de melhoria."
                    optionalLabel="(opcional)"
                  >
                    <TextAnswerDemo />
                  </QuestionCard>
                </QuestionAnswerStack>
                <FormStepFooter
                  prefix={P}
                  back={{ label: "Voltar", onClick: () => {} }}
                  next={{ label: "Avançar", onClick: () => {} }}
                />
                <FormStepFooter
                  prefix={P}
                  message="Responda a questão 1 para continuar."
                  back={{ label: "Voltar", onClick: () => {} }}
                  next={{
                    label: "Enviar respostas",
                    onClick: () => {},
                    busy: true,
                    busyLabel: "Enviando…",
                  }}
                />
              </div>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormNotice",
    family: "forms",
    exportName: "FormNotice",
    title: "FormNotice",
    description:
      "Aviso em bloco (role=note): warning usa --delpi-ui-form-warning-*; info usa tint + accent-text. Textos por children.",
    docAnchor: "acoes-e-fechamento-do-kit-de-formulario-p4",
    propsSummary: ["tone", "children", "prefix", "className"],
    demos: [
      {
        id: "tones",
        label: "warning · info",
        render: () => (
          <ThemedPair>
            {() => (
              <QuestionAnswerStack prefix={P}>
                <FormNotice prefix={P}>
                  Suas respostas são anônimas e usadas apenas para melhoria.
                </FormNotice>
                <FormNotice prefix={P} tone="info">
                  Você pode voltar e revisar antes de enviar.
                </FormNotice>
              </QuestionAnswerStack>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormReviewSection",
    family: "forms",
    exportName: "FormReviewSection",
    title: "FormReviewSection",
    description:
      "Seção de revisão: título + Editar (hit ≥44 px) e dl/dt/dd — linhas comuns, muted (itálico) e block (comentário com pre-line).",
    docAnchor: "acoes-e-fechamento-do-kit-de-formulario-p4",
    propsSummary: ["title", "edit", "rows", "prefix", "className"],
    demos: [
      {
        id: "rows",
        label: "valor · N/A · vazio · comentário",
        render: () => (
          <ThemedPair>
            {() => (
              <FormReviewSection
                prefix={P}
                title="Suas respostas"
                edit={{
                  label: "Editar",
                  ariaLabel: "Editar respostas desta etapa",
                  onClick: () => {},
                }}
                rows={[
                  { label: "Atendimento", value: "5 · Muito satisfeito" },
                  { label: "Prazo de entrega", value: "Não se aplica" },
                  {
                    label: "Recomendação",
                    value: "Sem resposta",
                    muted: true,
                  },
                  {
                    label: "Comentário",
                    value:
                      "Equipe atenciosa.\nEntrega dentro do prazo combinado.",
                    block: true,
                  },
                ]}
              />
            )}
          </ThemedPair>
        ),
      },
    ],
  },
  {
    id: "forms.FormResultPanel",
    family: "forms",
    exportName: "FormResultPanel",
    title: "FormResultPanel",
    description:
      "Tela de resultado centrada: círculo success 72 px + check (só no tom success), role status/alert, título/mensagem/hint/ação por props.",
    docAnchor: "acoes-e-fechamento-do-kit-de-formulario-p4",
    propsSummary: [
      "tone",
      "title",
      "message",
      "hint",
      "action",
      "logo",
      "prefix",
      "className",
    ],
    demos: [
      {
        id: "tones",
        label: "sucesso · erro com ação",
        render: () => (
          <ThemedPair>
            {() => (
              <QuestionAnswerStack prefix={P}>
                <FormResultPanel
                  prefix={P}
                  tone="success"
                  title="Respostas enviadas"
                  message="Obrigado por participar. Sua opinião ajuda a melhorar nossos serviços."
                  hint="Você já pode fechar esta página."
                />
                <FormResultPanel
                  prefix={P}
                  tone="error"
                  title="Não foi possível enviar"
                  message="Ocorreu uma falha ao registrar suas respostas."
                  hint="Tente novamente em alguns instantes."
                  action={
                    <FormButton prefix={P} onClick={() => {}}>
                      Tentar novamente
                    </FormButton>
                  }
                />
              </QuestionAnswerStack>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
];
