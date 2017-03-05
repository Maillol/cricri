"""
Decorator and objects to disable/enable test method regarding previous
executed steps.
"""

class Condition:
    """
    Condition is class base to set of condition for condition decorator.
    """

    def __neg__(self):
        return _NotWrap(self)

    def __and__(self, other):
        return _AndWrap(self, other)

    def __or__(self, other):
        return _OrWrap(self, other)


class _NotWrap(Condition):
    """
    Wrap condition and return a new condition.

    Wrapped condition call return not condition.
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, previous_steps):
        return not self.func(previous_steps)


class _AndWrap(Condition):
    """
    Wrap two condition and return a new condition.

    Wrapped condition calls return condition_1 and condition_2.
    """

    def __init__(self, func_1, func_2):
        self.func_1 = func_1
        self.func_2 = func_2

    def __call__(self, previous_steps):
        return self.func_1(previous_steps) and self.func_2(previous_steps)


class _OrWrap(Condition):
    """
    Wrap two condition and return a new condition.

    Wrapped condition calls return condition_1 or condition_2.
    """

    def __init__(self, func_1, func_2):
        self.func_1 = func_1
        self.func_2 = func_2

    def __call__(self, previous_steps):
        return self.func_1(previous_steps) or self.func_2(previous_steps)


class Path(Condition):
    """
    True if steps path is in previous steps.
    """

    def __init__(self, *steps):
        self.steps = tuple(steps)

    def __call__(self, previous_steps):
        previous_steps = tuple(previous_steps)
        length = len(self.steps)
        for i in range(len(previous_steps) - length + 1):
            if previous_steps[i : i + length] == self.steps:
                return True
        return False


class Newer(Condition):
    """
    True if step_2 is newer than step_1 or step_1 doesn't exist.
    """

    def __init__(self, step_1, step_2):
        self.step_1 = step_1
        self.step_2 = step_2

    def __call__(self, previous_steps):
        previous_steps = tuple(reversed(previous_steps))
        try:
            index_2 = previous_steps.index(self.step_2)
        except ValueError:
            return False

        try:
            index_1 = previous_steps.index(self.step_1)
        except ValueError:
            return True

        return index_1 > index_2


def condition(cond):
    """
    This decorator define condition to execute the decorated test method.
    """
    if not isinstance(cond, Condition):
        raise TypeError("First argument must be a Condition object such as Path or Newer.")

    def decorator(func):
        """
        Set condition attribute to decorated method.
        """
        func.condition = cond
        return func

    return decorator


def previous(previous_steps):
    """
    This decorator define previous steps of decorated input methods.
    You can use previous to decorate a test method.

    previous_steps - list of previous TestState subclasses names.
    """
    if not isinstance(previous_steps, list):
        raise TypeError('previous() take list of class names (got {})'
                        .format(type(previous_steps).__name__))

    def decorator(func):
        """
        Add previous_steps attribut to func
        """
        func.previous_steps = previous_steps
        return func

    return decorator
