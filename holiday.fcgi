#!/usr/bin/env python2

from flup.server.fcgi import WSGIServer

import holiday

WSGIServer(holiday.app).run()
