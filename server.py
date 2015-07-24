'''
This is a simple Flask app that acts as a caching proxy for GET requests. It accepts incoming GET
requests and forwards them on their destination using a simple caching layer.
'''
from flask import Flask, render_template, request, abort, Response, redirect, url_for
import requests
from response_cache import ResponseCache
from urlparse import urlparse
# import logging

# Setup logging
# logging.basicConfig(level=logging.INFO)
# LOG = logging.getLogger("main.py")


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


@app.route('/')
def home():
    return render_template('index.html',
                           port = PORT,
                           cache_duration_ms = CACHE_DURATION_MS,
                           cache_size_bytes = CACHE_SIZE_BYTES,
                           cache_size_elements = CACHE_SIZE_ELEMENTS,
                           response_cache = CACHE,)

@app.route('/<path:url>')
def root(url):
    # LOG.info("Root route, path: %s", url)
    # If referred from a proxy request, then redirect to a URL with the proxy prefix.
    # This allows server-relative and protocol-relative URLs to work.
    CACHE.insert(url, str(url) + " RESPONSE")
    proxy_ref = proxy_ref_info(request)
    if proxy_ref:
        redirect_url = "/p/%s/%s%s" % (proxy_ref[0], url, ("?" + request.query_string if request.query_string else ""))
        # LOG.info("Redirecting referred URL to: %s", redirect_url)
        return redirect(redirect_url)
    # Otherwise, default behavior
    return "Welcome to my little cache proxy server"


@app.route('/p/<path:url>')
def proxy(url):
    CACHE.insert(url, str(url) + " RESPONSE")
    """Fetches the specified URL and streams it out to the client.
    If the request was referred by the proxy itself (e.g. this is an image fetch for
    a previously proxied HTML page), then the original Referer is passed."""
    # if not url in CACHE:
    #     return CACHE.insert(url)['response']
    # return CACHE[url]['response']

    r = get_source_rsp(url)
    # LOG.info("Got %s response from %s",r.status_code, url)
    headers = dict(r.headers)
    def generate():
        for chunk in r.iter_content(1024):
            yield chunk
    return Response(generate(), headers = headers)


def get_source_rsp(url):
        url = 'http://%s' % url
        # LOG.info("Fetching %s", url)
        # Pass original Referer for subsequent resource requests
        proxy_ref = proxy_ref_info(request)
        headers = { "Referer" : "http://%s/%s" % (proxy_ref[0], proxy_ref[1])} if proxy_ref else {}
        # Fetch the URL, and stream it back
        # LOG.info("Fetching with headers: %s, %s", url, headers)
        return requests.get(url, stream=True , params = request.args, headers=headers)


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
            # LOG.info("Referred by proxy host, uri: %s, %s", r[0], r[1])
            return r
    return None

# Run the server
if __name__ == '__main__':
    app.run(debug=True, port=PORT)

