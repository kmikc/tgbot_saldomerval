#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, Job
from datetime import datetime, timedelta
from time import mktime
import sqlite3 as lite
import datetime
import requests
import logging
import HTMLParser
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import uuid

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

#
#
# OBTIENE NUMERO DE TARJETA GUARDADA SEGUN CHAT_ID
#
#

def get_cardnumber(p_chat_id):
    # COUNT
    conn = lite.connect('saldomerval.db')
    query = "SELECT COUNT(*) FROM saldomerval WHERE chatid={CHATID};".format(CHATID=p_chat_id)
    cur = conn.cursor()
    cur.execute(query)
    res_count = cur.fetchone()[0]
    conn.commit()

    if res_count == 0:
        res_cardnumber = -1
    else:
        query = "SELECT cardnumber FROM saldomerval WHERE chatid={CHATID};".format(CHATID=p_chat_id)
        cur = conn.cursor()
        cur.execute(query)
        res_cardnumber = cur.fetchone()[0]
        conn.commit()

    conn.close()

    return res_cardnumber


#
#
# BUSCA NUMERO DE TARJETA Y CONSULTA EL SALDO
#
#

def saldo(bot, update):
    print '---------------'
    print 'saldo'
    print datetime.datetime.now()
    p_chat_id = update.message.chat.id
    print p_chat_id
    int_cardnumber = get_cardnumber(p_chat_id)

    print int_cardnumber

    if int_cardnumber > -1:
        # CONSULTAR

        print 'Consultar...'

        r = requests.post("https://www.metro-valparaiso.cl/saldonuevo.php", data={"numerotarjeta": int_cardnumber})

        #r.text
        responsetext = r.text
        print responsetext
        return_text = responsetext

        #HTMLParser
        html_parser = HTMLParser.HTMLParser()
        responsetext_unescaped = html_parser.unescape(responsetext)
        print responsetext_unescaped
        return_text = responsetext_unescaped

        #BeautifulSoup
        responsetext_unescaped_beautiful = unicode(BeautifulSoup(responsetext_unescaped, convertEntities=BeautifulStoneSoup.ALL_ENTITIES).text)
        print responsetext_unescaped_beautiful
        return_text = responsetext_unescaped_beautiful

    else:
        # NO HAY NUMERO DE TARJETA

        print 'No hay numero'
        return_text = 'No hay número de tarjeta configurado. Ingrésalo con /numerotarjeta <numero>'

    bot.sendMessage(chat_id=update.message.chat.id, text=return_text)


def numerotarjeta(bot, update, args):
    print 'numerotarjeta'
    str_result = 'args: {}'.format(args[0])
    try:
        p_numerotarjeta = int(args[0])
        ok = True
        p_username = str(update.message.chat.username)

    except:
        str_result = "Valor no numérico"
        ok = False

    if ok:
        conn = None
        try:
            conn = lite.connect('saldomerval.db')
            cur = conn.cursor()

            # Cuenta registros existentes
            cur.execute("SELECT COUNT(*) FROM saldomerval WHERE chatid=:CHATID", {"CHATID": update.message.chat.id})
            row_count = cur.fetchone()[0]

            print row_count

            # Segun resultado obtenido, actualiza o inserta
            if row_count > 0:
                print 'UPDATE'
                cur.execute("UPDATE saldomerval SET cardnumber=?, username=? WHERE chatid=?", (p_numerotarjeta, p_username, update.message.chat.id))
                conn.commit()
                str_result = 'Se ha actualizado el número de la tarjeta'
            else:
                print 'INSERT'
                p_uniqid = str(uuid.uuid4())
                cur.execute("INSERT INTO saldomerval (uniqid, chatid, cardnumber, username) VALUES (?, ?, ?, ?)", (p_uniqid, update.message.chat.id, p_numerotarjeta, p_username))
                conn.commit()
                str_result = 'Se ha ingresado tu número de tarjeta'

        except:
            str_result = 'No se pudo conectar'

        finally:
            if conn:
                conn.close()

    bot.sendMessage(chat_id=update.message.chat.id, text=str_result)


#
#
# CONFIGURA EL VALOR DEL GMT, Y LO GUARDA EN DB
#
#

def gmt(bot, update, args):
    str_result = 'args: {}'.format(args[0])
    try:
        var_gmt = int(args[0])
        ok = True

    except:
        str_result = "Valor no numérico"
        ok = False

    if ok:
        conn = None
        try:
            conn = lite.connect('checkpoint_settings.db')
            cur = conn.cursor()

            # Cuenta regstros existentes
            cur.execute("SELECT COUNT(*) FROM chat_settings WHERE chat_id=:CHATID", {"CHATID": update.message.chat.id})
            row_count = cur.fetchone()[0]

            # Segun resultado obtenido, actualiza o inserta
            if row_count > 0:
                cur.execute("UPDATE chat_settings SET gmt_value=? WHERE chat_id=?", (var_gmt, update.message.chat.id))
                conn.commit()
                str_result = 'Registro actualizado'
            else:
                cur.execute("INSERT INTO chat_settings (chat_id, gmt_value) VALUES (?, ?)", (update.message.chat.id, var_gmt))
                conn.commit()
                str_result = 'Registro ingresado'

        except:
            str_result = 'No se pudo conectar'

        finally:
            if conn:
                conn.close()

    update.message.reply_text(str_result)


# TOKEN
token = open('TOKEN').read().rstrip('\n')
updater = Updater(token)

# COMANDOS
#updater.dispatcher.add_handler(CommandHandler('info', info))
#updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('numerotarjeta', numerotarjeta, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('saldo', saldo))

# JOB QUEUE
#jobqueue = updater.job_queue
#checkpoint_queue = Job(notify_checkpoint, 10.0)
#jobqueue.put(checkpoint_queue, next_t=5.0)

updater.start_polling()
updater.idle()
