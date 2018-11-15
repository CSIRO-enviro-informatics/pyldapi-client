# -*- coding: latin-1 -*-
#
import sys
ver = sys.version_info
py_ver_major = ver[0]
if py_ver_major < 2:
    sys.exit(0)
__version__ = "0.1.1"
py_ver_minor = ver[1]
if py_ver_major > 3:
    # for python >= 4.0, just assume 3.7
    py_ver_major = 3
    py_ver_minor = 7
if py_ver_major == 2:
    if py_ver_minor < 7:
        raise RuntimeError("Python 2.6 or older is not supported.")
    ver_point = ver[2]
    if ver_point < 9:
        raise RuntimeError("When using Python 2.7, the v2.7.9 release is the minimum requirement.")
    try:
        from requests import Session
    except ImportError:
        raise RuntimeError("When running under Python 2.7, ldapi-client needs to use the 'requests' library.")
    from pyldapi_client.py27 import LDAPIClient
elif py_ver_major == 3:
    if py_ver_minor < 5:
        raise RuntimeError("When using Python 3, the v3.5.x series is the minimum requirement.")
    try:
        from aiohttp import ClientSession
    except ImportError:
        raise RuntimeError("When running under Python 3.5+, ldapi-client needs to use the 'aiohttp' library.")
    try:
        from requests import Session
    except ImportError:
        raise RuntimeError("When running under Python 3.5+, ldapi-client needs to use the 'requests' library.")
    from pyldapi_client.py35 import LDAPIClient
else:
    raise NotImplementedError("Cannot use python version %s.%s" % (str(py_ver_major), str(py_ver_minor)))

__all__ = ['LDAPIClient']
