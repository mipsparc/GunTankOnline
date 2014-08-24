from multiprocessing import Process, Queue
from Queue import Empty
import socket
import datetime
import time

PORT = 8800

cli_num = raw_input('CliNum> ')
send_host = raw_input('SendHost> ')

def send(q):
    waitingtime = 0
    last_time = 0
    while True:
        waitingtime += time.time() - last_time
        last_time = time.time()
        if waitingtime >= 1.0:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            nowtime = datetime.datetime.now().isoformat()
            sock.sendto(cli_num+':'+nowtime,(send_host,PORT))
            print 'send',cli_num
            try:
                print q.get(block=False)
            except Empty:
                print 'empty'

            waitingtime = 0

def receive():
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('',PORT))

        data, addr = sock.recvfrom(4096)
        print data,addr

q = Queue()
q.put({'a':'hoge'})

send_process = Process(target=send, args=(q,))
receive_process = Process(target=receive)

send_process.start()
receive_process.start()

