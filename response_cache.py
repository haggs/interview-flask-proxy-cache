#########################################################################################################
# This is our really simple cache class. It's more-or-less a key-value store of URL's to GET responses.
#########################################################################################################
from flask import request
import requests
from urlparse import urlparse
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
        return sys.getsizeof(self.cache_dict[url]['response'])

    def get_total_size(self):
        size = 0
        for url in self.cache_dict:
            size += self.get_size(url)
        return size

    def cache_expired(self, url):
        age_ms = datetime.now(pytz.timezone("US/Pacific")) - self.cache_dict[url]['last_updated']
        if age_ms.seconds * 1000 + age_ms.microseconds / 1000 > self.cache_duration_ms:
            return True
        return False

    def delete_oldest(self):
        oldest = datetime.now(pytz.timezone("US/Pacific"))
        for url in self.cache_dict:
            if self.cache_dict[url]['last_updated'] < oldest:
                self.delete(url)
                break

    def insert(self, url):
        print "Inserting URL:", url

        # If adding this element puts us over our cache size (elements) limit, delete this oldest record
        if len(self.cache_dict) + 1 > self.cache_size_elements:
            print "Reached cache element limit, deleting oldest record"
            self.delete_oldest()

        # Fetch the URL. What we're actually caching is the request content as a list of elements of size 1 KB
        proxy_ref = self.parse_referer_info(request)
        headers = { "Referer" : "http://%s/%s" % (proxy_ref[0], proxy_ref[1])} if proxy_ref else {}
        req = requests.get(url, stream=True , params = request.args, headers=headers)
        response = list(req.iter_content(1024))

        # If adding this element puts us over our cache size (Bytes) limit, keep deleting the oldest
        # record until we have space for it
        while self.get_total_size() + sys.getsizeof(response) > self.cache_size_bytes:
            print "Reached cache size limit, deleting oldest record(s)"
            self.delete_oldest()

        # Finally add the response, its headers, and the time we updated the record to the internal cache dictionary.
        self.cache_dict[url] = { "response" : response,
                                 "headers"  : dict(req.headers),
                                 "last_updated" : datetime.now(pytz.timezone("US/Pacific"))
                               }

    # Delete the URL from the internal cache dictionary
    def delete(self, url):
        print "Deleting URL:", url
        del self.cache_dict[url]

    # Fetches the specified URL and streams it out to the client.
    # If the request was referred by the proxy itself (e.g. this is an image fetch for
    # a previously proxied HTML page), then the original Referer is passed.
    def get(self, url):
        url = 'http://' + url
        # LOG.info("Fetching %s", url)
        # Pass original Referer for subsequent resource requests

        # Fetch the URL, and stream it back
        # LOG.info("Fetching with headers: %s, %s", url, headers)
        if url not in self.cache_dict:
            print "URL doesn't exist in cache, inserting: " + url
            self.insert(url)

        elif self.cache_expired(url):
            print "URL exists in cache but is stale, deleting: " + url
            self.delete(url)
            self.insert(url)

        else:
            print "URL exists in cache and is fresh:" + url
        return self.cache_dict[url]['headers'], self.cache_dict[url]['response']


    def parse_referer_info(self, request):
        ref = request.headers.get('referer')
        if ref:
            uri = urlparse(ref).path

            if uri.find("/") < 0:
                return None
            uri_split = uri.split("/", 2)
            if uri_split[1] in "proxyd":
                parts = uri_split[2].split("/", 1)
                r = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")
                return r
        return None
