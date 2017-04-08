from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from collections import OrderedDict
from datetime import datetime
import json

import pandas as pd
#import matplotlib.pyplot as plt
#import matplotlib as mpl
#import matplotlib.dates

from tachyonic import jinja
from tachyonic import app 
from tachyonic import router
from tachyonic.neutrino import constants as const
from tachyonic.neutrino import exceptions
from tachyonic.client import Client
from tachyonic.neutrino.utils.general import timer

from tachyonic.ui.views import ui
from tachyonic.ui.views.datatable import datatable
from tachyonic.ui import menu
from tachyonic.ui.models.users import User as UserModel
from tachyonic.ui.views.select import select

log = logging.getLogger(__name__)


menu.admin.add('/Infrastructure/Nokia NPO/Reports','/nnpo/reports','nnpo:customer')


@app.resources()
class Reports(object):
    def __init__(self):
        router.add(const.HTTP_GET,
                   '/nnpo/reports',
                   self.view,
                   'nnpo:customer')
        router.add(const.HTTP_POST,
                   '/nnpo/reports',
                   self.view,
                   'nnpo:customer')

    def _check_date(self, from_date, to_date):
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
        except:
            raise exceptions.HTTPInvalidParam("From Date Selection")
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d')
        except:
            raise exceptions.HTTPInvalidParam("To Date Selection")
        if from_date > to_date:
            raise exceptions.HTTPInvalidParam("From Date after To Date")


    def view(self, req, resp):
        timed = timer()
        report = req.post.get('report','d')
        from_date = req.post.get('from_date')
        to_date = req.post.get('to_date')
        server = req.post.get('server')

        if from_date is None:
            from_date = str(datetime.now().strftime('%Y-%m-%d'))
        if to_date is None:
            to_date = str(datetime.now().strftime('%Y-%m-%d'))

        self._check_date(from_date, to_date)
        

	api = Client(req.context['restapi'], timeout=120)
	headers, servers = api.execute(const.HTTP_GET,
	                               "/v1/nodes",
				       endpoint='nnpo')

        request_obj = {}
        request_obj['node'] = server
        request_obj['from_date'] = from_date
        request_obj['to_date'] = to_date
        request_obj['periodicty'] = report
        request_obj['datalist'] = [ 'AttachSR_WithoutSystemRela' ]

        sheets = OrderedDict()
        # FORMAT FLOATS for 2 Decimal Values
        pd.options.display.float_format = '{:,.2f}'.format
        if server is not None:
            headers, server = api.execute(const.HTTP_GET,
                                           "/v1/node/%s" % server,
                                           endpoint='nnpo')

            if server['template'] is not None and server['template'] != '':
                all_data = get_data(req.context['restapi'], server, request_obj)

                template = server['template'].split('\n')

                for t in template:
                    t = t.split('=')
                    otype = t[0]
                    data = all_data[otype]
                    eids = t[1]
                    datalist = t[2]
                    sheet = otype
                    if sheet not in sheets:
                       sheets[sheet] = None

                    columns = []
                    #columns.append('DateTime')
                    columns.append('ID')
                    for i in data['indicators']:
                        if "_%s" % i in datalist:
                            columns.append(i)

                    i = 0
                    rows = []
                    indexes = []
                    formatters = {}
                    for e in data['data']:
                        for d in data['data'][e]:
                            row = []
                            indexes.append(d)
                            row.append(e)
                            for v in data['data'][e][d]:
                                if "_%s" % v in datalist:
                                    if ((isinstance(data['data'][e][d][v], unicode) or
                                         isinstance(data['data'][e][d][v], str)) and
                                        '%' in data['data'][e][d][v]):
                                       data['data'][e][d][v] = float(data['data'][e][d][v].replace('%',''))
                                       if v not in formatters:
                                           formatters[v] = '{}%'.format
                                    row.append(data['data'][e][d][v])
                            rows.append(row)
                            # d for Index by Date
                            # e for Index by EID
                            # v for Index by Indicator
                            # i for number
                            #df.loc[i] = row
                            #df.append(row)
                            #df.iat[i] = row
                            #i += 1
                            #df.to_json('/tmp/test.json')
                    #log.error(rows)
                    df = pd.DataFrame(rows, columns=columns, index=indexes)
                    #df = df.append(rows, columns=columns)
                    sheets[sheet] = df.to_html(classes=[ 'table' ],
                                               border=0, formatters=formatters)
                    
                        
        t = jinja.get_template('tachyonic.nnpo.ui/report.html')

        if server is None:
            server = {}

        return t.render(servers=servers,
                        server=server.get('id'),
                        from_date=from_date,
                        to_date=to_date,
                        report=report,
                        sheets=sheets)


def get_data(restapi, server, request_obj):
    api = Client(restapi)
    if server['template'] is not None and server['template'] != '':
        template = server['template'].split('\n')
        otypes = {}

        for t in template:
            o = t.split('=')
            otype = o[0]
            if otype not in otypes:
                otypes[otype] = {}
                otypes[otype]['eids'] = []
                otypes[otype]['datalist'] = []
            for eid in o[1].split(','):
                if eid not in otypes[otype]['eids']:
                    otypes[otype]['eids'].append(eid)
            for dl in o[2].split(','):
                if dl not in otypes[otype]['datalist']:
                    otypes[otype]['datalist'].append(dl)

        data = {}
        for otype in otypes:
            request_obj['otype'] = otype
            request_obj['eids'] = otypes[otype]['eids']
            request_obj['datalist'] = otypes[otype]['datalist']
            headers, d = api.execute(const.HTTP_POST,
                                        "/v1/report",
                                        obj=request_obj,
                                        endpoint='nnpo')
            data[otype] = d
        return data
    else:
        return {}
