import xbmc
import json
from .filter import SimpleFilter, ComplexFilter
import web_pdb

class RPC:
    def __init__(self, core, method, request_id):
        self.core = core
        self.method = method
        self.params = {}
        self.properties = []
        self.limits = Limits()
        self.filter = None
        self.request_id = request_id
        self.sort = Sort()

    def add_param(self, key, value):
        self.params[key] = value

    def add_property(self, field):
        self.properties.append(field)

    def set_page(self, page):
        self.limits.set_page(page)

    def set_sort_field(self, field):
        self.sort.set_field(field)

    def has_limits(self):
        if self.method == 'AudioLibrary.GetArtists':
            return True
        if self.method == 'AudioLibrary.GetSongs':
            return True

        return False

    def has_sort(self):
        if self.method == 'AudioLibrary.GetArtists':
            return True
        if self.method == 'AudioLibrary.GetSongs':
            return True
        return False

    def set_filter(self, rpc_filter):
        self.filter = rpc_filter
        return self

    def has_filter(self):
        if self.filter is None:
            return False
        if isinstance(self.filter, SimpleFilter):
            return True
        if isinstance(self.filter, ComplexFilter):
            return self.filter.has_filter()

    def get_params(self):
        params = self.params
        if self.has_limits():
            params['limits'] = self.limits.get_payload()
        if self.has_sort():
            params['sort'] = self.sort.get_payload()
        if self.has_filter():
            params['filter'] = self.filter.get_payload()
        if len(self.properties):
            params['properties'] = self.properties
        return params

    def __str__(self):
        payload = {
            "jsonrpc": "2.0",
            "method": self.method,
            "id": self.request_id
        }
        params = self.get_params()

        if len(params):
            payload['params'] = params
        return json.dumps(payload)

    def execute(self):
        request = self.__str__()
        self.core.log.debug('Executing json/rpc: %s', request)
        return json.loads(xbmc.executeJSONRPC(request))


class Limits:
    def __init__(self):
        self.start = 0
        self.end = 99
        self.page_size = 100
        self.page = 1

    def set_start(self, start):
        self.start = start

    def set_end(self, end):
        self.end = end

    def set_page(self, page):
        self.page = page
        start = (page - 1) * self.page_size
        self.set_start(start)
        self.set_end(start + self.page_size)

    def get_payload(self):
        return {
            "start": self.start,
            "end": self.end
        }


class Sort:
    def __init__(self):
        self.field = None
        self.order = 'ascending'
        self.ignore_article = True

    def set_field(self, field):
        self.field = field

    def get_payload(self):
        return {
            "order": self.order,
            "method": self.field,
            "ignorearticle": self.ignore_article
        }

