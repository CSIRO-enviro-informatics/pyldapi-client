# -*- coding: utf-8 -*-
#
import asyncio
from abc import ABCMeta, abstractmethod

import aiohttp
import requests
import json
from pyldapi_client.functions import *
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class LoadedRegister(object):
    """
    TODO: Ashley
    """
    __slots__ = ('uri', 'item_classes', 'payload')

    def __init__(self, uri, item_classes=None, payload=None):
        """
        TODO: Ashley

        :param uri:
        :type uri:

        :param item_classes:
        :type item_classes:

        :param payload:
        :type payload:
        """
        self.uri = uri
        self.item_classes = item_classes or []
        self.payload = payload

    def get_current_page_details(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        page = 1
        per_page = 100
        first = 1
        last = 1
        if not self.payload:
            return page, per_page, first, last
        for p in self.payload:
            if "@type" in p and ldp_Page in p['@type']:
                page_string = str(p['@id'])
                ex_page = extract_page_from_string(page_string)
                ex_per_page = extract_per_page_from_string(page_string)
                page = ex_page or page
                per_page = ex_per_page or per_page
                if vocab_first in p and len(p[vocab_first]) > 0:
                    page_string = p[vocab_first][0]['@id']
                    ex_first_page = extract_page_from_string(page_string)
                    first = ex_first_page or first
                if vocab_last in p and len(p[vocab_last]) > 0:
                    page_string = p[vocab_last][0]['@id']
                    ex_last_page = extract_page_from_string(page_string)
                    last = ex_last_page or last
                break
        return page, per_page, first, last

    def make_instance_uri(self, identifier):
        """
        TODO: Ashley

        :param identifier:
        :type identifier:

        :return:
        :rtype:
        """
        if identifier.startswith("http:") or identifier.startswith("https:"):
            pass
        else:
            identifier = "/".join([self.uri.rstrip('/'), identifier])
        return identifier

    def filter_index(self, payload):
        """
        TODO: Ashley

        :param payload:
        :type payload:

        :return:
        :rtype:
        """
        index = {}
        for p in payload:
            if "@id" not in p:
                continue
            if "@type" not in p:
                continue
            contained = False
            for t in p['@type']:
                if t in self.item_classes:
                    contained = True
                    break
            if not contained:
                continue
            index[p["@id"]] = p
        return index


class AbstractBoundIndexPage(object, metaclass=ABCMeta):
    """
    TODO: Ashley
    """
    __slots__ = ('register', 'index', 'page', 'per_page', 'first', 'last')

    def __init__(self, register, index, page, per_page, first, last):
        """
        TODO: Ashley

        :param register:
        :type register:

        :param index:
        :type index:

        :param page:
        :type page:

        :param per_page:
        :type per_page:

        :param first:
        :type first:

        :param last:
        :type last:
        """
        self.register = register
        self.index = index
        self.page = page
        self.per_page = per_page
        self.first = first
        self.last = last

    def items(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        for k, i in self.index.items():
            yield k, i



class BoundIndexPage(AbstractBoundIndexPage):
    """
    TODO: Ashley
    """
    __slots__ = tuple()

    def prev_page(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        if self.page == 1 or self.page <= self.first:
            return None
        index = self.register.index_page(self.page - 1, self.per_page)
        return index

    def next_page(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        if self.page >= self.last:
            return None
        index = self.register.index_page(self.page + 1, self.per_page)
        return index



class AsyncBoundIndexPage(AbstractBoundIndexPage):
    """
    TODO: Ashley
    """
    __slots__ = tuple()

    async def prev_page(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        if self.page == 1 or self.page <= self.first:
            return None
        index = await self.register.index_page(self.page - 1, self.per_page)
        return index

    async def next_page(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        if self.page >= self.last:
            return None
        index = await self.register.index_page(self.page + 1, self.per_page)
        return index

class AbstractBoundRegister(object, metaclass=ABCMeta):
    """
    TODO: Ashley
    """
    __slots__ = ('register', 'client')

    def __init__(self, register, client):
        """
        TODO: Ashley

        :param register:
        :type register:

        :param client:
        :type client:
        """
        self.register = register
        self.client = client


class AsyncBoundRegister(AbstractBoundRegister):
    """
    TODO: Ashley
    """
    __slots__ = tuple()

    async def index(self, offset=None, min_count=None):
        """
        Gets all of the IDs of instances on this register.

        Note: this can take a long time for a large dataset

        :return:
        :rtype: dict
        """
        current_page, current_per_page, first, last =\
            self.register.get_current_page_details()
        if last < first:
            last = first
        if last == first and offset is None:
            page = await self.index_page(first)
            return page.index
        if offset and offset > 0:
            offset_pages = offset // current_per_page
            offset_entries = offset - (offset_pages * current_per_page)
            first = first+offset_pages
            last = last+offset_pages
        else:
            offset_entries = 0
        # plus 1 because first and last are inclusive.
        total_pages = (last - first) + 1
        if total_pages < 1:
            total_pages = 1
        chunks = total_pages // 8
        if chunks < 1:
            chunks = 1
        elif (total_pages % 8) > 0:
            chunks += 1
        index = {}
        for c in range(chunks):
            jobs = []
            page_offset = c*8
            for p in range(page_offset+first, page_offset+first+8):
                page_job = self.index_page(page=p)
                jobs.append(page_job)
            awaitable = asyncio.gather(*jobs, return_exceptions=True)
            pages = await awaitable
            for p in pages:
                if p is None:
                    continue
                elif isinstance(p, Exception):
                    print(p)
                    continue
                if offset_entries:
                    skip_entries = sorted(p.index.keys())[:offset_entries]
                    for s in skip_entries:
                        _ = p.index.pop(s)
                    offset_entries = 0
                try:
                    index.update(p.index)
                except Exception as e:
                    print(e)
                    continue
            if min_count is not None and len(index) >= min_count:
                break
        return index

    async def instances(self, index=None, min_count=None):
        """
        Gets all of the instances on this register.

        Note: this can take a *very* long time for a large dataset.

        :return:
        :rtype: dict
        """
        if index is None:
            index = await self.index()
        if isinstance(index, dict):
            index = tuple(index.keys())
        instance_count = len(index)
        chunks = instance_count // 8
        if chunks < 1:
            chunks = 1
        elif (instance_count % 8) > 0:
            chunks += 1
        ret_dict = {}

        async def _get_instance_for_key(_instance_uri):
            nonlocal self
            _instance = await self.instance(_instance_uri)
            return _instance_uri, _instance

        for c in range(chunks):
            jobs = []
            for p in range(0, 8):
                _offset = (c*8)+p
                if _offset >= instance_count:
                    break
                instance_uri = index[_offset]
                instance_job = _get_instance_for_key(instance_uri)
                jobs.append(instance_job)
            awaitable = asyncio.gather(*jobs, return_exceptions=True)
            completed_jobs = await awaitable
            for completed_job in completed_jobs:
                identifier, instance = completed_job
                if instance is None:
                    continue
                elif isinstance(instance, Exception):
                    print(instance)
                    continue
                try:
                    ret_dict[identifier] = instance
                except Exception as e:
                    print(e)
                    continue
            if min_count is not None and len(ret_dict) >= min_count:
                break
        return ret_dict

    async def index_page(self, page=None, per_page=None):
        """
        TODO: Ashley

        :param page:
        :type page:

        :param per_page:
        :type per_page:

        :return:
        :rtype:
        """
        current_page, current_per_page, first, last = self.register.get_current_page_details()
        if page is None:
            page = current_page or 1
        if per_page is None:
            per_page = current_per_page or 100
        first = first or 1
        last = last or 1
        if page < 1:
            raise RuntimeError("Cannot execute an index call to register page less-than 1.")
        if per_page < 1:
            raise RuntimeError("Cannot execute an index call to register with items-per-page less-than 1.")
        if page == current_page and per_page == current_per_page:
            payload = self.register.payload
        else:
            payload = await self.client._get_register_index(self.register.uri, page, per_page)
            if not payload:
                return None
            self.register.payload = payload
            current_page, current_per_page, first, last = self.register.get_current_page_details()
        index = self.register.filter_index(payload)
        return AsyncBoundIndexPage(self, index, current_page, current_per_page, first, last)

    async def instance(self, identifier):
        """
        TODO: Ashley

        :param identifier:
        :type identifier:

        :return:
        :rtype:
        """
        id_uri = self.register.make_instance_uri(identifier)
        resp = await self.client._get_register_instance(self.register.uri, id_uri)
        return resp


class BoundRegister(AbstractBoundRegister):
    """
    TODO: Ashley
    """
    __slots__ = tuple()

    def _index_threaded(self, first, last, offset_entries, min_count):
        """
        Gets all of the ids of instances on this register.

        Note: this can take a long time for a large dataset.

        :return:
        :rtype: dict
        """
        # plus 1 because first and last are inclusive.
        num_threads = int(self.client.threads)
        total_pages = (last - first) + 1
        if total_pages < 1:
            total_pages = 1
        chunks = total_pages // num_threads
        if chunks < 1:
            chunks = 1
        elif (total_pages % num_threads) > 0:
            chunks += 1
        index = {}
        import threading
        pages = {}

        def _thread_job(i, p):
            nonlocal self
            nonlocal pages
            try:
                result = self.index_page(page=p)
                pages[i] = result
            except Exception as e:
                pages[i] = e

        for c in range(chunks):
            jobs = []
            c_page_offset = c*8
            pages = {}
            for i, p in enumerate(range(c_page_offset+first, c_page_offset+first+num_threads)):
                page_job = threading.Thread(target=_thread_job, args=(i, p))
                page_job.start()
                jobs.append(page_job)
            for j in jobs:
                try:
                    j.join()
                except Exception:
                    pass
            for i, p in pages.items():
                if p is None:
                    continue
                elif isinstance(p, Exception):
                    print(p)
                    continue
                if offset_entries:
                    skip_entries = sorted(p.index.keys())[:offset_entries]
                    for s in skip_entries:
                        _ = p.index.pop(s)
                    offset_entries = 0
                try:
                    index.update(p.index)
                except Exception as e:
                    print(e)
                    continue
            if min_count is not None and len(index) >= min_count:
                break
        return index

    def index(self, offset=None, min_count=None):
        """
        Gets all of the ids of instances on this register

        Note: this can take a long time for a large dataset

        :return:
        :rtype: dict
        """

        current_page, current_per_page, first, last =\
            self.register.get_current_page_details()
        if last < first:
            last = first
        if last == first and offset is None:
            return self.index_page(first).index
        if offset and offset > 0:
            offset_pages = offset // current_per_page
            offset_entries = offset - (offset_pages * current_per_page)
            first = first+offset_pages
            last = last+offset_pages
        else:
            offset_entries = 0
        if self.client.threads and self.client.threads > 1:
            return self._index_threaded(first, last, offset_entries, min_count)
        index = {}
        for p in range(first, last+1):
            page = self.index_page(page=p)
            if page is None:
                continue
            elif isinstance(page, Exception):
                print(page)
                continue
            if offset_entries:
                skip_entries = sorted(page.index.keys())[:offset_entries]
                for s in skip_entries:
                    _ = page.index.pop(s)
                offset_entries = 0
            try:
                index.update(page.index)
            except Exception as e:
                print(e)
                continue
            if min_count is not None and len(index) >= min_count:
                break
        return index

    def instances(self, index=None, min_count=None):
        """
        Gets all of the instances on this register.
        Note: this can take a *very* long time for a large dataset.

        :return:
        :rtype: dict
        """
        if index is None:
            index = self.index()
        if isinstance(index, dict):
            index = tuple(index.keys())
        if self.client.threads and self.client.threads > 1:
            return self._instances_threaded(index, min_count)
        instance_count = len(index)
        ret_dict = {}

        for p in range(0, instance_count):
            instance_uri = index[p]
            instance = self.instance(instance_uri)
            if instance is None:
                continue
            elif isinstance(instance, Exception):
                print(instance)
                continue
            try:
                ret_dict[instance_uri] = instance
            except Exception as e:
                print(e)
                continue
            if min_count is not None and len(ret_dict) >= min_count:
                break
        return ret_dict

    def _instances_threaded(self, index, min_count):
        """
        Gets all of the instances on this register.
        Note: this can take a *very* long time for a large dataset.

        :return:
        :rtype: dict
        """
        num_threads = int(self.client.threads)
        if isinstance(index, dict):
            index = tuple(index.keys())
        instance_count = len(index)
        chunks = instance_count // num_threads
        if chunks < 1:
            chunks = 1
        elif (instance_count % num_threads) > 0:
            chunks += 1

        ret_dict = {}
        import threading
        instances = {}
        def _get_instance_for_key(i, _instance_uri):
            nonlocal self
            nonlocal instances
            try:
                _instance = self.instance(_instance_uri)
                instances[_instance_uri] = _instance
            except Exception as e:
                instances[_instance_uri] = e

        for c in range(chunks):
            jobs = []
            instances = {}
            for i, p in enumerate(range(0, num_threads)):
                _offset = (c*8)+p
                if _offset >= instance_count:
                    break
                instance_uri = index[_offset]
                instance_job = threading.Thread(target=_get_instance_for_key, args=(i, instance_uri))
                instance_job.start()
                jobs.append(instance_job)
            for j in jobs:
                try:
                    j.join()
                except Exception:
                    pass
            for identifier, instance in instances.items():
                if instance is None:
                    continue
                elif isinstance(instance, Exception):
                    print(instance)
                    continue
                try:
                    ret_dict[identifier] = instance
                except Exception as e:
                    print(e)
                    continue
            if min_count is not None and len(ret_dict) >= min_count:
                break
        return ret_dict

    def index_page(self, page=None, per_page=None):
        """
        TODO: Ashley

        :param page:
        :type page:

        :param per_page:
        :type per_page:

        :return:
        :rtype:
        """
        current_page, current_per_page, first, last = self.register.get_current_page_details()
        if page is None:
            page = current_page or 1
        if per_page is None:
            per_page = current_per_page or 100
        first = first or 1
        last = last or 1
        if page < 1:
            raise RuntimeError("Cannot execute an index call to register page less-than 1.")
        if per_page < 1:
            raise RuntimeError("Cannot execute an index call to register with items-per-page less-than 1.")
        if page == current_page and per_page == current_per_page:
            payload = self.register.payload
        else:
            payload = self.client._get_register_index(self.register.uri, page, per_page)
            if not payload:
                return None
            self.register.payload = payload
            current_page, current_per_page, first, last = self.register.get_current_page_details()
        index = self.register.filter_index(payload)
        return BoundIndexPage(self, index, current_page, current_per_page, first, last)

    def instance(self, identifier):
        """
        TODO: Ashley

        :param identifier:
        :type identifier:

        :return:
        :rtype:
        """
        uri = self.register.make_instance_uri(identifier)
        resp = self.client._get_register_instance(self.register.uri, uri)
        return resp


class AbstractLDAPIClient(object, metaclass=ABCMeta):
    """
    TODO: Ashley
    """
    __slots__ = ('base_uri', 'url_remapper', '_registers', 'session')

    def __init__(self, base_uri, *args, url_remapper=None, **kwargs):
        """
        TODO: Ashley

        :param base_uri:
        :type base_uri:

        :param args:
        :type args:

        :param url_remapper:
        :type url_remapper:

        :param kwargs:
        :type kwargs:
        """
        self.base_uri = base_uri
        self.url_remapper = url_remapper
        self._registers = {}
        self.session = requests.Session()
        self._populate_registers()

    @abstractmethod
    def _populate_registers(self):
        """
        TODO: Ashley

        :return:
        """
        pass

    def _remap_url(self, url):
        """
        TODO: Ashley

        :param url:
        :type url:

        :return:
        """
        if self.url_remapper is None:
            return url
        for u, v in self.url_remapper.items():
            if url.startswith(u):
                url = url.replace(u, v)
                break
        return url

    @abstractmethod
    def register(self, reg_uri):
        """
        TODO: Ashley

        :param reg_uri:
        :type reg_uri:

        :return:
        :rtype:
        """
        pass


class LDAPIClient(AbstractLDAPIClient):
    """
    TODO: Ashley
    """
    __slots__ = ('threads',)

    def __new__(cls, *args, asynchronous=False, **kwargs):
        """
        TODO: Ashley

        :param args:
        :type args:

        :param asynchronous:
        :type asynchronous:

        :param kwargs:
        :type kwargs:

        :return:
        :rtype:
        """
        if asynchronous:
            return AsyncLDAPIClient(*args, **kwargs)
        self = super(LDAPIClient, cls).__new__(cls)
        return self

    def __init__(self, base_uri, *args, url_remapper=None,
                 threads=1, **kwargs):
        """

        :param base_uri:
        :type base_uri:

        :param args:
        :type args:

        :param url_remapper:
        :type url_remapper:

        :param threads:
        :type threads:

        :param kwargs:
        :type kwargs:
        """
        super(LDAPIClient, self).__init__(
            base_uri, *args, url_remapper=url_remapper, **kwargs)
        self.threads = threads

    def register(self, reg_uri):
        """
        TODO: Ashley

        :param reg_uri:
        :type reg_uri:

        :return:
        :rtype:
        """
        try:
            register = self._registers[reg_uri]
        except KeyError as k:
            raise ValueError(*k.args)
        return BoundRegister(register, client=self)

    def _get_register_instance(self, register_uri, instance_uri):
        """
        TODO: Ashley

        :param register_uri:
        :type register_uri:

        :param instance_uri:
        :type instance_uri:

        :return:
        :rtype:
        """
        headers = {
            "Accept": "application/ld+json",
            "Accept-Profile": "http://purl.org/linked-data/registry"
        }
        url = self._remap_url(instance_uri)
        resp = self.session.get(url, headers=headers)
        if resp.status_code == 404:
            raise RuntimeError((404, instance_uri))
        elif resp.status_code == 500:
            raise RuntimeError((500, instance_uri))
        if resp.status_code != 200:
            return resp.status_code
        text = resp.text
        payload = json.loads(text)
        return payload

    def _get_register_index(self, register_uri, page=1, per_page=100):
        """
        TODO: Ashley

        :param register_uri:
        :type register_uri:

        :param page:
        :type page:

        :param per_page:
        :type per_page:

        :return:
        :rtype:
        """
        headers = {
            "Accept": "application/ld+json",
            "Accept-Profile": "http://purl.org/linked-data/registry"
        }
        url = self._remap_url(register_uri)
        resp = self.session.get(
            url, headers=headers,
            params={'page': page, 'per_page': per_page},
            timeout=900
        )
        if resp.status_code != 200:
            return None
        text = resp.text
        payload = json.loads(text)
        return payload

    def _populate_registers(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        headers = {
            "Accept": "application/ld+json",
            "Accept-Profile": "http://purl.org/linked-data/registry"
        }
        url = self._remap_url(self.base_uri)
        response = self.session.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError("Cannot get base register.")
        text = response.text
        json_struct = json.loads(text)
        registers = find_registers_from_ld_payload(self.base_uri, json_struct, LoadedRegister)
        first_registers = list(registers.keys())
        for uri in first_registers:
            r = registers[uri]
            if not r.payload:
                url = self._remap_url(uri)
                response = self.session.get(url, headers=headers)
                if response.status_code != 200:
                    raise RuntimeError("Cannot get linked register: {}".format(uri))
                text = response.text
                json_struct = json.loads(text)
                new_registers = find_registers_from_ld_payload(uri, json_struct, LoadedRegister)
                registers.update(new_registers)
        self._registers = registers

    def close(self):
        self.session.close()


class AsyncLDAPIClient(AbstractLDAPIClient):
    """
    TODO: Ashley
    """
    __slots__ = ('_loop',)

    def __new__(cls, *args, loop=None, **kwargs):
        """
        TODO: Ashley

        :param args:
        :type args:

        :param loop:
        :type loop:

        :param kwargs:
        :type kwargs:

        :return:
        :rtype:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        self = super(AsyncLDAPIClient, cls).__new__(cls)
        self._loop = loop
        asyncio.set_event_loop(loop)
        return self.__async_init__(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        """
        TODO: Ashley

        :param args:
        :type args:

        :param kwargs:
        :type kwargs:
        """
        # deliberately don't call super init here, because we use an async init
        object.__init__(self)

    def register(self, reg_uri):
        """
        TODO: Ashley

        :param reg_uri:
        :type reg_uri:

        :return:
        :rtype:
        """
        try:
            register = self._registers[reg_uri]
        except KeyError as k:
            raise ValueError(*k.args)
        return AsyncBoundRegister(register, client=self)

    async def _get_register_instance(self, register_uri, instance_uri):
        """
        TODO: Ashley

        :param register_uri:
        :type register_uri:

        :param instance_uri:
        :type instance_uri:

        :return:
        :rtype:
        """
        headers = {
            "Accept": "application/ld+json",
            "Accept-Profile": "http://purl.org/linked-data/registry"
        }
        url = self._remap_url(instance_uri)
        resp = await self.session.get(url, headers=headers)
        if resp.status != 200:
            return resp.status
        text = await resp.text()
        payload = json.loads(text)
        return payload

    async def _get_register_index(self, register_uri, page=1, per_page=100):
        """
        TODO: Ashley

        :param register_uri:
        :type register_uri:

        :param page:
        :type page:

        :param per_page:
        :type per_page:

        :return:
        :rtype:
        """
        headers = {
            "Accept": "application/ld+json",
            "Accept-Profile": "http://purl.org/linked-data/registry"
        }
        url = self._remap_url(register_uri)
        resp = await self.session.get(
            url, headers=headers,
            params={'page': page, 'per_page': per_page},
            timeout=900
        )
        if resp.status != 200:
            return None
        text = await resp.text()
        payload = json.loads(text)
        return payload

    async def _populate_registers(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        headers = {
            "Accept": "application/ld+json",
            "Accept-Profile": "http://purl.org/linked-data/registry"
        }
        url = self._remap_url(self.base_uri)
        response = await self.session.get(url, headers=headers)
        if response.status != 200:
            raise RuntimeError("Cannot get base register.")
        text = await response.text()
        json_struct = json.loads(text)
        registers = find_registers_from_ld_payload(self.base_uri, json_struct, LoadedRegister)
        first_registers = list(registers.keys())
        for uri in first_registers:
            r = registers[uri]
            if not r.payload:
                url = self._remap_url(uri)
                response = await self.session.get(url, headers=headers, params={"per_page": 1})
                if response.status != 200:
                    raise RuntimeError("Cannot get linked register: {}".format(uri))
                text = await response.text()
                json_struct = json.loads(text)
                new_registers = find_registers_from_ld_payload(uri, json_struct, LoadedRegister)
                registers.update(new_registers)
        self._registers = registers

    async def __async_init__(self, base_uri, *args, url_remapper=None, **kwargs):
        """
        TODO: Ashley

        :param base_uri:
        :type base_uri:

        :param args:
        :type args:

        :param url_remapper:
        :type url_remapper:

        :param kwargs:
        :type kwargs:

        :return:
        :rtype:
        """
        self.base_uri = base_uri
        self.url_remapper = url_remapper
        self._registers = {}
        self.session = aiohttp.ClientSession()
        await self._populate_registers()
        return self

    async def close(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        r = await self.session.close()
        return r

    @property
    def loop(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        return self._loop



__all__ = ['LDAPIClient']
