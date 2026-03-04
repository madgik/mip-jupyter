from .client import get_client

class DataModel:
    """Data model metadata and datasets available for analysis."""

    def __init__(self, data):
        self.code = data.get('code')
        self.version = data.get('version')
        self.label = data.get('label')
        self.variables = data.get('variables', [])
        # Datasets structure might vary, handle as list of dicts or strings
        self.datasets = data.get('datasets', [])

    def __repr__(self):
        return f"<DataModel(code='{self.code}', version='{self.version}')>"

    @classmethod
    def list(cls):
        """List all data models visible to the current user."""
        client = get_client()
        data = client.get('/data-models')
        return [cls(model) for model in data]
