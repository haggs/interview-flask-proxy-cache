# Cached Proxy Server
This is a simple Flask app that acts as a caching proxy for GET requests. It accepts incoming GET
requests and forwards them on their destination using a simple caching layer represented by the
ResponseCache class.

I developed this app for an interview task, and I figured I'd use it as an opportunity to mess
around with Flask and a few Python modules like requests, urlparse, etc. I wrote it in my last days in Ecuador,
so it might be a little sloppy. Give it a try, let me know what you think :)

### Requirements
**Note:** This was developed and tested in an Ubuntu 12.04 virtual machine

* Python (tested with Python 2.7)
* Python Modules
  * flask
  * requests

I recommend you use virtualenv to run the server, so you don't mess with your Python install. To install virtualenv, do:

```
sudo apt-get install python-virtualenv
```

To initialize your virtual environment, cd to the directory that contains this repository and do:

```
virtualenv environment
```

To install the required Python modules in your virtual environment, do:

```
environment/bin/pip install flask
environment/bin/pip install requests
```

### Usage
You can edit the configuration of the cache and the port the server runs on by editing **conf.py**. This file should look like:
```
CACHE_DURATION_MS   = 10 * 1000
CACHE_SIZE_BYTES    = 100000
CACHE_SIZE_ELEMENTS = 8
LOG_TABLE_MAX_SIZE = 100
PORT = 5000
```

If you're using virtualenv as described above, run the server by doing:

```
environment/bin/python server.py
```

Otherwise just do:

```python server.py```

Now that the server is running, I recommend you keep two browser tabs open:
* In the first tab, go to **localhost:PORT/proxyinfo** (port 5000 is default).
This shows general information about the cache. It's not that dynamic, so refresh it after every request.
* In the second tab, go to **localhost:PORT/proxy/www.google.com** (for example) to use the proxy and cache.

Look at the log in the proxyinfo page to see what the cache is doing.

### TODO's
* _The proxyinfo page is just static HTML (err, it uses Flask's dynamic templating, but you still have to refresh the page
for new info). I want to look into Flask's ajax support for making it more dynamic._
* _The cache layer is better developed than the proxy layer. I need to do more testing and improvements there._