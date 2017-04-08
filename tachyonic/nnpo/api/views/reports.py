import json
import logging
import datetime
import xml.etree.ElementTree
from collections import OrderedDict

from tachyonic.neutrino.mysql import Mysql
from tachyonic import app 
from tachyonic import router
from tachyonic.neutrino import constants as const
from tachyonic.neutrino import exceptions
from tachyonic.client import RestClient
from tachyonic.client import constants as const
from tachyonic.api.api import orm as api

from tachyonic.nnpo.models import nodes as models
from tachyonic.nnpo.npo import Npo

log = logging.getLogger(__name__)

@app.resources()
class npos(object):
    def __init__(self):
        router.add(const.HTTP_POST,
                   '/v1/report',
                   self.report,
                   'nnpo:customer')

    def report(self, req, resp):
        request = json.loads(req.read())
        if request is not None:
            node = request.get('node')
            date_from = request.get('from_date')
            date_to = request.get('to_date')
            otype = request.get('otype')
            eids = request.get('eids')
            periodicity = request.get('periodicty','h')
            data_list = request.get('datalist')
            if node is not None:
                db = Mysql()
                result = db.execute("SELECT * FROM node WHERE id = %s AND enabled = 1", (node,))
                if len(result) == 0:
                    raise exceptions.HTTPNotFound("NPO Not found",
                                                  "Unknown NPO Server ID")
                else:
                    server = result[0]['server']
                    server = "https://%s:8443" % server
                    username = result[0]['username']
                    password = result[0]['password']
                    npo = Npo(server, username, password)
                    if len(eids) == 1:
                        data = npo.request(date_from,date_to,otype,eids,periodicity,data_list)
                    else:
                        periodicity = 'd'
                        data = npo.request(date_to,date_to,otype,eids,periodicity,data_list)
                    return json.dumps(data, indent=4)
