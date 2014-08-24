#coding:utf-8
import socket

while True:
    HOST = raw_input('HOST> ')
    PORT = 8800

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        data = raw_input('> ')
        sock.sendto(data, (HOST, PORT))
    except KeyboardInterrupt:
        sock.close()
