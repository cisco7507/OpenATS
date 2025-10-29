from asteval import Interpreter
from logging import getLogger
from typing import Dict, Any

log = getLogger(__name__)

# The default asteval symtable allows for an unsafe 'eval'
# We'll remove it, and a few others we don't need.
unwanted_symbols = ['eval', 'exec', 'exit', 'quit', 'help', 'dir']

class AttrDict:
    """A dictionary that allows attribute-style access."""
    def __init__(self, d):
        self.__dict__ = d

class SafeEvaluator(Interpreter):
    """
    A customized asteval Interpreter that prevents access to unsafe
    built-in functions in workflow conditional expressions.
    """
    def __init__(self, symtable: Dict[str, Any] = None, *args, **kwargs):
        if symtable is None:
            symtable = {}

        # 1. Create the default symbol table
        super().__init__(symtable=symtable, *args, **kwargs)

        # 2. Remove any unwanted symbols
        for symbol in unwanted_symbols:
            if symbol in self.symtable:
                self.symtable.pop(symbol)
                log.debug(f"Removed unsafe symbol '{symbol}' from asteval symtable.")

def evaluate_condition(expression: str, context: 'WorkflowContext') -> bool:
    """
    Safely evaluates a conditional expression from a workflow step.

    Args:
        expression: The string expression to evaluate (e.g., "${metrics.lufs > -23.0}").
        context: The WorkflowContext object containing vars, metrics, and params.

    Returns:
        The boolean result of the evaluation.
    """
    if not isinstance(expression, str):
        log.warning(f"Invalid expression type for condition: {type(expression)}. Returning False.")
        return False

    # Expand any variables in the expression before evaluation
    expanded_expr = context.expand_vars(expression)

    # Strip the ${...} wrapper if it exists, so we evaluate the inner expression
    if expanded_expr.startswith('${') and expanded_expr.endswith('}'):
        expanded_expr = expanded_expr[2:-1]

    log.debug(f"Evaluating expression: '{expanded_expr}'")

    # Create a combined symbol table for the evaluator
    symtable = {
        'vars': AttrDict(context.vars),
        'metrics': AttrDict(context.metrics),
        'parameters': AttrDict(context.params)
    }

    aeval = SafeEvaluator(symtable=symtable)

    try:
        result = aeval.eval(expanded_expr)

        if not isinstance(result, bool):
            log.warning(f"Expression '{expanded_expr}' did not evaluate to a boolean. Result: {result}. Returning False.")
            return False

        return result
    except Exception as e:
        log.error(f"Error evaluating condition '{expression}': {e}", exc_info=True)
        return False