# -*- coding: utf-8 -*-
from requests import session
from BeautifulSoup import BeautifulSoup
import re
import codecs


class PHPBB_Login:
    def __init__(self, url):
        self.url = url

    def check_login(self, username, password):
        u = self.url+'/login.php'

        payload = {
            'username': username,
            'password': password,
            'redirect':'',
            'login':'Prijava'
        }

        with session() as c:
            c.post(u, data=payload)
            request = c.get(self.url+'/forums_m.php?mode=editprofile')
            
            content = request.text.encode('ascii', 'ignore')

            soup = BeautifulSoup(content)

            email = soup('input', {'name':'email'})

            if len(email) == 0:
                return None, None
            else:
                nickname = soup('input', {'name':'username'})

                return nickname[0]['value'], email[0]['value']

        return None, None

if __name__ == '__main__':
    #test
    u = 'http://rit2011vs.mojforum.si'

    login = PHPBB_Login(u)
    print login.check_login('u','p')
