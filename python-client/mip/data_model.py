from .client import get_client


class DataModel:
    """Data model metadata and datasets available for analysis."""

    def __init__(self, data):
        self.code = data.get('code')
        self.version = data.get('version')
        self.label = data.get('label')
        self.longitudinal = data.get('longitudinal')
        self.variables = data.get('variables', [])
        self.groups = data.get('groups', [])
        # Datasets structure might vary, handle as list of dicts or strings
        self.datasets = data.get('datasets', [])
        self.datasets_variables = data.get('datasetsVariables', data.get('datasets_variables', {}))

    def __repr__(self):
        return f"<DataModel(code='{self.code}', version='{self.version}')>"

    @classmethod
    def list(cls):
        """List all data models visible to the current user."""
        client = get_client()
        data = client.get('/data-models')
        return [cls(model) for model in data]
