class ImportExternalActionsSchemaUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute_from_json(self, provider_key: str, schema_json: dict) -> dict:
        if not isinstance(schema_json, dict):
            raise ValueError("schema must be a JSON object")

        return self.repository.import_schema_from_json(
            provider_key=provider_key,
            schema_json=schema_json,
            source_type="manual",
        )

    def execute_from_url(self, provider_key: str) -> dict:
        return self.repository.import_schema_from_url(provider_key=provider_key)
