import json
import logging
import datetime
import xml.etree.ElementTree
from collections import OrderedDict

from tachyonic import app 
from tachyonic import router
from tachyonic.neutrino import constants as const
from tachyonic.client import RestClient
from tachyonic.client import constants as const
from tachyonic.api.api import orm as api

from tachyonic.nnpo.models import nodes as models

log = logging.getLogger(__name__)

@app.resources()
class npos(object):
    def __init__(self):
        router.add(const.HTTP_GET,
                   '/v1/nodes',
                   self.get,
                   'nnpo:admin')
        router.add(const.HTTP_GET,
                  '/v1/node/{npo_id}',
                   self.get,
                   'nnpo:admin')
        router.add(const.HTTP_POST,
                   '/v1/node',
                   self.post,
                   'nnpo:admin')
        router.add(const.HTTP_PUT,
                   '/v1/node/{npo_id}',
                   self.put,
                   'nnpo:admin')
        router.add(const.HTTP_DELETE,
                   '/v1/node/{npo_id}',
                   self.delete,
                   'nnpo:admin')

    def get(self, req, resp, npo_id=None):
        return api.get(models.Nodes, req, resp, npo_id)

    def post(self, req, resp):
        return api.post(models.Node, req)

    def put(self, req, resp, npo_id):
        return api.put(models.Node, req, npo_id)

    def delete(self, req, resp, npo_id):
        return api.delete(models.Node, req, npo_id)
