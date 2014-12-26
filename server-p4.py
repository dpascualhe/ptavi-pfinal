#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco
en UDP simple
"""

import SocketServer
import sys
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

class ConfigHandler(ContentHandler):
    """
    Clase para manejar chistes malos
    """

    def __init__ (self):
        """
        Constructor. Inicializamos las variables
        """
        self.server_name = ""
        self.server_ip = ""
        self.server_port = 0
        self.database = ""
        self.log = ""

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta
        """
        if name == 'server':
            self.server_name = attrs.get('name',"")
            self.server_ip = attrs.get('ip',"")
            if self.server_ip == "":
                self.server_ip = "127.0.0.1"
            self.server_port = int(attrs.get('puerto',""))
            print "server:" + self.server_name + " " + self.server_ip + ":",
            print self.server_port
        elif name == 'database':
            self.database = attrs.get('path',"")
            print "database:" + self.database        
        elif name == 'log':
            self.log = attrs.get('path',"")
            print "log:" + self.log


class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    Clase para SIP register
    """

    def handle(self):
        """
        Manejador de los registros SIP
        """
        while 1:
            # Leemos lo que nos envía el cliente y lo separamos en lineas
            peticion_string = self.rfile.read()
            peticion_lines = peticion_string.split("\r\n")
            peticion = peticion_lines[0].split(" ")

            # Procesamos el REGISTER
            if peticion[0] == "REGISTER":
                self.sip_dir = peticion[1].split(":")[1]
                clients[self.sip_dir] = self.client_address[0]
                # Procesamos la cabecera 'expires'
                cabecera = peticion_lines[1]
                self.expire_sec = int(cabecera.split(" ")[1])
                if self.expire_sec == 0:
                    del clients[self.sip_dir]
                # Enviamos OK
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")

            if not peticion_string:
                break
            print "El cliente nos manda " + peticion_string

        # Imprimimos la dirección del cliente
        print "Direccion cliente:", self.client_address, "\r\n\r\n"
        self.register2file()

    # Lleva un registro de los clientes conectados
    def register2file(self):
        """
        Crea el archivo que toma los registros de los usuarios
        """
        # Abrimos el fichero...
        fich = open('registered.txt', 'w')
        fich.write('User\tIP\tExpires\r\n')

        # Obtenemos el tiempo de expiración
        expire = time.strftime('%Y-%m-%d %H:%M:%S',
                                time.gmtime(time.time() + self.expire_sec))
        clients[self.sip_dir] = [self.client_address[0], expire]

        for client in clients.keys():
            if clients[client][1] > time.strftime('%Y-%m-%d %H:%M:%S',
                                                    time.gmtime(time.time())):
                fich.write(client + '\t' + clients[client][0] +
                            '\t' + clients[client][1] + '\r\n')
            else:
                del clients[client]
        fich.close()

def raise_error():
    """Procedimiento que eleva la excepcion"""
    print "Usage: python proxy_registar.py config"
    raise SystemExit


# Argumentos
if len(sys.argv) != 2:
    raise_error()
# Extraemos el fichero de configuración. Si no existe, elevamos la excepción.
try:
    CONFIG_FILE = open(sys.argv[1])
except IOError:
    raise_error()


# Manejamos el fichero de configuración
parser = make_parser()
cHandler = ConfigHandler()
parser.setContentHandler(cHandler)
print "\033[93m"
parser.parse("pr.xml")
print "\033[0m"

# Creamos servidor de eco y escuchamos
print "Server " + cHandler.server_name + " listening at", cHandler.server_port

#Inicializamos los diccionarios de clientes
clients = {}
clients_time = {}

serv = SocketServer.UDPServer(("", cHandler.server_port), SIPRegisterHandler)
serv.serve_forever()
