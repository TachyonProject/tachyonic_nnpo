import json
import logging
import datetime
import xml.etree.ElementTree
from collections import OrderedDict
import math

from tachyonic.neutrino import exceptions
from tachyonic.neutrino import constants as const
from tachyonic.client.restclient import RestClient

log = logging.getLogger(__name__)

class Npo(object):
    def __init__(self, server, username, password):
        log.error(password)
        self.server = server
        self.username = username
        self.password = password
        self.api = RestClient(ssl_cipher_list='TLSv1',
                         username=username,
                         password=password)

    def _format_value(self, value):
        value = value.replace(' ','')
        if '%' in value:
            return value
        else:
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = long(value)
                if math.isnan(value):
                    return 0
                else:
                    return value
            except:
                return 0

    def _format_indicator(self, value):
        if value[0] == "_":
            value = value[1:]
        return value

    def _format_date(self, value):
        if " " in value:
            date = datetime.datetime.strptime(value, "%m/%d/%Y %H:%M")
            date = datetime.datetime.strftime(date, "%Y/%m/%d %H:%M")
            return str(date).replace('-','/')
        else:
            date = datetime.datetime.strptime(value, "%m/%d/%Y")
            date = datetime.datetime.strftime(date, "%Y/%m/%d")
            return str(date).split(' ')[0].replace('-','/')

    def _clean_date(self, value):
        value = value.replace(" ", "")
        value = value.replace("-", "/")
        date = datetime.datetime.strptime(value, "%Y/%m/%d")
        return str(date).split(' ')[0].replace('-','/')

    def request(self, date_from, date_to, otype, eids, periodicity, data_list):
        if date_from is None:
            date_from = str(datetime.datetime.now().strftime('%Y-%m-%d'))
        if date_to is None:
            date_to = str(datetime.datetime.now().strftime('%Y-%m-%d'))
        if otype is None:
            raise exceptions.HTTPInvalidParam('otype')
        if periodicity is None:
            raise exceptions.HTTPInvalidParam('periodicity')
        if not isinstance(eids, list):
            raise exceptions.HTTPInvalidParam('eids')
        if not isinstance(data_list, list):
            raise exceptions.HTTPInvalidParam('data_list')

        q_eids = ",".join(eids)

        date_from = "%s 00.00" % date_from
        date_to = "%s 23.00" % date_to
        date_from = date_from.replace('/', '.')
        date_to = date_to.replace('/', '.')
        date_from = date_from.replace('-', '.')
        date_to = date_to.replace('-', '.')

        url = "%s/maat/report?" % self.server
	url += "otype=%s" % otype
        url += "&eids=%s" % q_eids
        url += "&periodicity=%s" % periodicity
        url += "&firstdate=%s" % date_from
        url += "&seconddate=%s" % date_to
        url += "&datalist=%s" % ",".join(data_list)
        url += "&format=xml"
        status, headers, response = self.api.execute(const.HTTP_GET, url)
	if status != 200:
	    if status == 401:
		raise exceptions.HTTPInternalServerError('NPO Auth Failed',
							 'NPO Auth Failed %s' % self.server)
            else:
		raise exceptions.HTTPInternalServerError('NPO Internal Error',
							 'NPO Internal Error %s' % self.server)
		

        report = OrderedDict()
        ns = {'maatQos': 'http://www.alcatel.com/2005/MUSE/maatQos'}
        x = xml.etree.ElementTree.fromstring(response)
        report['indicators'] = []
        report['dates'] = []
        report['data'] = OrderedDict()

        for mt in x.findall('maatQos:mt', ns):
            report['indicators'].append(self._format_indicator(mt.text))

        for mr in x.findall('maatQos:mr', ns):
            oid = mr.find('maatQos:oid', ns).text
            if oid not in report['data']:
                report['data'][oid] = OrderedDict()

            for mv in mr.findall('maatQos:mv', ns):
                date = self._format_date(mv.find('maatQos:date', ns).text)
                if date not in report['dates']:
                    report['dates'].append(date)
                if date not in report['data'][oid]:
                    report['data'][oid][date] = OrderedDict()
                i = 0
                for r in mv.findall('maatQos:r', ns):
                    indicator = report['indicators'][i]
                    if indicator not in report['data'][oid][date]:
                        report['data'][oid][date][indicator] = self._format_value(r.text)
                    i += 1
        return report

    def _last_day_of_month(self, date):
        date = date.split('/')
        month = date[1]
        date = "%s/%s/01" % (date[0],date[1])
        date = datetime.datetime.strptime(date, "%Y/%m/%d")
        td = datetime.timedelta(days=1)
        if month == "12":
            date = datetime.datetime(date.year+1,
                                        date.month,
                                        date.day) - td
        else:
            date = datetime.datetime(date.year,
                                        date.month+1,
                                        date.day) - td
        return str(date).split(' ')[0]

    def hourly(self, date, otype, eids, data_list):
        date = self._clean_date(date)
        date_from = date
        date_to = date
        periodicity = 'h'
        return self._request(date_from, date_to, otype, eids, periodicity, data_list)

    def daily(self, date_from, date_to, otype, eids, data_list):
        date_from = self._clean_date(date_from)
        date_to = self._clean_date(date_to)
        periodicity = 'd'
        return self._request(date_from, date_to, otype, eids, periodicity, data_list)

    def week(self, date, otype, eids, data_list):
        date = self._clean_date(date)
        date_from = date
        date_to = datetime.datetime.strptime(date, "%Y/%m/%d")
        date_to = str(date_to + datetime.timedelta(days=6)).split(' ')[0]
        periodicity = 'd'
        return self._request(date_from, date_to, otype, eids, periodicity, data_list)

    def weekly(self, date_from, date_to, otype, eids, data_list):
        date_from = self._clean_date(date_from)
        date_to = self._clean_date(date_to)
        periodicity = 'w'
        return self._request(date_from, date_to, otype, eids, periodicity, data_list)

    def month(self, date, otype, eids, data_list):
        date = self._clean_date(date)
        date = date.split('/')
        date = "%s/%s/01" % (date[0],date[1])
        date_to = self._last_day_of_month(date)
        date_from = date
        periodicity = 'd'
        return self._request(date_from, date_to, otype, eids, periodicity, data_list)

    def monthly(self, date_from, date_to, otype, eids, data_list):
        date_from = self._clean_date(date_from)
        date_to = self._clean_date(date_to)
        date_from = date_from.split('/')
        date_from = "%s/%s/01" % (date_from[0],date_from[1])
        date_to = date_to.split('/')
        date_to = "%s/%s/01" % (date_to[0],date_to[1])
        date_to = self._last_day_of_month(date_to)
        periodicity = 'm'
        return self._request(date_from, date_to, otype, eids, periodicity, data_list)

    def year(self, date, otype, eids, data_list):
        date = self._clean_date(date)
        date_from = date.split('/')
        date_from = "%s/01/01" % date_from[0]
        date_to = date.split('/')
        date_to = "%s/12/01" % date_to[0]
        date_to = self._last_day_of_month(date_to)
        periodicity = 'm'
        return self._request(date_from, date_to, otype, eids, periodicity, data_list)

"""
blah = NPO('https://10.28.94.42:8443',
           'hgerber',
           'Smile@12')

datalist = ('_AttachSR_WithoutSystemRela',
            '_Paging_SuccRate_withoutUELocated',
            '_ERABReq',
            '_RRCSR',
            '_ERABSR',
            '_ERABSucc',
            '_RRCConeqFailures',
            '_RRCConeqReqNoRep',
            '_RRCConeqSucc',
            '_DLTrafficKbyte',
            '_ULTrafficKbyte',
            '_IntereNBHOReq',
            '_Availability',
            '_IntereNBHOSR',
            '_IntereNBHOSucc',
            '_IntraeNBHOReq',
            '_IntraeNBHOReq',
            '_IntraeNBHOSR',
            '_ERABDrops',
            '_ERABCDR',
            '_DLThroughputMbpsBH')

eids = [
    'AAR_OFFICE_1',
    'AAR_OFFICE_2',
    'AAR_OFFICE_3',
    'Acacia_Mall_1',
    'Acacia_Mall_2',
    'Acacia_Mall_3',
    'BUGOLOBI_UBC_1',
    'BUGOLOBI_UBC_2',
    'BUGOLOBI_UBC_3',
    'BUKASA_1',
    'BUKASA_2',
    'BUKASA_3',
    'BUKESA_1',
    'BUKESA_2',
    'BUKESA_3',
    'BUNGA_HILL_1',
    'BUNGA_HILL_2',
    'BUNGA_HILL_3',
    'BWEYOGERERE_1',
    'BWEYOGERERE_2',
    'BWEYOGERERE_3',
    'Bugolobi_e0',
    'Bugolobi_e1',
    'Bugolobi_e2',
    'Bukoto_Kalonda_1',
    'Bukoto_Kalonda_2',
    'Bukoto_Kalonda_3',
    'Bukoto_e0',
    'Bukoto_e1',
    'Bukoto_e2',
    'Bwebajja_1',
    'Bwebajja_2',
    'Bwebajja_3',
    'CELLLTE_Twed_Plaza_1',
    'CELLLTE_Twed_Plaza_2',
    'CELLLTE_Twed_Plaza_3',
    'CITY_SQUARE_1',
    'CITY_SQUARE_2',
    'CITY_SQUARE_3',
    'CITY_SQUARE_F1',
    'CITY_SQUARE_F2',
    'CITY_SQUARE_F3',
    'CRESTED_TOWERS_1',
    'CRESTED_TOWERS_2',
    'CRESTED_TOWERS_3',
    'CRESTED_TOWERS_F1',
    'CRESTED_TOWERS_F2',
    'CRESTED_TOWERS_F3',
    'DUNDU_1',
    'DUNDU_2',
    'DUNDU_3',
    'ELITE_BUILDING_1',
    'ELITE_BUILDING_2',
    'ELITE_BUILDING_3',
    'ENTEBBE_1',
    'ENTEBBE_2',
    'ENTEBBE_3',
    'Elite_Apartment_1',
    'Elite_Apartment_2',
    'Elite_Apartment_3',
    'Entebbe_Bugonga_1',
    'Entebbe_Bugonga_2',
    'Entebbe_Bugonga_3',
    'FOURTH_STREET_LUGOGO_1',
    'FOURTH_STREET_LUGOGO_2',
    'FOURTH_STREET_LUGOGO_3',
    'Fort_Portal_Boma_1',
    'Fort_Portal_Boma_2',
    'Fort_Portal_Boma_3',
    'Fort_Portal_Town_1',
    'Fort_Portal_Town_2',
    'Fort_Portal_Town_3',
    'GAYAZA_1',
    'GAYAZA_2',
    'GAYAZA_3',
    'Gulu_Town_1',
    'Gulu_Town_2',
    'Gulu_Town_3',
    'Gulu_University_1',
    'Gulu_University_2',
    'Gulu_University_3',
    'Gweri_1',
    'Gweri_2',
    'Gweri_3',
    'Jinja_Catholic_1',
    'Jinja_Catholic_2',
    'Jinja_Catholic_3',
    'Jinja_St_James_1',
    'Jinja_St_James_2',
    'Jinja_St_James_3',
    'KABOWA_1',
    'KABOWA_2',
    'KABOWA_3',
    'KALINABIRI_1',
    'KALINABIRI_2',
    'KALINABIRI_3',
    'KANYANYA_1',
    'KANYANYA_2',
    'KANYANYA_3',
    'KASANGATI_1',
    'KASANGATI_2',
    'KASANGATI_3',
    'KATABI_1',
    'KATABI_2',
    'KATABI_3',
    'KAWUGA_1',
    'KAWUGA_2',
    'KAWUGA_3',
    'KIBUYE_1',
    'KIBUYE_2',
    'KIBUYE_3',
    'KIBUYE_PRIMARY_SCHOOL_1',
    'KIBUYE_PRIMARY_SCHOOL_2',
    'KIBUYE_PRIMARY_SCHOOL_3',
    'KIIRA_ROAD_1',
    'KIIRA_ROAD_2',
    'KIIRA_ROAD_3',
    'KIREKA_KAMULI_1',
    'KIREKA_KAMULI_2',
    'KIREKA_KAMULI_3',
    'KIRINYA_1',
    'KIRINYA_2',
    'KIRINYA_3',
    'KISAASI_1',
    'KISAASI_2',
    'KISAASI_3',
    'KISENYI_1',
    'KISENYI_2',
    'KISENYI_3',
    'KISUGU_1',
    'KISUGU_2',
    'KISUGU_3',
    'KITANTE_1',
    'KITANTE_2',
    'KITANTE_3',
    'KITANTE_F1',
    'KITANTE_F2',
    'KITANTE_F3',
    'KITARA_1',
    'KITARA_2',
    'KITARA_3',
    'KIWATULE_1',
    'KIWATULE_2',
    'KIWATULE_3',
    'KOLOLO_1',
    'KOLOLO_2',
    'KOLOLO_3',
    'KOLOLO_HILL_1',
    'KOLOLO_HILL_2',
    'KOLOLO_HILL_3',
    'KOLOLO_HILL_F1',
    'KOLOLO_HILL_F2',
    'KOLOLO_HILL_F3',
    'KONGE_HILL_1',
    'KONGE_HILL_2',
    'KONGE_HILL_3',
    'KYALIWAJALA_1',
    'KYALIWAJALA_2',
    'KYALIWAJALA_3',
    'KYAMBOGO_1',
    'KYAMBOGO_2',
    'KYAMBOGO_3',
    'KYANJA_1',
    'KYANJA_2',
    'KYANJA_3',
    'KYEBANDO_1',
    'KYEBANDO_2',
    'KYEBANDO_3',
    'Kabale_Rugarama_1',
    'Kabale_Rugarama_2',
    'Kabale_Rugarama_3',
    'Kabale_Town_1',
    'Kabale_Town_2',
    'Kabale_Town_3',
    'Kampala_Park_1',
    'Kampala_Park_2',
    'Kampala_Park_3',
    'Kampala_park_F1',
    'Kampala_park_F2',
    'Kampala_park_F3',
    'Kamukuzi_1',
    'Kamukuzi_2',
    'Kamukuzi_3',
    'Kashari_1',
    'Kashari_2',
    'Kashari_3',
    'Kibuli_e0',
    'Kibuli_e1',
    'Kibuli_e2',
    'Kigo_1',
    'Kigo_2',
    'Kigo_3',
    'Kigungu_1',
    'Kigungu_2',
    'Kigungu_3',
    'Kira_1',
    'Kira_2',
    'Kira_3',
    'Kira_SS_1',
    'Kira_SS_2',
    'Kira_SS_3',
    'Kitintale_Biraro_Estate_1',
    'Kitintale_Biraro_Estate_2',
    'Kitintale_Biraro_Estate_3',
    'Kitovu_1',
    'Kitovu_2',
    'Kitovu_3',
    'Kyengera_1',
    'Kyengera_2',
    'Kyengera_3',
    'LOWER_KOLOLO_1',
    'LOWER_KOLOLO_2',
    'LUBAGA_1',
    'LUBAGA_2',
    'LUBAGA_3',
    'LUBYA_1',
    'LUBYA_2',
    'LUBYA_3',
    'LUZIRA_1',
    'LUZIRA_2',
    'LUZIRA_3',
    'Lacor_Hospital_1',
    'Lacor_Hospital_2',
    'Lacor_Hospital_3',
    'Lira_Bur_1',
    'Lira_Bur_2',
    'Lira_Bur_3',
    'Lira_Town_1',
    'Lira_Town_2',
    'Lira_Town_3',
    'Lower_Muyenga_1',
    'Lower_Muyenga_2',
    'Lower_Muyenga_3',
    'Lumumba_Avenue_1',
    'Lumumba_Avenue_2',
    'Lumumba_Avenue_3',
    'Lumumba_Avenue_F1',
    'Lumumba_Avenue_F2',
    'Lumumba_Avenue_F3',
    'Luwum_1',
    'Luwum_2',
    'Luwum_3',
    'Luwum_F1',
    'Luwum_F2',
    'Luwum_F3',
    'MAKERERE_1',
    'MAKERERE_2',
    'MAKERERE_3',
    'MAKERERE_UNIVERSITY_C2_1',
    'MAKERERE_UNIVERSITY_C2_2',
    'MAKERERE_UNIVERSITY_C2_3',
    'MAKINDYE_KIZUNGU_1',
    'MAKINDYE_KIZUNGU_2',
    'MAKINDYE_KIZUNGU_3',
    'MBOGO_1',
    'MBOGO_2',
    'MBOGO_3',
    'MBUYA_1',
    'MBUYA_2',
    'MBUYA_3',
    'MUKONO_HILL_1',
    'MUKONO_HILL_2',
    'MUKONO_HILL_3',
    'MUTUNDWE_1',
    'MUTUNDWE_2',
    'MUTUNDWE_3',
    'MUTUNGO_HILL_1',
    'MUTUNGO_HILL_2',
    'MUTUNGO_HILL_3',
    'MUYENGA_1',
    'MUYENGA_2',
    'MUYENGA_3',
    'MUYENGA_F1',
    'MUYENGA_F2',
    'MUYENGA_F3',
    'Makenzie_Vale_1',
    'Makenzie_Vale_2',
    'Makenzie_Vale_3',
    'Makenzie_Valz_F1',
    'Makenzie_Valz_F2',
    'Makenzie_Valz_F3',
    'Makerere_LDC_1',
    'Makerere_LDC_2',
    'Makerere_LDC_3',
    'Masaka_Sports_1',
    'Masaka_Sports_2',
    'Masaka_Sports_3',
    'Masindi_Town_1',
    'Masindi_Town_2',
    'Masindi_Town_3',
    'Mbale_Resort_1',
    'Mbale_Resort_2',
    'Mbale_Resort_3',
    'Mbale_SS_1',
    'Mbale_SS_2',
    'Mbale_SS_3',
    'Mbarara_Golf_1',
    'Mbarara_Golf_2',
    'Mbarara_Golf_3',
    'NAGURU_1',
    'NAGURU_2',
    'NAGURU_3',
    'NAGURU_VALLEY_1',
    'NAGURU_VALLEY_2',
    'NAGURU_VALLEY_3',
    'NAJEERA_1',
    'NAJEERA_2',
    'NAJEERA_3',
    'NAKASERO_1',
    'NAKASERO_2',
    'NAKASERO_3',
    'NAKASERO_HILL_1',
    'NAKASERO_HILL_2',
    'NAKASERO_HILL_3',
    'NAKASERO_PRIMARY_SCHOOL_1',
    'NAKASERO_PRIMARY_SCHOOL_2',
    'NAKASERO_PRIMARY_SCHOOL_3',
    'NAMASUBA_1',
    'NAMASUBA_2',
    'NAMASUBA_3',
    'NDEJJE_LUBUGUMU_1',
    'NDEJJE_LUBUGUMU_2',
    'NDEJJE_LUBUGUMU_3',
    'NSAMBYA_1',
    'NSAMBYA_2',
    'NSAMBYA_3',
    'NSAMIZI_ENTEBBE_1',
    'NSAMIZI_ENTEBBE_2',
    'NSAMIZI_ENTEBBE_3',
    'Nakawa_1',
    'Nakawa_2',
    'Nakawa_3',
    'Namirembe_1',
    'Namirembe_2',
    'Namirembe_3',
    'Namugongo_1',
    'Namugongo_2',
    'Namugongo_3',
    'Namuwongo_1',
    'Namuwongo_2',
    'Namuwongo_3',
    'Nana_Centre_1',
    'Nana_Centre_2',
    'Nana_Centre_3',
    'Nansana_1',
    'Nansana_2',
    'Nansana_3',
    'Nile_Source_1',
    'Nile_Source_2',
    'Nile_Source_3',
    'Njeru_1',
    'Njeru_2',
    'Njeru_3',
    'Ntinda_PS_1',
    'Ntinda_PS_2',
    'Ntinda_PS_3',
    'OLD_KAMPALA_1',
    'OLD_KAMPALA_2',
    'OLD_KAMPALA_3',
    'OLD_KAMPALA_F1',
    'OLD_KAMPALA_F2',
    'OLD_KAMPALA_F3',
    'SALAAMA_1',
    'SALAAMA_2',
    'SALAAMA_3',
    'SEETA_1',
    'SEETA_2',
    'SEETA_3',
    'SEGUKU_1',
    'SEGUKU_2',
    'SEGUKU_3',
    'Smile_Office_1',
    'Sonde_1',
    'Sonde_2',
    'Sonde_3',
    'Soroti_Station_1',
    'Soroti_Station_2',
    'Soroti_Station_3',
    'Tororo_HC_1',
    'Tororo_HC_2',
    'Tororo_HC_3',
    'Tororo_Sen_Quarters_1',
    'Tororo_Sen_Quarters_2',
    'Tororo_Sen_Quarters_3',
    'Twed_Towers_1',
    'Twed_Towers_2',
    'Twed_Towers_3',
    'Wakiso_1',
    'Wakiso_2',
    'Wakiso_3'
]

#report = blah.month('2017/03/27','EUTRAN', 1, datalist)
#report = blah.daily('2017/02/20','2017/02/21','CELLLTE', eids, datalist)
#report = blah.daily('2017/03/20','2017/03/21','CELLLTE', eids, datalist)
#print json.dumps(report, indent=4)
"""


