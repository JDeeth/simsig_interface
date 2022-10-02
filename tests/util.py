def arg_or_kwarg(call, position, keyword):
    """Extract argument from unittest.mock.call whether positional or keyword"""

    # for 3.7 compatibility: call[0] is call.args, call[1] is call.kwargs
    if keyword in call[1]:
        return call[1][keyword]
    return call[0][position]
