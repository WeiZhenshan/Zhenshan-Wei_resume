import socket
import threading
import time
import datetime as dt
import sys
from enum import Enum


def StrToCommand(str):
    # eval函数的作用是：把字符串当成表达式解析并求值，帮助在字典和字符串之间来回转换（字典形式的字符串-》字典）
    command = eval(str)
    return command


def CommandToStr(command):
    # 字典-》字符串
    return str(command)


class Client:
    serverIp = ""
    serverPort = 0
    clientSocket = None
    username = ""
    class states(Enum):
        start0=1
        wait0=2
        start1=3
        wait1=4
        exit=5
    #states = Enum("states", ("start0", "wait0", "start1", "wait1", "exit"))
    state = states.start0
    # 指示文件传输在第几步
    currentStage = 1
    # server返回，是0表示正常执行
    returnCode = 0
    needToSendFilename = ""
    needToSendThreadTitle = ""
    exit = False

    def __init__(self, ip, port):
        self.serverIp = ip
        self.serverPort = port
        try:
            self.clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.clientSocket.connect((self.serverIp, self.serverPort))
        except:
            print("服务器连接错误")
            exit()

    def parseCommand(self, input_str):
        # 解析command,自己发挥
        commandList = ["ATE", "CRT", "MSG", "DLT", "EDT", "LST", "RDT", "UPD", "DWN", "XIT", "SHT"]
        split_rst = input_str.split()
        rst = []
        rst.append(split_rst[0])
        if rst[0] not in commandList:
            if self.state == self.states.start0:
                rst[0] = "ATE"
                rst += split_rst
            else:
                raise Exception()
        elif rst[0] in ["MSG", "EDT"]:
            rst.append(split_rst[1])
            if rst[0] == "MSG":
                rst.append(input_str.replace("MSG" + split_rst[1] + " ", ""))
            else:
                rst.append(split_rst[2])
                rst.append(input_str.replace("EDT" + split_rst[1] + " " + split_rst[2] + " ", ""))
        else:
            rst += split_rst[1:]
        return rst

    def recvFromServer(self):
        # 字符串-》字典（使用字典的方法）
        return StrToCommand(self.clientSocket.recv(1024).decode())

    def sendToServer(self, data):
        self.clientSocket.send(CommandToStr(data).encode())

    def recv(self):
        while True:
            try:
                res = self.recvFromServer()
                self.returnCode = res["returncode"]
                # print("Recv from server：",res)
            except ConnectionError as e:
                print("Exception: ", e)
                return
            else:
                if res["id"] == "ATE":
                    if res["stage"] == 1:
                        if res["returncode"] == 2:
                            print("This user alread login.")
                            self.state = self.states.start0
                        else:
                            self.state = self.states.start0
                            self.currentStage = 2
                    elif res["stage"] == 2:
                        # 方便下一条指令进行解析
                        self.currentStage = 1
                        if res["returncode"] == 0:
                            print("Welcome to the forum")
                            self.state = self.states.start1
                        elif res["returncode"] == 1:
                            print("This user already login")
                            self.state = self.states.start0
                        elif res["returncode"] == 2:
                            print("Incorrect password.")
                            self.state = self.states.start0
                elif res["id"] == "CRT":
                    if res["returncode"] == 0:
                        print("Thread" + res["threadtitle"] + " created.")
                    else:
                        print("Thread" + res["threadtitle"] + " exists.")
                    self.state = self.states.start1
                elif res["id"] == "MSG":
                    if res["returncode"] == 0:
                        print("Message posted to " + res["threadtitle"] + " thread.")
                    else:
                        print("Thread" + res["threadtitle"] + " not exists.")
                    self.state = self.states.start1
                elif res["id"] == "DLT":
                    if res["returncode"] == 0:
                        print("Message in " + res["threadtitle"] + " have deleted.")
                    elif res["returncode"] == 1:
                        print("You don't have permission to delete messages.")
                    elif res["returncode"] == 2:
                        print("Message number not exist.")
                    elif res["returncode"] == 3:
                        print("Thread" + res["threadtitle"] + " not exists.")
                    self.state = self.states.start1
                elif res["id"] == "RDT":
                    if res["returncode"] == 0:
                        if res["content"] == "":
                            print("Thread" + res["threadtitle"] + " is empty")
                        else:
                            print(res["content"])
                    else:
                        print("Thread" + res["threadtitle"] + " not exist.")
                    self.state = self.states.start1
                elif res["id"] == "LST":
                    if res["content"] == "":
                        print("No threads to list.")
                    else:
                        print(res["content"])
                    self.state = self.states.start1
                elif res["id"] == "EDT":
                    if res["returncode"] == 0:
                        print("Message in " + res["threadtitle"] + " have modify.")
                    elif res["returncode"] == 1:
                        print("You don't have permission to edit messages.")
                    elif res["returncode"] == 2:
                        print("Message number not exist.")
                    self.state=self.states.start1
                elif res["id"] == "RMV":
                    if res["returncode"] == 0:
                        print("Thread " + res["threadtitle"] + " removed.")
                    elif res["returncode"] == 1:
                        print("Thread " + res["threadtitle"] + " not exist.")
                    elif res["returncode"] == 2:
                        print("The thread was created by another user and cannot be removed.")
                    self.state = self.states.start1
                elif res["id"] == "UPD":
                    if self.currentStage == 1:
                        if res["returncode"] == 0:
                            self.currentStage = 2
                            self.needToSendFilename = res["filename"]
                            self.needToSendThreadTitle = res["threadtitle"]
                        elif res["returncode"] == 1:
                            self.currentStage = 1
                            print("File exist")
                        else:
                            self.currentStage = 1
                            print("Thread not exist.")
                    elif self.currentStage == 2:
                        self.currentStage = 1
                        print(res["filename"] + " uploaded to " + res["threadtitle"] + " thread.")
                    self.state = self.states.start1
                elif res["id"] == "DWN":
                    if res["returncode"] == 0:
                        with open(res["filename"], 'wb') as fp:
                            fp.write(res["filedata"])
                        print("File" + res["filename"] + " download.")
                    elif res["returncode"] == 1:
                        print("File not exist.")
                    elif res["returncode"] == 2:
                        print("Thread" + res["threadtitle"] + " not exist.")
                    self.state = self.states.start1
                elif res["id"] == "XIT":
                    if res["returncode"] == 0:
                        print("User" + res["username"] + " logout.")
                        print("Goodbye")
                        self.exit = True
                        self.state = self.states.exit
                    elif res["returncode"] == 1:
                        print("User " + res["username"] + " repeat logout.")
                        self.state = self.states.start1
                    elif res["returncode"] == 2:
                        print("User " + res["username"] + " not exist.")
                        self.state = self.states.start1
                elif res["id"] == "SHT":
                    if res["returncode"] == 0:
                        print("Goodbye. Server shutdown.")
                        self.exit = True
                        self.state = self.states.exit
                    else:
                        print("Admin password incorrect.")
                        self.state = self.states.start1

    def send(self):
        tips = "Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RMV, UDP, DWN, XIT, SHT"
        tip_tmp = "Command："
        while True:
            try:
                req = dict()
                if self.state == self.states.wait0 or self.state == self.states.wait1:
                    pass
                elif self.state == self.states.start0:
                    req["id"] = "ATE"
                    if self.currentStage == 1:
                        input_str = input("Username: ")
                        req["stage"] = 1
                        req["username"] = input_str
                        self.username = input_str
                    elif self.currentStage == 2:
                        req["username"] = self.username
                        if self.returnCode == 0:
                            input_str = input("Password: ")
                            req["stage"] = 2
                            req["password"] = input_str
                        else:
                            input_str = input("New password: ")
                            req["stage"] = 2
                            req["newpassword"] = input_str
                    self.sendToServer(req)
                    self.state = self.states.wait0

                elif self.state == self.states.start1:
                    req["username"] = self.username
                    command = []
                    if self.currentStage == 1:
                        input_str = input(tip_tmp)
                        command = self.parseCommand(input_str)
                        # command=["MSG","T1","fdsdfs dfsaffd"]
                    else:
                        if self.needToSendFilename != "":
                            command.append("UPD")
                    if command[0] == 'CRT':
                        req["id"] = 'CRT'
                        req["stage"] = 1
                        req["threadtitle"] = command[1]
                    elif command[0] == 'MSG':
                        req["id"] = 'MSG'
                        req["stage"] = 1
                        req["threadtitle"] = command[1]
                        req["message"] = command[2]
                    elif command[0] == 'DLT':
                        req["id"] = "DLT"
                        req["stage"] = 1
                        req["threadtitle"] = command[1]
                        req["messagenumber"] = int(command[2])
                    elif command[0] == 'EDT':
                        req["id"] = "EDT"
                        req["stage"] = 1
                        req["threadtitle"] = command[1]
                        req["messagenumber"] = int(command[2])
                        req["message"] = command[3]
                    elif command[0] == 'RDT':
                        req["id"] = "RDT"
                        req["stage"] = 1
                        req["threadtitle"] = command[1]
                    elif command[0] == 'LST':
                        req["id"] = "LST"
                        req["stage"] = 1
                    elif command[0] == 'RMV':
                        req["id"] = "RMV"
                        req["stage"] = 1
                        req["threadtitle"] = command[1]
                    elif command[0] == 'UPD':
                        req["id"] = "UPD"
                        if self.currentStage == 1:
                            req["stage"] = 1
                            req["threadtitle"] = command[1]
                            req["filename"] = command[2]
                        else:
                            req["stage"] = 2
                            req["threadtitle"] = self.needToSendThreadTitle
                            req["filename"] = self.needToSendFilename
                            with open(self.needToSendFilename, "rb") as fp:
                                req["filedata"] = fp.read()
                            self.needToSendFilename = ""
                            self.needToSendThreadTitle = ""
                    elif command[0] == 'DWN':
                        req["id"] = "DWN"
                        req["stage"] = 1
                        req["threadtitle"] = command[1]
                        req["filename"] = command[2]
                    elif command[0] == 'XIT':
                        req["id"] = "XIT"
                        req["stage"] = 1
                    elif command[0] == 'SHT':
                        req["id"] = "SHT"
                        req["stage"] = 1
                        req["password"] = command[1]
                    self.sendToServer(req)
                    self.state = self.states.wait1
                elif self.state == self.states.exit:
                    return
            except Exception as e:
                print("Incorect command.")
                continue

    def start(self):
        recv_thread = threading.Thread(target=self.recv())
        recv_thread.setDaemon(True)
        recv_thread.start()
        send_thread = threading.Thread(target=self.send())
        send_thread.setDaemon(True)
        send_thread.start()
        while True:
            if self.exit:
                return


if __name__ == "__main__":
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    client = Client(server_ip, server_port)
    client.start()

#python HK201119010/client.py 127.0.0.1 8080