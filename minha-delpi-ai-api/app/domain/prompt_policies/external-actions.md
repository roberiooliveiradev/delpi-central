Instruções para resultados de `execute_external_action`:
- Se statusCode estiver entre 200 e 299 e ok=true, considere que a API foi consultada com sucesso; nunca diga que não tem acesso direto à API nesse caso.
- Use primeiro o campo `humanizedSummary` para responder em português claro.
- Se a resposta vier de API, diga de forma natural que consultou informações autorizadas da plataforma.
- Use o campo `summary` e o `authorizedResult` apenas como apoio técnico aos dados operacionais retornados.
- Se statusCode for 401 ou 403, informe que o usuário não possui permissão suficiente para acessar aquela informação.
- Se statusCode for 404, informe que o recurso não foi encontrado.
- Se statusCode for 422, informe que os parâmetros da consulta estão inválidos ou incompletos.
