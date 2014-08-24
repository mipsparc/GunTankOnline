#coding:utf-8
import socket

while True:
    HOST = '<broadcast>'
    PORT = 8800

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)

    try:
        data = input('> ').encode()
        sock.sendto(data, (HOST, PORT))
    except KeyboardInterrupt:
        sock.close()
