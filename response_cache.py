'''
This is our really simple cache class. It's more-or-less a key-value store of URL's to GET responses.
'''
from datetime import datetime
import pytz
import sys

class ResponseCache:

    def __init__(self, cache_duration_ms = 30 * 1000, cache_size_bytes = 1024, cache_size_elements = 100):
        self.cache_duration_ms   = cache_duration_ms
        self.cache_size_bytes    = cache_size_bytes
        self.cache_size_elements = cache_size_elements
        self.validate_configuration(cache_duration_ms, cache_size_bytes, cache_size_elements)
        self.cache_dict = {}

    def __contains__(self, key):
        return key in self.cache_dict

    def __getitem__(self, item):
        return self.cache_dict[item]

    def __iter__(self):
        return iter(self.cache_dict)

    def length(self):
        return len(self.cache_dict)

    def size_bytes(self):
        return 0

    def validate_configuration(self, cache_duration_ms, cache_size_bytes, cache_size_elements):
        if cache_duration_ms <= 0:
            raise Exception("ResponseCache: CACHE_DURATION_MS must be greater than 0")
        if cache_size_bytes <= 0:
            raise Exception("ResponseCache: CACHE_SIZE_BYTES must be greater than 0")
        if cache_size_elements <= 0:
            raise Exception("ResponseCache: CACHE_SIZE_ELEMENTS must be greater than 0")

    def get_time(self, url):
        return self.cache_dict[url]['last_updated'].strftime("%Y-%m-%d %H:%M:%S %Z")

    def get_size(self, url):
        return sys.getsizeof(self.cache_dict[url])

    def get_total_size(self):
        size = 0
        for url in self.cache_dict:
            size += self.get_size(url)
        return size

    def insert(self, url, response):
        if url in self.cache_dict:
            return self.cache_dict[url]
        else:
            result = self.cache_dict[url] = {'response': response, "last_updated": datetime.now(pytz.timezone("US/Pacific"))}
            return result

    def delete(self, url):
        del self.cache_dict[url]
