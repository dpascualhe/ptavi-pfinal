#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco
en UDP simple
"""

import SocketServer
import socket
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


class ServerHandler(SocketServer.DatagramRequestHandler):
    """
    Server class
    """
    def handle(self):
        mess = self.rfile.read()
        line = mess.split("\r\n")
        # Envia los códigos de respuesta correspondientes
        while 1:
            proxy = 0
            print "\r\nEl cliente nos manda:"
            print '\033[96m\033[01m' + mess + '\033[0m'
            word = line[0].split(' ')
            if word[0] == 'REGISTER':
                client_name = word[1].split(":")[1]
                client_ip = self.client_address[0]
                client_port = word[1].split(":")[2]
                # Procesamos la cabecera 'expires'
                word = line[1].split(' ')
                if word[0] == 'Expires:':
                    expires = word[1]
                    clients[client_name] = [client_ip, client_port, time.time(),
                                            expires]
                    if expires == 0:
                        del clients[client_name]
                    self.register2file()
                    # Enviamos OK
                    respuesta = "SIP/2.0 200 OK\r\n\r\n"
                else:
                    respuesta = "SIP/2.0 400 Bad Request\r\n\r\n"    
            else:
                if client_name in clients:
                    proxy = 1
                    respuesta = mess                  
                    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
                    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_socket.connect((clients[client_name][0], 
                                        int(clients[client_name][1])))
                else:
                    respuesta = "SIP/2.0 404 User Not Found\r\n\r\n"
                    
            # Imprimimos la respuesta enviada y la enviamos
            print 'Enviamos a:' + client_name 
            print '\033[31m\033[01m' + respuesta + '\033[0m'
            if proxy:
                my_socket.send(respuesta)
            else:
                self.wfile.write(respuesta)

            # Si no hay linea rompemos el bucle
            line = self.rfile.read()
            if not line:
                break

    # Lleva un registro de los clientes conectados
    def register2file(self):
        """
        Crea el archivo que toma los registros de los usuarios
        """
        # Abrimos el fichero...
        fich = open(cHandler.database, 'w')
        #fich.write('User\tIP\tPort\tDate\tExpires\r\n')

        # Obtenemos el tiempo de expiración
        for client in clients.keys():
            expire = clients[client][3]
            date = clients[client][2]
            
            expire_date = date + int(expire)
            if expire_date > time.time():
                fich.write(client + '\t' + clients[client][0] +
                            '\t' + clients[client][1] + '\t' + 
                            str(clients[client][2]) + '\t' +
                            clients[client][3] + '\r\n')
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

serv = SocketServer.UDPServer(("", cHandler.server_port), ServerHandler)
serv.serve_forever()
