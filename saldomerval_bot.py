#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, Job
from datetime import datetime, timedelta
from time import mktime
import sqlite3 as lite
import datetime
import requests
import logging
#import HTMLParser
#from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import uuid
from lxml import html

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
    p_chat_id = update.message.chat.id
    int_cardnumber = get_cardnumber(p_chat_id)
    return_text = '';

    if int_cardnumber > -1:
        # CONSULTAR
        r = requests.post("https://www.metro-valparaiso.cl/saldonuevo.php", data={"numerotarjeta": int_cardnumber})

        tree = html.fromstring(r.content)

        # Saldo, operaciones y mensaje final
        lSaldo = tree.xpath('//h2/strong/text()')
        lOperaciones = tree.xpath('//li//strong/text()')
        lMensaje = tree.xpath('//p/text()')

        # Preparar respuesta
        if len(lSaldo) > 0:
            return_text = "Tu saldo disponible es: " + lSaldo[0]

        #if len(lOperaciones) > 0:

        return_text = return_text + lMensaje[0]

    else:
        # NO HAY NUMERO DE TARJETA
        return_text = 'No hay número de tarjeta configurado. Ingrésalo con /numerotarjeta <numero>'

    bot.sendMessage(chat_id=update.message.chat.id, text=return_text)


def numerotarjeta(bot, update, args):
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

            # Segun resultado obtenido, actualiza o inserta
            if row_count > 0:
                cur.execute("UPDATE saldomerval SET cardnumber=?, username=? WHERE chatid=?", (p_numerotarjeta, p_username, update.message.chat.id))
                conn.commit()
                str_result = 'Se ha actualizado el número de la tarjeta'
            else:
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
