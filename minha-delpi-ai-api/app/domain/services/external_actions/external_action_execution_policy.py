class ExternalActionExecutionPolicy:
    """Sanitiza respostas de actions sem cortar listas de dados operacionais."""

    MAX_RESPONSE_STRING_LENGTH = 8000

    _SENSITIVE_KEYS = frozenset(
        {
            "access_token",
            "refresh_token",
            "token",
            "client_secret",
            "password",
            "authorization",
        }
    )

    def validate(self, provider: dict, action: dict, arguments: dict) -> None:
        if not provider.get("enabled"):
            raise ValueError("Provider is disabled")

        if not action.get("enabled"):
            raise ValueError("Action is disabled")

        parameters = arguments.get("parameters") or {}

        if not isinstance(parameters, dict):
            raise ValueError("parameters must be an object")

        body = arguments.get("body")

        self._validate_parameters(action, parameters)
        self._validate_body(action, body)

    def sanitize_response(self, data):
        return self._sanitize(data)

    def _validate_parameters(self, action: dict, parameters: dict) -> None:
        allowed_parameters = {
            parameter.get("name"): parameter
            for parameter in action.get("parametersSchema") or []
            if parameter.get("name")
        }

        for name in parameters:
            if name not in allowed_parameters:
                raise ValueError(f"Unknown parameter: {name}")

        for name, parameter in allowed_parameters.items():
            if parameter.get("required") and name not in parameters:
                raise ValueError(f"Missing required parameter: {name}")

        for parameter in action.get("parametersSchema") or []:
            if parameter.get("in") != "path":
                continue

            name = parameter.get("name")

            if name and "{" + name + "}" in action["path"] and name not in parameters:
                raise ValueError(f"Missing path parameter: {name}")

    def _validate_body(self, action: dict, body) -> None:
        method = str(action.get("method") or "").upper()

        if method in {"GET", "HEAD", "DELETE"} and body not in (None, "", {}, []):
            raise ValueError("body is not allowed for this method")

    def _sanitize(self, value):
        if isinstance(value, dict):
            return {
                key: self._sanitize(item)
                for key, item in value.items()
                if key.lower() not in self._SENSITIVE_KEYS
            }

        if isinstance(value, list):
            return [self._sanitize(item) for item in value]

        if isinstance(value, str):
            return value[: self.MAX_RESPONSE_STRING_LENGTH]

        return value
