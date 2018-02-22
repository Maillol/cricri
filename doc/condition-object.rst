.. _condition-object:

Condition object
================

The Conditions objets are used in **condition** decorator.

You can combine Condition objects using operator.

+------------+------------+----------------------------------+
| Operator   | Meaning    | Example                          |
+============+============+==================================+
|  \-        | not        | \- Path('A', 'B')                |
+------------+------------+----------------------------------+
|  &         | and        | Path('A', 'B') & Path('F', 'G')  |
+------------+------------+----------------------------------+
|  \|        | or         | Path('A', 'B') \| Path('F', 'G') |
+------------+------------+----------------------------------+

Built-in Condition
------------------

Previous
~~~~~~~~

Previous(step [,step2 [...]]) is enable if last executed step is in given steps.

Example:

+-----------------------------------------------+
|       @condition(Previous("I", "J"))          |
+----------------+------------------------------+
| Executed steps | Decorated method is executed |
+================+==============================+
| K, I, J        | True                         |
+----------------+------------------------------+
| K, J, I        | True                         |
+----------------+------------------------------+
| J, I, K        | False                        |
+----------------+------------------------------+
| I, J, K        | False                        |
+----------------+------------------------------+
| J              | True                         |
+----------------+------------------------------+
| I              | True                         |
+----------------+------------------------------+

Path
~~~~

Path(step [,step2 [...]]) is enable if the given contigious steps have executed.

Example:

+-----------------------------------------------+
|        @condition(Path("I", "J"))             |
+----------------+------------------------------+
| Executed steps | Decorated method is executed |
+================+==============================+
| I, J           | True                         |
+----------------+------------------------------+
| J, I, J, I     | True                         |
+----------------+------------------------------+
| J, I           | False                        |
+----------------+------------------------------+
| I, K, J        | False                        |
+----------------+------------------------------+
| K, J           | False                        |
+----------------+------------------------------+

Newer
~~~~~

Newer(step1, step2) is enable if step2 execution is newer than step1 execution or step1 has not executed.

Example:

+-----------------------------------------------+
|        @condition(Newer("I", "J"))            |
+----------------+------------------------------+
| Executed steps | Decorated method is executed |
+================+==============================+
| I, J           | True                         |
+----------------+------------------------------+
| J, I, J, I     | False                        |
+----------------+------------------------------+
| J, I           | False                        |
+----------------+------------------------------+
| I, K, J        | True                         |
+----------------+------------------------------+
| K, J           | True                         |
+----------------+------------------------------+
| K, I           | False                        |
+----------------+------------------------------+


How to create a custom Condition
--------------------------------

You can create a custom Condition by inheriting from Condition class and overriding the \_\_call__ method.
The \_\_call__ method takes *previous_steps* parameter - *previous_steps* parameters is a list of executed step names -
and return True if decorated method must be executed else False.

Here is a Condition wich is enable when step appears a given number of times::

    class Count(Condition):

        def __init__(self, step, count):
            self.step = step
            self.count = count

        def __call__(self, previous_steps):
            previous_steps = tuple(previous_steps)
            return previous_steps.count(self.step) ==  self.count



Shortcut
--------

Cricri provides shortcut decorators:

+---------------------------------+--------------------------------------------+
| shortcut                        | means                                      |
+=================================+============================================+
| @previous(step [,step2 [...]])  | @conditon(Previous(step [,step2 [...]]))   |
+---------------------------------+--------------------------------------------+
| @path(step [,step2 [...]])      | @conditon(Path(step [,step2 [...]]))       |
+---------------------------------+--------------------------------------------+
| @newer(step1, step2)            | @conditon(Newer(step1, step2))             |
+---------------------------------+--------------------------------------------+



