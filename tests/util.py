def arg_or_kwarg(call, position, keyword):
    """Extract argument from unittest.mock.call whether positional or keyword"""
    if keyword in call.kwargs:
        return call.kwargs[keyword]
    return call.args[position]
