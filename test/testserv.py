#coding:utf-8
import socket

HOST = ''
PORT = 8800

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST,PORT))

try:
    while True:
        data, address = sock.recvfrom(4096)
        print(data)

except KeyboardInterrupt:
    sock.close()
