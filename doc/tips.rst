TIPS
====


Generate scenario with an other class than unittest.TestCase
------------------------------------------------------------

You can define the base class of generated TestCase using `base_class` attribute.
By default the used class is unittest.TestCase but you can use any unittest.TestCase subclass.

::

    class BaseTest(TestState):
        base_class = MyCustomTestCase


Create a custom client for TestServer class
-------------------------------------------

.. automodule:: cricri
  
    .. automethod:: MetaServerTestState.bind_class_client
    
