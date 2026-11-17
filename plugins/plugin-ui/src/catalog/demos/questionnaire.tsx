import { Clock, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { PUC_PREFIX } from "../../app/bemPrefix";
import { ActionButton } from "../../components/actions/ActionButton";
import {
  FormCard,
  FormHeaderCard,
  FormIntroCard,
  FormLogo,
  FormPageLayout,
  FormProgress,
  FormThemeToggle,
  QuestionCard,
  QuestionnaireThemeScope,
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

/** Área de resposta neutra (escala/campo chegam nos pacotes seguintes). */
function AnswerPlaceholder() {
  return (
    <div className="puc-questionnaire-answer-placeholder">
      Área de resposta — escala/campo (pacotes seguintes)
    </div>
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
                  <AnswerPlaceholder />
                </QuestionCard>
                <QuestionCard
                  prefix={P}
                  number={2}
                  prompt="Deixe uma sugestão de melhoria."
                  optionalLabel="(opcional)"
                >
                  <AnswerPlaceholder />
                </QuestionCard>
                <QuestionCard
                  prefix={P}
                  number={3}
                  prompt="Avalie a experiência como um todo."
                  required
                  requiredLabel="obrigatória"
                  error="Selecione uma opção para continuar."
                >
                  <AnswerPlaceholder />
                </QuestionCard>
              </>
            )}
          </ThemedPair>
        ),
      },
    ],
  },
];
