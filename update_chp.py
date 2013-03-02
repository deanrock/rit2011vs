# -*- coding: utf-8 -*-

from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db, models
from BeautifulSoup import BeautifulSoup
import re
import urllib2
from urllib2 import urlopen, URLError, HTTPError

def get_day(name):
    days = ['ponedeljek', 'torek', 'sreda', 'četrtek', 'petek']

    name = name.replace('<td>','').replace('</td>','').lower()

    i = 1
    for day in days:
        if day == name:
            return i
        i=i+1

    return 0

def update(predmet, url):
    try:
        data=urllib2.urlopen(url).read()
    except:
        return

    soup = BeautifulSoup(data)

    rows = soup('tr')
    
    for row in rows:
        columns = row('td')

        if len(columns) == 7:
            naziv = str(columns[0]).replace('<td>','').replace('</td>','')
            prostor = str(columns[1]).replace('<td>','').replace('</td>','')
            dan = get_day(str(columns[2]))
            termin = str(columns[3]).replace('<td>','').replace('</td>','')
            asistent = str(columns[4]).replace('<td>','').replace('</td>','')
            
            if dan > 0:
                record = models.Vaje.query.filter_by(naziv=naziv).first()

                if record:
                    record.prostor = prostor
                    record.predmet = predmet
                    record.termin = termin
                    record.dan=dan
                    record.asistent=unicode(asistent, 'utf-8')
                    db.session.commit()
                else:
                    record = models.Vaje()
                    record.naziv = naziv
                    record.prostor = prostor
                    record.predmet = predmet
                    record.termin = termin
                    record.dan=dan
                    record.asistent=unicode(asistent, 'utf-8')
                    
                    db.session.add(record)
                    db.session.commit()


#update RAIN
update(u'Razvoj aplikacij za internet', 'http://chp.uni-mb.si/rezervacije/rain/')

#update RO
update(u'Računalniška omrežja', 'http://chp.uni-mb.si/rezervacije/ro/')

print models.Vaje.query.all()
