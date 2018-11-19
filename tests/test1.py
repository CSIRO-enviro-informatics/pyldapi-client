"""
TODO: Ashley
"""

from pyldapi_client import LDAPIClient

async def async_test_script(loop):
    remapper = {
        "http://test.linked.data.gov.au/dataset/asgs/": "http://localhost:5000/"
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
        "http://test.linked.data.gov.au/dataset/asgs/": "http://localhost:5000/"
    }
    base = "http://test.linked.data.gov.au/dataset/asgs/reg"
    client = LDAPIClient(base, url_remapper=remapper, asynchronous=False, threads=8)
    register = client.register("http://test.linked.data.gov.au/dataset/asgs/sa4/")
    first_page = register.index_page(per_page=50)
    a = register.index()
    instances = register.instances(index=a, min_count=20)
    client.close()
    # import pickle
    # with open("sa4_index.pickle", 'wb') as f:
    #     pickle.dump(a, f)
    print(len(a))
    print(len(instances))
    return

def sync_test_script():
    remapper = {
        "http://test.linked.data.gov.au/dataset/asgs/": "http://localhost:5000/"
    }
    base = "http://test.linked.data.gov.au/dataset/asgs/reg"
    client = LDAPIClient(base, url_remapper=remapper, asynchronous=False, threads=1)
    register = client.register("http://test.linked.data.gov.au/dataset/asgs/sa4/")
    first_page = register.index_page(per_page=50)
    a = register.index()
    instances = register.instances(index=a, min_count=20)
    client.close()
    # import pickle
    # with open("state_index.pickle", 'wb') as f:
    #     pickle.dump(a, f)
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
