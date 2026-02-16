from .client import get_client

class Experiment:
    """High-level experiment entity and operations."""

    def __init__(self, data):
        self.uuid = data.get('uuid')
        self.name = data.get('name')
        self.status = data.get('status')
        # Backend uses created/finished; keep legacy keys for backwards compatibility.
        self.creation_date = data.get('created', data.get('creationDate'))
        self.end_date = data.get('finished', data.get('endDate'))
        self.algorithm = data.get('algorithm', {})
        # Backend uses "result"; keep legacy "results".
        self.results = data.get('result', data.get('results'))
        # Backend doesn't have a stable top-level error field; keep legacy key and also
        # try a few common shapes inside result for better error reporting.
        self.error_message = data.get('errorMessage') or data.get('error')
        if not self.error_message and isinstance(self.results, dict):
            self.error_message = (
                self.results.get('errorMessage')
                or self.results.get('error')
                or self.results.get('message')
            )

    def __repr__(self):
        return f"<Experiment(uuid='{self.uuid}', name='{self.name}', status='{self.status}')>"

    @classmethod
    def list(cls, limit=10, offset=0):
        """List experiments with pagination controls."""
        client = get_client()
        response = client.get('/experiments', params={'size': limit, 'page': offset // limit})
        experiments_data = response.get('experiments', [])
        return [cls(exp_data) for exp_data in experiments_data]

    @classmethod
    def get(cls, uuid):
        """Get a single experiment by UUID."""
        client = get_client()
        data = client.get(f'/experiments/{uuid}')
        return cls(data)

    def delete(self):
        """Delete this experiment from backend."""
        client = get_client()
        client.delete(f'/experiments/{self.uuid}')

    @classmethod
    def create(cls, name, algorithm_name, data_model, datasets, x=None, y=None, filters=None, parameters=None, preprocessing=None, mip_version=None):
        """
        Create a new experiment.

        :param name: Name of the experiment
        :param algorithm_name: Name of the algorithm (e.g., 'linear_regression')
        :param data_model: Data model code (e.g., 'dementia:0.1')
        :param datasets: List of dataset codes
        :param x: List of covariate codes (features)
        :param y: List of variable codes (targets)
        :param filters: Filter dictionary (condition, rules)
        :param parameters: Algorithm parameters dictionary
        :param preprocessing: Preprocessing dictionary
        :param mip_version: MIP version string
        :return: Experiment instance
        """
        client = get_client()
        
        payload = {
            "name": name,
            "mipVersion": mip_version or "9.0.0",
            "algorithm": {
                "name": algorithm_name,
                "parameters": parameters or {},
                "preprocessing": preprocessing or {},
                "inputdata": {
                    "data_model": data_model,
                    "datasets": datasets,
                    "x": x or [],
                    "y": y or [],
                    "filters": filters
                }
            }
        }
        
        data = client.post('/experiments', data=payload)
        return cls(data)

    @classmethod
    def run_transient(
        cls,
        name,
        algorithm_name,
        data_model,
        datasets,
        x=None,
        y=None,
        filters=None,
        parameters=None,
        preprocessing=None,
        mip_version=None,
        raise_on_failure=True,
    ):
        """Run a transient experiment (synchronous, not persisted).

        Backend endpoint: POST /experiments/transient

        This is useful for notebook users who want quick feedback without creating
        a persisted experiment in their history. The backend executes the algorithm
        synchronously and returns the final result and status.

        Args:
            raise_on_failure: If True (default), raise RuntimeError when the
                returned status indicates failure.
        """
        client = get_client()

        payload = {
            "name": name,
            "mipVersion": mip_version or "9.0.0",
            "algorithm": {
                "name": algorithm_name,
                "parameters": parameters or {},
                "preprocessing": preprocessing or {},
                "inputdata": {
                    "data_model": data_model,
                    "datasets": datasets,
                    "x": x or [],
                    "y": y or [],
                    "filters": filters,
                },
            },
        }

        data = client.post("/experiments/transient", data=payload)
        exp = cls(data)

        if raise_on_failure:
            status = (exp.status or "").strip().lower()
            if status in {"error", "failed", "failure"} or exp.error_message:
                details = exp.error_message or exp.results
                raise RuntimeError(
                    "Transient experiment failed.\n"
                    f"- uuid: {exp.uuid}\n"
                    f"- status: {exp.status}\n"
                    f"- details: {details}\n"
                )

        return exp

    def wait(self, timeout=None, poll_interval=2, raise_on_failure=True):
        """Poll backend until experiment reaches a terminal state.

        Portal Backend statuses (current):
        - pending: in progress
        - success: completed
        - error: failed

        Args:
            timeout: Optional timeout in seconds.
            poll_interval: Seconds to sleep between polls (default 2).
            raise_on_failure: If True (default), raise RuntimeError when the
                experiment finishes with a failure status.
        """
        import time
        start = time.time()
        poll_interval = float(poll_interval or 0)

        def _norm(s):
            if s is None:
                return ""
            return str(s).strip().lower()

        # Be permissive for older/newer backends.
        success_states = {"success", "done", "completed", "complete", "ok"}
        failure_states = {"error", "failed", "failure", "cancelled", "canceled", "aborted", "killed"}
        terminal_states = success_states | failure_states

        while True:
            status = _norm(self.status)
            # Some backends may keep status at "pending" even after a terminal update,
            # while still setting finished/end_date and result. Treat finished timestamp as terminal.
            finished = self.end_date is not None

            if status in terminal_states or finished:
                is_failure = status in failure_states or bool(self.error_message)
                if is_failure and raise_on_failure:
                    details = self.error_message
                    if not details:
                        details = self.results
                    raise RuntimeError(
                        "Experiment failed.\n"
                        f"- uuid: {self.uuid}\n"
                        f"- status: {self.status}\n"
                        f"- finished: {self.end_date}\n"
                        f"- details: {details}\n"
                    )
                return self

            if timeout and (time.time() - start) > timeout:
                raise TimeoutError(
                    f"Experiment timed out after {timeout}s (last status: {self.status!r}, uuid: {self.uuid})"
                )

            time.sleep(poll_interval if poll_interval > 0 else 0)

            # Refresh
            updated = self.get(self.uuid)
            self.status = updated.status
            self.results = updated.results
            self.error_message = updated.error_message
            self.end_date = updated.end_date
