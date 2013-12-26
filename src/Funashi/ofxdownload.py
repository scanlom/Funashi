'''
Created on Jul 27, 2013

Downloads account information using ofxclient

@author: scanlom
'''

import smtplib, psycopg2, psycopg2.extras, ConfigParser, os       
from email.mime.text import MIMEText
from ofxclient.config import OfxConfig
from ofxparse import OfxParser
from log import log

def send_mail_html(subject, body):
    config = ConfigParser.SafeConfigParser()
    config.read(os.path.expanduser('~/.Kumamon'))
    server = config.get('Email','Server')
    port = config.getint('Email','Port')
    user = config.get('Email','User')
    password = config.get('Email','Password')
    
    msg = MIMEText(body, 'html')

    msg['Subject'] = subject
    msg['From'] = user
    msg['To'] = user

    # Send the message via our own SMTP server.
    s = smtplib.SMTP(server, port)
    s.ehlo()
    s.starttls()
    s.ehlo
    s.login(user, password)
    s.sendmail(user, [user], msg.as_string())
    s.quit()

def main():
    log.info("Started...")
    
    config = ConfigParser.SafeConfigParser()
    config.read(os.path.expanduser('~/.Kumamon'))
    connect = config.get('Database','Connect')
        
    conn = psycopg2.connect( connect )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "select * from accounts_types where download=true";
    cur.execute(sql)
    banks = cur.fetchall()   
    for bank in banks:
        log.info("Downloading: " + " " + bank['description'])
        GlobalConfig = OfxConfig()
        a = GlobalConfig.account(bank['id'])
        ofxdata = a.download(days=0)
        f = open(os.path.expanduser('~/tmp/ofxdata.tmp'), 'w')
        f.write(ofxdata.read())
        f.close()
        f = open(os.path.expanduser('~/tmp/ofxdata.tmp'), 'r')
        parsed = OfxParser.parse(f)
        f.close()
        log.info("OfxParser complete")
        positions = {}
        for pos in parsed.account.statement.positions:
            positions[pos.security] = round(pos.units * pos.unit_price, 2)
            log.info("Downloaded: " + str(bank['description']) + " " + str(pos.security))
        
        sql = "select * from accounts where type=" + str(bank['type']);
        cur.execute(sql)
        accounts = cur.fetchall()
        for account in accounts:
            if account['name'] not in positions:
                raise Exception('account ' + account['name'] + ' not present in download')
            log.info( bank['description'] + '\t' + account['name_local'] + '\t' + str(positions[account['name']]) ) 
            sql = "update portfolio set value=" + str(positions[account['name']]) + "where symbol='" + account['name_local'] + "'"
            cur.execute(sql)
            conn.commit()
            log.info("Set: " + str(account['name_local']))
    
    # Close the db
    cur.close()
    conn.close()
    log.info("Completed")
            
if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        log.exception(err)
        log.error("Aborted")
        send_mail_html("FAILURE:  Ofxdownload.py", str( err ) )        
