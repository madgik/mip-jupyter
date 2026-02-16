from .client import get_client

class Algorithm:
    """Algorithm metadata returned by backend catalog."""

    def __init__(self, data):
        self.name = data.get('name')
        self.label = data.get('label')
        self.parameters = data.get('parameters', {})
        self.inputdata = data.get('inputdata', {})

    def __repr__(self):
        return f"<Algorithm(name='{self.name}', label='{self.label}')>"

    @classmethod
    def list(cls):
        """List all available algorithms."""
        client = get_client()
        data = client.get('/algorithms')
        return [cls(algo) for algo in data]
