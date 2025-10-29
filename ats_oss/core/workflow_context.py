from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import re
import copy
from ats_oss.logging import log

class WorkflowContext:
    """
    Manages the state of a running workflow, including variables, metrics,
    parameters, and the thread pool for parallel execution.
    """
    def __init__(self, workflow_id: str, initial_vars: Dict[str, Any], params: Dict[str, Any]):
        self.workflow_id = workflow_id
        self.vars: Dict[str, Any] = initial_vars
        self.metrics: Dict[str, Any] = {}
        self.params: Dict[str, Any] = params
        self.executor: Optional[ThreadPoolExecutor] = None

    def expand_vars(self, data: Any) -> Any:
        """
        Recursively substitutes placeholders in a data structure.
        Placeholders can be in the format ${scope.key}, where scope is one of
        'vars', 'metrics', or 'parameters'.

        Example:
            "${vars.input_path}" -> "/path/to/file.wav"
            "${metrics.integrated_lufs}" -> -23.5
        """
        if isinstance(data, dict):
            return {k: self.expand_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.expand_vars(item) for item in data]
        elif isinstance(data, str):
            # Regex to find all placeholders like ${scope.key}
            pattern = re.compile(r'\$\{(\w+)\.(\w+)\}')

            def replacer(match):
                scope_name, key = match.groups()

                if scope_name == 'vars':
                    source = self.vars
                elif scope_name == 'metrics':
                    source = self.metrics
                elif scope_name == 'parameters':
                    source = self.params
                else:
                    log.warning(f"Invalid scope '{scope_name}' in placeholder '{match.group(0)}'.")
                    return match.group(0) # Return the original placeholder if scope is invalid

                value = source.get(key, f'<{scope_name}.{key}_NOT_FOUND>')

                # It's crucial to convert the value to a string for substitution
                return str(value)

            # Keep expanding until no placeholders are left
            while pattern.search(data):
                data = pattern.sub(replacer, data)
            return data
        return data

    def copy(self) -> 'WorkflowContext':
        """
        Creates a deep copy of the context for use in parallel branches.
        The executor is shared across all copies.
        """
        new_context = WorkflowContext(self.workflow_id, copy.deepcopy(self.vars), copy.deepcopy(self.params))
        new_context.metrics = copy.deepcopy(self.metrics)
        new_context.executor = self.executor # Share the executor instance
        return new_context

    def get_or_create_executor(self, max_workers: Optional[int] = None) -> ThreadPoolExecutor:
        """
        Initializes the ThreadPoolExecutor if it doesn't exist.
        """
        if self.executor is None:
            log.info("Creating a new ThreadPoolExecutor for parallel execution.")
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
        return self.executor

    def shutdown_executor(self):
        """
        Gracefully shuts down the thread pool executor if it was created.
        """
        if self.executor:
            log.info("Shutting down the ThreadPoolExecutor.")
            self.executor.shutdown(wait=True)
            self.executor = None
