import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

def execute(cmd):
    cmd=cmd.strip()
    if not cmd:
        return
    output=subprocess.check_output(shlex.split(cmd),stderr=subprocess.STDOUT)
    return output.decode()

if (__name__ == '__main__'):
    parser=argparse.ArgumentParser(description="Net Tool",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=textwrap.dedent('''Example netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
    netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
    netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat/etc/passwd\" # execute command
    echo "ABC" | ./netcat.py -t -192.168.56.1.108 -p 135 # echo text to server port 135
    netcat.py -t 192.168.1.108 -p 5555 # connect to server'''))

    parser.add_argument("-c","--command",action="store_true",help="command shell")
    parser.add_argument("-e","--execute",help="execute specified command")
    parser.add_argument("-l","--listen",action="store_true",help="listen")
    parser.add_argument("-p","--port",type=int,default=5555,help="specified port")
    parser.add_argument("-t","--target",default='192.168.1.203',help="specified ip")
    parser.add_argument("-u","--upload",help="upload file")
    args=parser.parse_args()
    if args.listen:
        buffer=''
    else:
        buffer = sys.stdin.read()


    class Netcat :
        def __init__(self,args,buffer=None):
            self.args = args
            self.buffer = buffer
            self.socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        def run(self):
            if self.args.listen:
                self.listen()
            else:
                self.send()

        def send(self):
            self.socket.connect((self.args.target,self.args.port))
            if self.buffer:
                self.socket.send(self.buffer)
            
            try:
                while True:
                    recv_len = 1
                    response = ''
                    while recv_len:
                        data=self.socket.recv(4096)
                        recv_len=len(data)
                        response = response + data.decode()
                        print(response)
                        if (response=="Bigyan: #>"):
                            buffer = input ('> ')
                            buffer =  buffer + '\n'
                            self.socket.send(buffer.encode())
                        response = ''    
            except KeyboardInterrupt:
                print("user terminated. ")
                self.socket.close()
                sys.exit


        def listen(self):
            self.socket.bind((self.args.target,self.args.port))
            self.socket.listen()

            while True:
                self.client_socket= self.socket.accept()[0]
                print(self.client_socket)
                client_thread = threading.Thread(target=self.handle)
                client_thread.start()

        def handle(self):
            if self.args.execute:
                output = execute(self.args.execute)
                self.client_socket.send(output.encode())
            elif self.args.upload:
                file_buffer = b''
                with open(self.args.upload,'rb') as f:
                    file_buffer=f.read()
                message = f'Saved file {self.args.upload}' 
                self.client_socket.send(message.encode())
                self.client_socket.send(file_buffer)
            
            elif self.args.command:
                cmd_buffer = b''
                try:
                    while True:
                    
                            self.client_socket.send(b'Bigyan: #>')
                            while '\n' not in cmd_buffer.decode():
                                cmd_buffer = cmd_buffer + self.client_socket.recv(1024)
                            response = execute(cmd_buffer.decode())
                            if response:
                                self.client_socket.send(response.encode())
                            cmd_buffer=b''

                except Exception as e :
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit

    nc = Netcat(args, buffer.encode())
    nc.run()


    