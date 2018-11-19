# -*- coding: utf-8 -*-
#
from abc import ABCMeta, abstractmethod
import json
import requests
from pyldapi_client.functions import *


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
            return page, per_page
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
                if t in iter(self.item_classes):
                    contained = True
                    break
            if not contained:
                continue
            index[p["@id"]] = p
        return index


class AbstractBoundIndexPage(object):
    """
    TODO: Ashley
    """
    __metaclass__ = ABCMeta
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
        for k, i in self.index.iteritems():
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


class AbstractBoundRegister(object):
    """
    TODO: Ashley
    """
    __metaclass__ = ABCMeta
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


class BoundRegister(AbstractBoundRegister):
    """
    TODO: Ashley
    """
    __slots__ = tuple()

    def index_threaded(self, first, last):
        """
        Gets all of the ids of instances on this register
        Note, this can take a long time for a large dataset

        :param first:
        :type first:

        :param last:
        :type last:

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
        elif (chunks % num_threads) > 0:
            chunks += 1
        index = {}
        import threading
        pages = {}

        def _thread_job(i, p):
            """
            TODO: Ashley

            :param i:
            :type i:

            :param p:
            :type p:

            :return:
            :rtype:
            """
            try:
                result = self.index_page(page=p)
                pages[i] = result
            except Exception, e1:
                pages[i] = e1

        for c in xrange(chunks):
            jobs = []
            page_offset = c*8
            pages = {}
            for i, p in enumerate(xrange(page_offset+first, page_offset+first+num_threads)):
                page_job = threading.Thread(target=_thread_job, args=(i, p))
                page_job.start()
                jobs.append(page_job)
            for j in jobs:
                try:
                    j.join()
                except Exception:
                    pass
            for i, p in pages.iteritems():
                if p is None:
                    continue
                elif isinstance(p, Exception):
                    print p
                    continue
                try:
                    index.update(p.index)
                except Exception, e:
                    print e
                    continue
        return index

    def index(self):
        """
        Gets all of the ids of instances on this register
        Note, this can take a long time for a large dataset

        :return:
        :rtype: dict
        """

        current_page, current_per_page, first, last =\
            self.register.get_current_page_details()
        if last < first:
            last = first
        if last == first:
            return self.index_page(first).index
        if self.client.threads and self.client.threads > 1:
            return self.index_threaded(first, last)

        index = {}
        for p in xrange(first, last+1):
            page = self.index_page(page=p)
            if page is None:
                continue
            elif isinstance(page, Exception):
                print page
                continue
            try:
                index.update(page.index)
            except Exception, e:
                print e
                continue
        return index

    def instances(self, index=None, min_count=None):
        """
        Gets all of the instances on this register
        Note, this can take a _very_ long time for a large dataset

        :param index:
        :type index:

        :param min_count:
        :type min_count:

        :return:
        :rtype: dict
        """
        if index is None:
            index = self.index()
        if isinstance(index, dict):
            index = tuple(index.keys())
        if self.client.threads and self.client.threads > 1:
            return self.instances_threaded(index, min_count=min_count)
        instance_count = len(index)
        ret_dict = {}

        for p in xrange(0, instance_count):
            instance_uri = index[p]
            instance = self.instance(instance_uri)
            if instance is None:
                continue
            elif isinstance(instance, Exception):
                print instance
                continue
            try:
                ret_dict[instance_uri] = instance
            except Exception, e:
                print e
                continue
            if min_count is not None and len(ret_dict) >= min_count:
                break
        return ret_dict

    def instances_threaded(self, index, min_count=None):
        """
        Gets all of the instances on this register
        Note, this can take a _very_ long time for a large dataset

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
            except Exception, e:
                instances[_instance_uri] = e

        for c in xrange(chunks):
            jobs = []
            instances = {}
            for i, p in enumerate(xrange(0, num_threads)):
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
                    print instance
                    continue
                try:
                    ret_dict[identifier] = instance
                except Exception, e:
                    print e
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


class AbstractLDAPIClient(object):
    """
    TODO: Ashley
    """
    __metaclass__ = ABCMeta

    __slots__ = ('base_uri', 'url_remapper', '_registers', 'session')

    def __init__(self, base_uri, url_remapper=None, **kwargs):
        """
        TODO: Ashley

        :param base_uri:
        :type base_uri:

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
        :rtype:
        """
        pass

    def _remap_url(self, url):
        """
        TODO: Ashley

        :param url:
        :type url:

        :return:
        :rtype:
        """
        if self.url_remapper is None:
            return url
        for u, v in self.url_remapper.iteritems():
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

    def __init__(self, base_uri, url_remapper=None,
                 threads=1, **kwargs):
        """
        TODO: Ashley

        :param base_uri:
        :type base_uri:

        :param url_remapper:
        :type url_remapper:

        :param threads:
        :type threads:

        :param kwargs:
        :type kwargs:
        """
        async = kwargs.pop('asynchronous', False)
        if async:
            raise RuntimeError(
                "Cannot set asyncronous=True on the Python 2.7 "
                "version of ldapi-client.")
        super(LDAPIClient, self).__init__(
            base_uri, url_remapper=url_remapper, **kwargs)
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
        found_registers = registers.keys()
        for uri in found_registers:
            r = registers[uri]
            if not r.payload:
                url = self._remap_url(uri)
                response = self.session.get(url, headers=headers)
                if response.status_code != 200:
                    raise RuntimeError("Cannot get linked register: %s" % str(uri))
                text = response.text
                json_struct = json.loads(text)
                new_registers = find_registers_from_ld_payload(uri, json_struct, LoadedRegister)
                registers.update(new_registers)
        self._registers = registers

    def close(self):
        """
        TODO: Ashley

        :return:
        :rtype:
        """
        self.session.close()


__all__ = ['LDAPIClient']
