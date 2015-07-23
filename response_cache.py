'''
This is our really simple cache class. It's more-or-less a key-value store of URL's to GET responses.
'''
class ResponseCache:

    def __init__(self, cache_duration_ms = 30 * 1000, cache_size_bytes = 1024, cache_size_elements = 100):
        print "Instantiating a ResponseCache"
        self.validate_conf(cache_duration_ms, cache_size_bytes, cache_size_elements)
        self.cache_dict = {}

    def validate_conf(self, cache_duration_ms, cache_size_bytes, cache_size_elements):
        if cache_duration_ms <= 0:
            raise Exception("ResponseCache: CACHE_DURATION_MS must be greater than 0")
        if cache_size_bytes <= 0:
            raise Exception("ResponseCache: CACHE_SIZE_BYTES must be greater than 0")
        if cache_size_elements <= 0:
            raise Exception("ResponseCache: CACHE_SIZE_ELEMENTS must be greater than 0")

    def get(self, request=None):
        if request not in self.cache_dict:
            self.cache_dict[request] = "REQUEST"
        else:
            return self.cache_dict[request]