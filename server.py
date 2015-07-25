#########################################################################################################
# This is a simple Flask app that acts as a caching proxy for GET requests. It accepts incoming GET
# requests and forwards them on their destination using a simple caching layer represented by the
# ResponseCache class.
#########################################################################################################
from flask import Flask, url_for, render_template, request, abort, Response, redirect
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
    assert PORT                and isinstance(PORT, int)
except:
    raise Exception("Import of conf.py was unsuccessful. Make sure you've defined a conf.py containing "
                    "CACHE_DURATION_MS, CACHE_SIZE_BYTES, CACHE_SIZE_ELEMENTS, and PORT defined as ints")


# Instantiate a ResponseCache with the attributes given by the configuration file
CACHE = ResponseCache(CACHE_DURATION_MS, CACHE_SIZE_BYTES, CACHE_SIZE_ELEMENTS)


# Display the rendered proxyinfo page if the user navigates to 'localhost:5000/proxyinfo'
@app.route('/proxyinfo')
def home():
    return render_proxyinfo_page()

# Return the rendered proxyinfo.html page
def render_proxyinfo_page():
    return render_template('proxyinfo.html',
                           port = PORT,
                           cache_duration_ms = CACHE_DURATION_MS,
                           cache_size_bytes = CACHE_SIZE_BYTES,
                           cache_size_elements = CACHE_SIZE_ELEMENTS,
                           response_cache = CACHE,)

#
@app.route('/proxy/<path:url>')
def proxy(url):
    headers, request_content = CACHE.get(url)
    # LOG.info("Got %s response from %s",r.status_code, url)
    def generate():
        for chunk in request_content:
            yield chunk
    return Response(generate(), headers = headers)

#
@app.route('/<path:url>')
def root(url):
    # CACHE.insert(url, str(url) + " RESPONSE")
    # LOG.info("Root route, path: %s", url)
    # If referred from a proxy request, then redirect to a URL with the proxy prefix.
    # This allows server-relative and protocol-relative URLs to work.
    proxy_ref = CACHE.parse_referer_info(request)
    if proxy_ref:
        redirect_url = "/proxy/%s/%s%s" % (proxy_ref[0], url, ("?" + request.query_string if request.query_string else ""))
        # LOG.info("Redirecting referred URL to: %s", redirect_url)
        return redirect(redirect_url)
    # Otherwise, default behavior
    return render_proxyinfo_page()




# # Fetches the specified URL and streams it out to the client.
# # If the request was referred by the proxy itself (e.g. this is an image fetch for
# # a previously proxied HTML page), then the original Referer is passed.
# def get_response(url):
#     url = 'http://%s' % url
#     # LOG.info("Fetching %s", url)
#     # Ensure the URL is approved, else abort
#     # Pass original Referer for subsequent resource requests
#     proxy_ref = parse_referer_info(request)
#     headers = { "Referer" : "http://%s/%s" % (proxy_ref[0], proxy_ref[1])} if proxy_ref else {}
#     # Fetch the URL, and stream it back
#     # LOG.info("Fetching with headers: %s, %s", url, headers)
#     return requests.get(url, stream=True , params = request.args, headers=headers)

# Parses out Referer info indicating the request is from a previously proxied page.
#     For example, if:
#         Referer: http://localhost:8080/p/google.com/search?q=foo
#     then the result is:
#         ("google.com", "search?q=foo")
# def parse_referer_info(request):
#
#     ref = request.headers.get('referer')
#     if ref:
#         uri = urlparse(ref).path
#
#         if uri.find("/") < 0:
#             return None
#         uri_split = uri.split("/", 2)
#         if uri_split[1] in "proxyd":
#             parts = uri_split[2].split("/", 1)
#             r = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")
#             return r
#     return None

# Run the server
app.run(debug=True, port=PORT)

