Welcome to pyLDAPI Client
=========================

The Python client library for the Python Linked Data API (pyLDAPI) is:

*A Simple helper library for consuming registers, indexes, and instances of classes exposed via a pyLDAPI endpoint.*

See the `pyLDAPI`_ module for more information.

.. _pyLDAPI: https://pyldapi.readthedocs.io/

PyPI Badge - *coming soon*

Example usage
-------------

.. code-block:: python
    :linenos:

    from pyldapi_client import LDAPIClient

    async def async_test_script(loop):
        remapper = {
            "http://test.linked.data.gov.au/dataset/asgs/": "http://13.236.122.60/asgs/sa4/"
        }
        base = "http://test.linked.data.gov.au/dataset/asgs/reg"
        client = await LDAPIClient(base, url_remapper=remapper, asynchronous=True, loop=loop)
        register = client.register("http://test.linked.data.gov.au/dataset/asgs/sa4/")
        first_page = await register.index_page(per_page=50)
        a = await register.index()
        instances = await register.instances(index=a, min_count=20)
        _ = await client.close()
        print(len(a))
        print(len(instances))
        return

    def threaded_test_script():
        remapper = {
            "http://test.linked.data.gov.au/dataset/asgs/": "http://13.236.122.60/asgs/sa4/"
        }
        base = "http://test.linked.data.gov.au/dataset/asgs/reg"
        client = LDAPIClient(base, url_remapper=remapper, asynchronous=False, threads=8)
        register = client.register("http://test.linked.data.gov.au/dataset/asgs/sa4/")
        first_page = register.index_page(per_page=50)
        a = register.index()
        instances = register.instances(index=a, min_count=20)
        client.close()
        print(len(a))
        print(len(instances))
        return

    def sync_test_script():
        remapper = {
            "http://test.linked.data.gov.au/dataset/asgs/": "http://13.236.122.60/asgs/sa4/"
        }
        base = "http://test.linked.data.gov.au/dataset/asgs/reg"
        client = LDAPIClient(base, url_remapper=remapper, asynchronous=False, threads=1)
        register = client.register("http://test.linked.data.gov.au/dataset/asgs/sa4/")
        first_page = register.index_page(per_page=50)
        a = register.index()
        instances = register.instances(index=a, min_count=20)
        client.close()
        print(len(a))
        print(len(instances))
        return


    if __name__ == "__main__":
        import asyncio
        # For debugging/testing
        threaded_test_script()
        sync_test_script()
        loop = asyncio.get_event_loop()
        _a = async_test_script(loop)
        loop.run_until_complete(_a)



Documentation
-------------

Read the documentation at `http://pyldapi-client.readthedocs.io/`_.

.. _http://pyldapi-client.readthedocs.io/: http://pyldapi-client.readthedocs.io/


Implementations of pyLDAPI Client
---------------------------------

* **LOC-I Index File Exporter**


Licence
-------

This module is licensed under Apache Software License v2.0. See the `LICENSE deed`_ for details.

.. _LICENSE deed: https://raw.githubusercontent.com/CSIRO-enviro-informatics/pyldapi-client/master/LICENSE.txt


Contact
-------

Nicholas Car (lead)
~~~~~~~~~~~~~~~~~~~
| *Senior Experimental Scientist*
| `CSIRO Land and Water`_
| `nicholas.car@csiro.au`_
| `http://orcid.org/0000-0002-8742-7730`_

.. _nicholas.car@csiro.au: nicholas.car@csiro.au
.. _http://orcid.org/0000-0002-8742-7730: http://orcid.org/0000-0002-8742-7730

Ashley Sommer (senior developer)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
| *Informatics Software Engineer*
| `CSIRO Land and Water`_
| `ashley.sommer@csiro.au`_

.. _ashley.sommer@csiro.au: ashley.sommer@csiro.au

.. _CSIRO Land and Water: https://www.csiro.au/en/Research/LWF