#coding:utf-8
import socket
import datetime

machine_size = int(raw_input('size> '))
start_num = 1
for machine_num in range(start_num, machine_size + start_num):
    HOST = '192.168.1.'+str(machine_num)
    PORT = 8800

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = datetime.datetime.now().isoformat()
    sock.sendto(data, (HOST, PORT))
    print 'DONE '+HOST
