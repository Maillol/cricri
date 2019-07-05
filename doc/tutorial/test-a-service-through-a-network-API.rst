
Test a service through a network API
====================================

Throughout this tutorial, we're going to write tests for a service that store action about hotels.
The API of this service is a REST API.


+-------+--------------------+-----------------------+---------------+
|HTTP   | URL                | DESCRIPTION           | Status        |
|METHOD |                    |                       | Code          |
+=======+====================+=======================+===============+
|GET    | /hotels            | Get all hotels        | 200 0K        |
+-------+--------------------+-----------------------+---------------+
|GET    | /hotels/<hotel_id> | Get hotel             | 200 0K        |
|       |                    |                       | 404 Not Found |
+-------+--------------------+-----------------------+---------------+
|DELETE | /hotels/<hotel_id> | Delete hotel          | 204 Deleted   |
|       |                    |                       | 404 Not Found |
+-------+--------------------+-----------------------+---------------+
|POST   | /hotels            | Create hotel          | 201 Created   |
+-------+--------------------+-----------------------+---------------+



We'll create file **test_hotel.py** and and put the following Python code in it:


.. code-block:: python


    from cricri import InetTestCase


    class TestHotelService(InetTestCase):


         http_clients = [
            {
                "name": "Alice",
                "host": "127.0.0.1",
                "port": "{port-1}",
                "extra_headers": [
                    ('Content-Type', 'application/json')
                ]
            }
        ]

        commands = [
            {
                "name": "hotel_service",
                "cmd": ["python3", "-u", "-m", "rest", "{port-1}"],
                "extra-env": {
                    "PYTHONPATH": os.environ.get('PYTHONPATH')
                },
                "kill-signal": signal.SIGKILL
            }
        ]



The **TestHotelService** define a http client and the command to launch the hotel_service.

TODO continue tutorial

