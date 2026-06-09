"""Script injetado no Swagger UI — auth e tema do portal (postMessage)."""

from __future__ import annotations


def build_swagger_portal_bridge_script(allowed_origins: list[str]) -> str:
    allowed_origins_js = "[" + ", ".join(f'"{origin}"' for origin in allowed_origins) + "]"

    return f"""
    <style id="delpi-swagger-theme-vars">
      :root {{
        --delpi-primary: #089bdb;
        --delpi-secondary: #003866;
        --delpi-bg: #ffffff;
        --delpi-surface: #ffffff;
        --delpi-surface-2: #f7f7f7;
        --delpi-text: #111111;
        --delpi-text-muted: rgba(17, 17, 17, 0.7);
        --delpi-border: #e6e6e6;
      }}
      html[data-delpi-theme="dark"] {{
        --delpi-bg: #0f1115;
        --delpi-surface: #0f1115;
        --delpi-surface-2: #1b2030;
        --delpi-text: rgba(255, 255, 255, 0.88);
        --delpi-text-muted: rgba(255, 255, 255, 0.72);
        --delpi-border: rgba(255, 255, 255, 0.12);
      }}
      html[data-delpi-theme="dark"] body {{
        background: var(--delpi-bg);
        color: var(--delpi-text);
      }}
      .swagger-ui .topbar {{
        background-color: var(--delpi-secondary);
      }}
      .swagger-ui .topbar .download-url-wrapper .select-label,
      .swagger-ui .topbar .download-url-wrapper input[type=text] {{
        color: #ffffff;
      }}
      html[data-delpi-theme="dark"] .swagger-ui .info .title,
      html[data-delpi-theme="dark"] .swagger-ui .info p,
      html[data-delpi-theme="dark"] .swagger-ui .info li,
      html[data-delpi-theme="dark"] .swagger-ui .info a,
      html[data-delpi-theme="dark"] .swagger-ui .opblock-tag,
      html[data-delpi-theme="dark"] .swagger-ui .opblock .opblock-summary-path,
      html[data-delpi-theme="dark"] .swagger-ui .opblock .opblock-summary-description,
      html[data-delpi-theme="dark"] .swagger-ui label,
      html[data-delpi-theme="dark"] .swagger-ui .parameter__name,
      html[data-delpi-theme="dark"] .swagger-ui .response-col_status,
      html[data-delpi-theme="dark"] .swagger-ui table thead tr td,
      html[data-delpi-theme="dark"] .swagger-ui table thead tr th,
      html[data-delpi-theme="dark"] .swagger-ui .model-title {{
        color: var(--delpi-text);
      }}
      html[data-delpi-theme="dark"] .swagger-ui .opblock {{
        background: var(--delpi-surface-2);
        border-color: var(--delpi-border);
      }}
      html[data-delpi-theme="dark"] .swagger-ui section.models {{
        background: var(--delpi-surface-2);
        border-color: var(--delpi-border);
      }}
      html[data-delpi-theme="dark"] .swagger-ui .model-box,
      html[data-delpi-theme="dark"] .swagger-ui .model {{
        background: var(--delpi-surface);
      }}
      html[data-delpi-theme="dark"] .swagger-ui .opblock-body pre.microlight,
      html[data-delpi-theme="dark"] .swagger-ui textarea,
      html[data-delpi-theme="dark"] .swagger-ui input[type=text],
      html[data-delpi-theme="dark"] .swagger-ui select {{
        background: var(--delpi-bg);
        color: var(--delpi-text);
        border-color: var(--delpi-border);
      }}
      html[data-delpi-theme="dark"] .swagger-ui .btn.authorize {{
        border-color: var(--delpi-primary);
        color: var(--delpi-primary);
      }}
      html[data-delpi-theme="dark"] .swagger-ui .scheme-container {{
        background: var(--delpi-surface);
        box-shadow: none;
        border: 1px solid var(--delpi-border);
      }}
    </style>
    <script>
    window.DELPI_TOKEN = null;
    window.DELPI_THEME_RESOLVED = "light";

    const ALLOWED_ORIGINS = {allowed_origins_js};

    function isAllowedOrigin(origin) {{
        if (!origin) return false;
        if (!ALLOWED_ORIGINS.length) return origin === window.location.origin;
        return ALLOWED_ORIGINS.includes(origin) || origin === window.location.origin;
    }}

    function parentTargetOrigin() {{
        if (ALLOWED_ORIGINS.includes(window.location.origin)) {{
            return window.location.origin;
        }}
        return ALLOWED_ORIGINS[0] || window.location.origin;
    }}

    function notifyParentReady() {{
        try {{
            if (window.parent && window.parent !== window) {{
                window.parent.postMessage(
                    {{ type: "DELPI_AUTH_READY" }},
                    parentTargetOrigin()
                );
            }}
        }} catch (error) {{
            console.warn("Falha ao notificar parent (DELPI_AUTH_READY):", error);
        }}
    }}

    function normalizeBearerToken(token) {{
        if (!token) return null;
        const trimmed = String(token).trim();
        if (!trimmed) return null;
        return trimmed.toLowerCase().startsWith("bearer ")
            ? trimmed
            : "Bearer " + trimmed;
    }}

    function bareJwt(token) {{
        const bearer = normalizeBearerToken(token);
        if (!bearer) return null;
        return bearer.replace(/^Bearer\\s+/i, "");
    }}

    function authorizeSwagger(token) {{
        const jwt = bareJwt(token);
        if (!jwt || !window.ui) return false;

        if (window.ui.authActions && window.ui.authActions.authorize) {{
            try {{
                window.ui.authActions.authorize({{
                    BearerAuth: {{
                        name: "BearerAuth",
                        schema: {{
                            type: "http",
                            scheme: "bearer",
                            bearerFormat: "JWT",
                        }},
                        value: jwt,
                    }},
                }});
                return true;
            }} catch (error) {{
                console.warn("authActions.authorize falhou:", error);
            }}
        }}

        if (window.ui.preauthorizeApiKey) {{
            try {{
                window.ui.preauthorizeApiKey("BearerAuth", jwt);
                return true;
            }} catch (error) {{
                console.warn("preauthorizeApiKey falhou:", error);
            }}
        }}

        return false;
    }}

    function applyToken(token) {{
        if (!token) return;

        function tryApply(attempt) {{
            if (authorizeSwagger(token)) return;
            if (attempt < 48) {{
                window.setTimeout(function () {{ tryApply(attempt + 1); }}, 250);
            }}
        }}

        tryApply(0);
    }}

    function applyTheme(resolved) {{
        const theme = resolved === "dark" ? "dark" : "light";
        window.DELPI_THEME_RESOLVED = theme;
        document.documentElement.setAttribute("data-delpi-theme", theme);
    }}

    window.addEventListener("message", function (event) {{
        if (!isAllowedOrigin(event.origin)) return;

        if (event.data?.type === "DELPI_AUTH" && event.data?.token) {{
            window.DELPI_TOKEN = event.data.token;
            applyToken(window.DELPI_TOKEN);
        }}

        if (event.data?.type === "DELPI_THEME") {{
            applyTheme(event.data.resolved || event.data.theme || "light");
        }}
    }});

    const originalFetch = window.fetch.bind(window);

    window.fetch = async function (input, init) {{
        const nextInit = Object.assign({{}}, init || {{}});
        const headers = new Headers(nextInit.headers || {{}});

        if (window.DELPI_TOKEN && !headers.has("Authorization")) {{
            const bearer = normalizeBearerToken(window.DELPI_TOKEN);
            if (bearer) headers.set("Authorization", bearer);
        }}

        nextInit.headers = headers;
        const response = await originalFetch.call(this, input, nextInit);

        if (response.status === 401) {{
            try {{
                if (window.parent && window.parent !== window) {{
                    window.parent.postMessage(
                        {{ type: "DELPI_REFRESH_REQUEST" }},
                        parentTargetOrigin()
                    );
                }}
            }} catch (error) {{
                console.warn("Falha ao solicitar refresh do token:", error);
            }}
        }}

        return response;
    }};

    window.addEventListener("load", function () {{
        notifyParentReady();
        if (window.DELPI_TOKEN) {{
            applyToken(window.DELPI_TOKEN);
        }}
    }});
    </script>
    """
