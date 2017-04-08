from __future__ import absolute_import
from __future__ import unicode_literals

from tachyonic.neutrino.model import Model
from tachyonic.neutrino.model import ModelDict

from tachyonic.neutrino.web.bootstrap3.forms import Form as Bootstrap

class NodesFields(object):                                                                                 
    class Meta(object):
        db_table = 'node'

    id = Model.Uuid(hidden=True)
    domain_id = Model.Uuid(hidden=True)
    name = Model.Text(length=15,
                      max_length=15,
                      label="Name",
                      required=True)
    server = Model.Text(length=15,
                        max_length=15,
                        label="Server",
                        required=True)
    username = Model.Text(length=15,
                          max_length=15,
                          label="Username",
                          required=True)
    password = Model.Text(length=15,
                          max_length=15,
                          label="Password",
                          password=True)
    template = Model.Text(rows=20,
                          hidden=True,
                          label="Template")
    enabled = Model.Bool(label="Enabled")
    creation_time = Model.Datetime(label="Created",
                                       placeholder="0000-00-00 00:00:00",
                                       readonly=True,
                                       length=20)

class Nodes(NodesFields, Model):
    pass


class Node(NodesFields, Bootstrap):
    pass
