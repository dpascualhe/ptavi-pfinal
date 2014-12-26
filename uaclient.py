#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time


class ConfigHandler(ContentHandler):
    """
    Clase para manejar chistes malos
    """

    def __init__ (self):
        """
        Constructor. Inicializamos las variables
        """
        self.username = ""
        self.passwd = ""
        self.server_ip = ""
        self.server_port = 0
        self.rtp_port = 0
        self.regproxy_ip = ""
        self.regproxy_port = 0
        self.log = ""
        self.audio = ""

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta
        """
        if name == 'account':
            # De esta manera tomamos los valores de los atributos
            self.username = attrs.get('username',"")
            print "username:" + self.username
        elif name == 'uaserver':
            self.server_ip = attrs.get('ip',"")
            if self.server_ip == "":
                self.server_ip = "127.0.0.1"
            self.server_port = int(attrs.get('puerto',""))
            print "server:" + self.server_ip + ":", self.server_port
        elif name == 'rtpaudio':
            self.rtp_port = int(attrs.get('puerto',""))
            print "rtp:", self.rtp_port
        elif name == 'regproxy':
            self.regproxy_ip = attrs.get('ip',"")
            if self.regproxy_ip == "":
                self.server_ip = "127.0.0.1"
            self.regproxy_port = int(attrs.get('puerto',""))
            print "server:" + self.regproxy_ip + ":", self.regproxy_port
        elif name == 'log':
            self.log = attrs.get('path',"")
            print "log:" + self.log
        elif name == 'audio':
            self.audio = attrs.get('path',"")
            print "audio:" + self.audio

def raise_error():
    """Procedimiento que eleva la excepcion"""
    print "Usage: python uaclient.py config method option"
    raise SystemExit

def update_log(mess_type, mess_content, ip="", port=""):
    """Procedimiento que actualiza el fichero log"""
    fich.write(time.strftime('%Y%m%d%H%M%S ', time.gmtime(time.time())))
    if mess_type == "error":
        fich.write("Error: " + mess_content)
    elif mess_type == "other":
        fich.write(mess_content)
    elif mess_type == "sent":
        fich.write("Sent to " + ip + ":" + port + " " + mess_content)
    elif mess_type == "rcv":
        fich.write("Received from " + ip + ":" + port + " " + mess_content)        
    fich.write("\r\n")


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
parser.parse(CONFIG_FILE)
print "\033[0m"

if __name__ == "__main__":
    """
    Programa principal
    """
    # Comprobamos si tenemos los argumentos correctos.
    if len(sys.argv) != 4:
        raise_error()

    # Extraemos el método y la opción.
    METHOD = sys.argv[2]
    OPTION = sys.argv[3]

    # Abrimos el fichero log
    fich = open(cHandler.log, 'a')
    update_log("other","Starting...")

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((cHandler.regproxy_ip, cHandler.regproxy_port))

    # Conformamos la petición.
    peticion = METHOD + " sip:" 

    if METHOD == "REGISTER":    
        peticion += cHandler.username + ":" + str(cHandler.server_port)
        peticion += " SIP/2.0\r\n" + "Expires: " + OPTION + "\r\n"
    elif METHOD == "INVITE":
        peticion += OPTION + " SIP/2.0\r\n"
        peticion += "Content-Type: application/sdp\r\n\r\n"
        peticion += "v=0\r\n"
        peticion += "o=" + cHandler.username + " " + cHandler.server_ip + "\r\n"
        peticion += "s=eva01\r\n"
        peticion += "t=0\r\n"
        peticion += "m=audio " + str(cHandler.rtp_port) + " RTP\r\n"
    elif METHOD == "BYE":
        peticion += OPTION + " SIP/2.0\r\n"

    # Enviamos la peticion
    print "\r\nEnviando:\r\n" + "\033[31m\033[01m" + peticion+ "\033[0m"
    my_socket.send(peticion + '\r\n')

    log_pet = " ".join(peticion.split("\r\n"))
    update_log('sent', log_pet, cHandler.regproxy_ip, str(cHandler.regproxy_port))

    try:
        data = my_socket.recv(1024)
    except socket.error:
        error_str = "No server listening at " + cHandler.regproxy_ip + ":"
        error_str += str(cHandler.regproxy_port)
        print "Error: " + error_str
        update_log('error', error_str)
        update_log('other', "Finishing.")
        raise SystemExit

    # Procesamos la respuesta
    log_rcv = " ".join(data.split("\r\n"))
    update_log('rcv', log_rcv, cHandler.regproxy_ip, str(cHandler.regproxy_port))

    line = data.split('\r\n\r\n')[:2]
    ack = 0
    if line == ["SIP/2.0 100 Trying", "SIP/2.0 180 Ring", "SIP/2.0 200 OK"]:
        # Si todo va bien enviamos un ACK
        respuesta = "ACK sip:" + sys.argv[2] + " SIP/2.0\r\n" + '\r\n'
        my_socket.send(respuesta)
        log_pet = " ".join(respuesta.split("\r\n"))
        update_log('sent', log_pet, cHandler.regproxy_ip, str(cHandler.regproxy_port))
        ack = 1
    elif line == ["SIP/2.0 400 Bad Request"]:
        print "El servidor no entiende la petición"
    elif line == ["SIP/2.0 405 Method Not Allowed"]:
        print "El servidor no entiende el método requerido"

    print 'Recibido -- \033[96m\033[01m', data, '\033[0m'
    if ack:
        print 'Enviamos:' + respuesta
    update_log('other', "Finishing.")
    print "Terminando socket..."

    # Cerramos todo
    my_socket.close()
    print "Fin."
