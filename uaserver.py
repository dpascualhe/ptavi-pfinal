#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import SocketServer
import socket
import sys
import os
import uaclient


class ServerHandler(SocketServer.DatagramRequestHandler):
    """
    Server class
    """
    def handle(self):
        mess = self.rfile.read()
        # Envia los códigos de respuesta correspondientes
        while 1:
            print "\r\nEl cliente nos manda:"
            print '\033[96m\033[01m' + mess + '\033[0m'
            word = mess.split(' ')
            if word[0] == 'INVITE':
                sdp = mess.split('\r\n\r\n')[1]
                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ringing\r\n\r\n"
                respuesta += "SIP/2.0 200 OK\r\n"
                respuesta += "Content-Type: application/sdp\r\n\r\n"
                respuesta += sdp
                respuesta += "\r\n\r\n"
            elif word[0] == 'BYE':
                respuesta = "SIP/2.0 200 OK\r\n\r\n"
            elif not word[0] in accepted:
                respuesta = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
            else:
                respuesta = "SIP/2.0 400 Bad Request\r\n\r\n"

            # Imprimimos la respuesta enviada y la enviamos
            if word[0] != 'ACK':
                print 'Enviamos:'
                print '\033[31m\033[01m' + respuesta + '\033[0m'
                my_socket.send(respuesta)

            # Si no hay linea rompemos el bucle
            mess = self.rfile.read()
            if not mess:
                break

        # Si recibimos un ACK procesamos el envío de audio
        if word[0] == 'ACK':
            rtp_send = "./mp32rtp -i 127.0.0.1 -p 23032 < " + sys.argv[3]
            print "Vamos a ejecutar", rtp_send
            os.system(rtp_send)

def raise_error():
    """Procedimiento que eleva la excepcion"""
    print "Usage: python uaserver.py config"
    raise SystemExit


# Comprobamos si los argumentos son válidos
if len(sys.argv) != 2:
    raise_error()
try:
    CONFIG_FILE = open(sys.argv[1])
except IOError:
    raise_error()

print 'Listening...'

# Puerto en el que escuchamos
port = uaclient.cHandler.server_port

# Métodos que entendemos
accepted = ['INVITE', 'ACK', 'BYE']

# Damos permisos de ejecución al programa RTP
os.system("chmod +x mp32rtp")

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((uaclient.cHandler.regproxy_ip, uaclient.cHandler.regproxy_port))

# Creamos servidor y escuchamos
serv = SocketServer.UDPServer(("", port), ServerHandler)
serv.serve_forever()
