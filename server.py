'''
This is a simple Flask app that acts as a caching proxy for GET requests. It accepts incoming GET
requests and forwards them on their destination using a simple caching layer.
'''
from flask import Flask, render_template, request, abort, Response, redirect
import requests
from response_cache import ResponseCache
from urlparse import urlparse


# Define our Flask app
app = Flask(__name__)


# Load in our conf.py file
try:
    from conf import *
    assert CACHE_DURATION_MS   and isinstance(CACHE_DURATION_MS, int)
    assert CACHE_SIZE_BYTES    and isinstance(CACHE_SIZE_BYTES, int)
    assert CACHE_SIZE_ELEMENTS and isinstance(CACHE_SIZE_ELEMENTS, int)
except:
    raise Exception("Import of conf.py was unsuccessful. Make sure you've defined a conf.py containing "
                    "CACHE_DURATION_MS, CACHE_SIZE_BYTES, CACHE_SIZE_ELEMENTS defined as ints")


# Instantiate a ResponseCache with the attributes given by the configuration file
CACHE = ResponseCache(CACHE_DURATION_MS, CACHE_SIZE_BYTES, CACHE_SIZE_ELEMENTS)



CHUNK_SIZE = 1024

def split_url(url):
    """Splits the given URL into a tuple of (protocol, host, uri)"""
    proto, rest = url.split(':', 1)
    rest = rest[2:].split('/', 1)
    host, uri = (rest[0], rest[1]) if len(rest) == 2 else (rest[0], "")
    return (proto, host, uri)

def proxy_ref_info(request):
    """Parses out Referer info indicating the request is from a previously proxied page.
    For example, if:
        Referer: http://localhost:8080/p/google.com/search?q=foo
    then the result is:
        ("google.com", "search?q=foo")
    """
    ref = request.headers.get('referer')
    if ref:
        _, _, uri = split_url(ref)
        if uri.find("/") < 0:
            return None
        first, rest = uri.split("/", 1)
        if first in "pd":
            parts = rest.split("/", 1)
            r = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")
            return r
    return None

def get_source_rsp(url):
    url = 'http://%s' % url
    # Pass original Referer for subsequent resource requests
    proxy_ref = proxy_ref_info(request)
    headers = { "Referer" : "http://%s/%s" % (proxy_ref[0], proxy_ref[1])} if proxy_ref else {}
    # Fetch the URL, and stream it back
    return requests.get(url, stream=True , params = request.args, headers=headers)







@app.route('/cache/<path:url>')
def cached_proxy_handler(url):
    '''
    If someone goes to 'localhost:5000/cache/http://www.google.com' (for example), use
    the cache to deliver the response
    '''
    print "Someone visited localhost:5000/cache/" + url

    r = get_source_rsp(url)
    headers = dict(r.headers)
    def generate():
        for chunk in r.iter_content(CHUNK_SIZE):
            yield chunk
    return Response(generate(), headers = headers)


@app.route('/<path:url>')
def proxy_handler(url):
    '''
    If someone goes to 'localhost:5000/http://www.google.com' (for example), forward them
    to that URL. If they forgot to specify a scheme, add it to the URL before redirecting
    '''
    print "Someone visited localhost:5000/" + url

    r = get_source_rsp(url)
    headers = dict(r.headers)
    def generate():
        for chunk in r.iter_content(CHUNK_SIZE):
            yield chunk
    return Response(generate(), headers = headers)


@app.route('/')
def root_handler():
    '''
    If someone goes to 'localhost:5000/', display a little welcome message for them.
    '''
    print "Someone visited localhost:5000"
    return "Welcome to the Flask Proxy Cache"


# Run the server
if __name__ == '__main__':
    app.run(debug=True, port=5000)