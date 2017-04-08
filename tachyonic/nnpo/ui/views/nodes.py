from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from collections import OrderedDict

from tachyonic import jinja
from tachyonic import app 
from tachyonic import router
from tachyonic.neutrino import constants as const
from tachyonic.neutrino import exceptions
from tachyonic.client import Client

from tachyonic.ui.views import ui
from tachyonic.ui.views.datatable import datatable
from tachyonic.ui import menu
from tachyonic.ui.models.users import User as UserModel
from tachyonic.ui.views.select import select
from tachyonic.ui import menu
from tachyonic.nnpo.models.nodes import Node as NodeModel

log = logging.getLogger(__name__)

menu.admin.add('/Infrastructure/Nokia NPO/Nodes','/nnpo/nodes','nnpo:admin')

log = logging.getLogger(__name__)

@app.resources()
class Nodes(object):
    def __init__(self):
        router.add(const.HTTP_GET,
                   '/nnpo/nodes',
                   self.view,
                   'nnpo:admin')
        router.add(const.HTTP_GET,
                   '/nnpo/nodes/view/{npo_id}',
                   self.view,
                   'nnpo:admin')
        router.add(const.HTTP_GET,
                   '/nnpo/nodes/create',
                   self.create,
                   'nnpo:admin')
        router.add(const.HTTP_POST,
                   '/nnpo/nodes/create',
                   self.create,
                   'nnpo:admin')
        router.add(const.HTTP_GET,
                   '/nnpo/nodes/edit/{npo_id}', self.edit,
                   'nnpo:admin')
        router.add(const.HTTP_POST,
                   '/nnpo/nodes/edit/{npo_id}', self.edit,
                   'nnpo:admin')
        router.add(const.HTTP_GET,
                   '/nnpo/nodes/delete/{npo_id}', self.delete,
                   'nnpo:admin')

    def view(self, req, resp, npo_id=None):
        if npo_id is None:
            fields = OrderedDict()
            fields['name'] = 'Name'
            fields['server'] = 'Server'
            fields['creation_time'] = 'Creation'
            dt = datatable(req, 'nodes', '/v1/nodes',
                           fields, view_button=True, service=False,
                           endpoint='nnpo')
            ui.view(req, resp, content=dt, title='NPO Nodes')
        else:
            api = Client(req.context['restapi'])
            headers, response = api.execute(const.HTTP_GET,
                                            "/v1/node/%s" % (npo_id,),
                                            endpoint='nnpo')
            t = jinja.get_template('tachyonic.nnpo.ui/nodes.html')
            form_extra = t.render(readonly=True)
            form = NodeModel(response, validate=False, readonly=True, cols=2)
            ui.view(req, resp, content=form, id=npo_id, title='View NPO Node',
                    view_form=True, form_extra=form_extra)

    def edit(self, req, resp, npo_id=None):
        if req.method == const.HTTP_POST:
            otype = req.post.getlist('otype')
            eids = req.post.getlist('eids')
            datalist = req.post.getlist('datalist')
            template = ''
            for i, o in enumerate(otype):
                if len(eids) >= i:
                    if len(datalist) >= i:
                        template += o
                        log.error("NO %s" % i)
                        log.error("OTYPE %s" % o)
                        template += "=%s" % eids[i].replace('\r','').replace('\n',',').strip(',')
                        template += "=%s" % datalist[i].replace('\r','').replace('\n',',').strip(',')
                        if len(datalist)-1 != i:
                            template += "\n"
            req.post['template'] = template

            form = NodeModel(req.post, validate=True, readonly=True, cols=2)
            api = Client(req.context['restapi'])
            t = req.post.get('template',None)
            headers, response = api.execute(const.HTTP_PUT, "/v1/node/%s" %
                                            (npo_id,), form, endpoint='nnpo')
        else:
            api = Client(req.context['restapi'])
            headers, response = api.execute(const.HTTP_GET, "/v1/node/%s" %
                                            (npo_id,), endpoint='nnpo')
            t = jinja.get_template('tachyonic.nnpo.ui/nodes.html')
            form_extra = t.render()
            form = NodeModel(response, validate=False, cols=2)
            ui.edit(req, resp, content=form, id=npo_id, title='Edit NPO Node',
                    form_extra=form_extra)

    def create(self, req, resp):
        if req.method == const.HTTP_POST:
            try:
                form = NodeModel(req.post, validate=True, cols=2)
                api = Client(req.context['restapi'])
                headers, response = api.execute(const.HTTP_POST,
                                                "/v1/node",
                                                form,
                                                endpoint='nnpo')
                if 'id' in response:
                    id = response['id']
                    self.view(req, resp, npo_id=id)
            except exceptions.HTTPBadRequest as e:
                form = NodeModel(req.post, validate=False)
                ui.create(req, resp, content=form, title='Create NPO Node',
                          error=[e], endpoint='nnpo')
        else:
            form = NodeModel(req.post, validate=False, cols=2)
            ui.create(req, resp, content=form, title='Create NPO Node')

    def delete(self, req, resp, npo_id=None):
        api = Client(req.context['restapi'])
        headers, response = api.execute(const.HTTP_DELETE, "/v1/node/%s" %
                                        (npo_id,), endpoint='nnpo')
        self.view(req, resp)
