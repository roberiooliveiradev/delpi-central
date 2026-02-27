from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html

@app.get("/docs", include_in_schema=False)
async def custom_swagger():

    swagger_html = get_swagger_ui_html(
        openapi_url="/apps/api-delpi/openapi.json",
        title="API DELPI Docs",
    )

    injected_script = """
    <script>
    window.DELPI_TOKEN = null;

    function applyToken(token) {
        if (!window.ui) return;
        window.ui.preauthorizeApiKey("BearerAuth", token);
    }

    // Recebe token da Central
    window.addEventListener("message", function (event) {
        if (event.origin !== "http://localhost") return;

        if (event.data?.type === "DELPI_AUTH") {
            window.DELPI_TOKEN = event.data.token;
            applyToken(window.DELPI_TOKEN);
            console.log("Swagger token atualizado automaticamente 🔄");
        }
    });

    // Intercepta 401 para solicitar refresh
    const originalFetch = window.fetch;
    window.fetch = async function() {
        const response = await originalFetch.apply(this, arguments);

        if (response.status === 401) {
            console.warn("Token expirado, solicitando refresh...");
            window.parent.postMessage(
                { type: "DELPI_REFRESH_REQUEST" },
                "http://localhost"
            );
        }

        return response;
    };
    </script>
    """

    html_content = swagger_html.body.decode("utf-8")
    html_content = html_content.replace("</body>", injected_script + "</body>")

    return HTMLResponse(content=html_content)