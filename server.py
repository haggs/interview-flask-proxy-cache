#########################################################################################################
# This is a simple Flask app that acts as a caching proxy for GET requests. It accepts incoming GET
# requests and forwards them on their destination using a simple caching layer represented by the
# ResponseCache class. Port number and cache configuration are set in conf.py.
#
# Usage:    Run this file (python server.py)
#           Navigate to localhost:PORT/proxyinfo to see the status of the cache
#           Navigate to localhost:PORT/proxy/www.google.com (for example) to use the proxy
#
# Requirements:    Python 2.7
#                  Flask
#                  requests
#
# Author:    Dan Haggerty, daniel.r.haggerty@gmail.com
# Date:      July 25th, 2015
#########################################################################################################
from flask import Flask, url_for, render_template, request, abort, Response, redirect
import requests
from response_cache import ResponseCache
from urlparse import urlparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("main.py")


# Define our Flask app
app = Flask(__name__)

# Load in our conf.py file
try:
    from conf import *
    assert CACHE_DURATION_MS   and isinstance(CACHE_DURATION_MS, int)
    assert CACHE_SIZE_BYTES    and isinstance(CACHE_SIZE_BYTES, int)
    assert CACHE_SIZE_ELEMENTS and isinstance(CACHE_SIZE_ELEMENTS, int)
    assert LOG_TABLE_MAX_SIZE  and isinstance(LOG_TABLE_MAX_SIZE, int)
    assert PORT                and isinstance(PORT, int)
except:
    msg = "Import of conf.py was unsuccessful. Make sure you've defined a conf.py containing " \
          "CACHE_DURATION_MS, CACHE_SIZE_BYTES, CACHE_SIZE_ELEMENTS, and PORT defined as ints"
    LOG.info(msg)
    raise Exception(msg)


# Instantiate a ResponseCache with the attributes given by the configuration file
CACHE = ResponseCache(CACHE_DURATION_MS, CACHE_SIZE_BYTES, CACHE_SIZE_ELEMENTS, LOG_TABLE_MAX_SIZE, LOG)


# Display the rendered proxyinfo page if the user navigates to 'localhost:PORT/proxyinfo'
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


# A request was made to /proxy/URL, get the response from the cache
# and return it
@app.route('/proxy/<path:url>')
def proxy(url):
    LOG.info("Received request for /proxy/" + str(url))
    headers, request_content = CACHE.get(url)
    return Response((part for part in request_content), headers = headers)


# A request was made to /URL, if this is coming from a proxy request,
# prefix URL with /proxy/ + the referer URL and redirect
@app.route('/<path:url>')
def root(url):
    LOG.info("Received request for /" + str(url))
    referer_info = CACHE.parse_referer_info(request)
    if referer_info:
        url_redirect = "/proxy/" + referer_info[0] + "/" + url + ("?" + request.query_string if request.query_string else "")
        LOG.info("Redirecting URL to " + url_redirect)
        return redirect(url_redirect)
    return render_proxyinfo_page()


# Run the server
app.run(host='0.0.0.0', port=PORT)

