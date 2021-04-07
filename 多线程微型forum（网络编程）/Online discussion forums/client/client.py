import socket
import threading
import time
import datetime as dt
import sys
from enum import Enum


def StrToCommand(str):
    # eval函数的作用是：把字符串当成表达式解析并求值
    return eval(str)


def CommandToStr(command):
    return str(command)


class states(Enum):
    Login = 1
    Login_wait = 2
    Command_interact = 3
    response_wait = 4
    exit = 5


class Client:
    serverIp = ""
    serverPort = 0
    clientSocket = None
    username = ""

    state = states.Login

    currentStage = 1

    returnCode = 0
    SendFilename = ""
    needToSendThreadTitle = ""
    exit = False

    def __init__(self, ip, port):
        self.serverIp = ip
        self.serverPort = port
        try:
            self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientSocket.connect((self.serverIp, self.serverPort))
        except:
            print("服务器连接错误")
            exit()

    # DONE
    def translate_command(self, input_str):
        commandList = ["CRT", "MSG", "DLT", "EDT", "LST", "RDT", "UPD", "DWN", "RMV", "XIT", "SHT"]
        split_input = input_str.split()
        command_formal = []
        command_formal.append(split_input[0])
        if command_formal[0] not in commandList:
            raise Exception()
        elif command_formal[0] in ["MSG", "EDT"]:
            command_formal.append(split_input[1])
            if command_formal[0] == "MSG":
                split_input.pop(0)
                split_input.pop(0)
                str_tmp = ""
                for i in split_input:
                    str_tmp += i
                    str_tmp += " "
                command_formal.append(str_tmp)
            else:
                command_formal.append(split_input[2])
                split_input.pop(0)
                split_input.pop(0)
                split_input.pop(0)
                str_tmp = ""
                for i in split_input:
                    str_tmp += i
                    str_tmp += " "
                command_formal.append(str_tmp)
        else:
            command_formal += split_input[1:]
        return command_formal

    # DONE
    def recvFromServer(self):

        return StrToCommand(self.clientSocket.recv(9999).decode())

    # Done
    def sendToServer(self, data):
        self.clientSocket.send(CommandToStr(data).encode())

    def recv(self):
        while True:
            try:
                res = self.recvFromServer()
                self.returnCode = res["returncode"]
            except ConnectionError:
                print("Exception: ", ConnectionError)
                return
            else:
                if res["id"] == "ATE":
                    if res["stage"] == 1:
                        if res["returncode"] == 2:
                            print("This user already login.")
                            self.state = states.Login
                        else:
                            self.state = states.Login
                            self.currentStage = 2
                    elif res["stage"] == 2:
                        # 方便下一条指令进行解析
                        self.currentStage = 1
                        if res["returncode"] == 0:
                            print("Welcome to the forum")
                            self.state = states.Command_interact
                        elif res["returncode"] == 1:
                            print("This user already login")
                            self.state = states.Login
                        elif res["returncode"] == 2:
                            print("Invalid password.")
                            self.state = states.Login
                elif res["id"] == "CRT":
                    if res["returncode"] == 0:
                        print("Thread " + res["threadtitle"] + " created.")
                    else:
                        print("Thread " + res["threadtitle"] + " exists.")
                    self.state = states.Command_interact
                elif res["id"] == "MSG":
                    if res["returncode"] == 0:
                        print("Message posted to " + res["threadtitle"] + " thread.")
                    else:
                        print("Thread " + res["threadtitle"] + " not exists.")
                    self.state = states.Command_interact
                elif res["id"] == "DLT":
                    if res["returncode"] == 0:
                        print("Message in " + res["threadtitle"] + " have deleted.")
                    elif res["returncode"] == 1:
                        print("You don't have permission to delete messages.")
                    elif res["returncode"] == 2:
                        print("Message number not exist.")
                    elif res["returncode"] == 3:
                        print("Thread " + res["threadtitle"] + " not exists.")
                    self.state = states.Command_interact
                elif res["id"] == "RDT":
                    if res["returncode"] == 0:
                        if res["content"] == "":
                            print("Thread " + res["threadtitle"] + " is empty")
                        else:
                            print(res["content"])
                    else:
                        print("Thread " + res["threadtitle"] + " not exist.")
                    self.state = states.Command_interact
                elif res["id"] == "LST":
                    if res["content"] == "":
                        print("No threads to list.")
                    else:
                        print(res["content"])
                    self.state = states.Command_interact
                elif res["id"] == "EDT":
                    if res["returncode"] == 0:
                        print("Message in " + res["threadtitle"] + " have modify.")
                    elif res["returncode"] == 1:
                        print("You don't have permission to edit messages.")
                    elif res["returncode"] == 2:
                        print("Message number not exist.")
                    self.state = states.Command_interact
                elif res["id"] == "RMV":
                    if res["returncode"] == 0:
                        print("Thread " + res["threadtitle"] + " removed.")
                    elif res["returncode"] == 1:
                        print("Thread " + res["threadtitle"] + " not exist.")
                    elif res["returncode"] == 2:
                        print("The thread was created by another user and cannot be removed.")
                    self.state = states.Command_interact
                elif res["id"] == "UPD":
                    if self.currentStage == 1:
                        if res["returncode"] == 0:
                            self.currentStage = 2
                            self.SendFilename = res["filename"]
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
                    self.state = states.Command_interact
                elif res["id"] == "DWN":
                    if res["returncode"] == 0:
                        with open(res["filename"], 'wb') as fp:
                            fp.write(res["filedata"])
                        print("File " + res["filename"] + " download.")
                    elif res["returncode"] == 1:
                        print("File not exist.")
                    elif res["returncode"] == 2:
                        print("Thread " + res["threadtitle"] + " not exist.")
                    self.state = states.Command_interact
                elif res["id"] == "XIT":
                    if res["returncode"] == 0:
                        print("User" + res["username"] + " logout.")
                        print("Goodbye")
                        self.exit = True
                        self.state = self.states.exit
                    elif res["returncode"] == 1:
                        print("User " + res["username"] + " repeat logout.")
                        self.state = self.states.Command_interact
                    elif res["returncode"] == 2:
                        print("User " + res["username"] + " not exist.")
                        self.state = self.states.Command_interact
                    elif res["id"] == "SHT":
                        if res["returncode"] == 0:
                            print("Goodbye. Server shutdown.")
                            self.exit = True
                            self.state = self.states.exit
                        else:
                            print("Admin password incorrect.")
                            self.state = self.states.Command_interact

    # Done
    def send(self):
        instruction = "Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT, SHT:"
        tip_tmp = "Command："
        while True:
            try:
                req = dict()
                if self.state == states.Login_wait or self.state == states.response_wait:
                    pass
                # In login state , input login command ( contain auto input (ATE))
                elif self.state == states.Login:
                    req["id"] = "ATE"
                    if self.currentStage == 1:
                        input_str = input("Enter username: ")
                        req["stage"] = 1
                        req["username"] = input_str
                        self.username = input_str
                    elif self.currentStage == 2:
                        req["username"] = self.username
                        if self.returnCode == 0:
                            input_str = input("Enter password: ")
                            req["stage"] = 2
                            req["password"] = input_str
                        else:
                            input_str = input("Enter new password for " + self.username + ":")
                            req["stage"] = 2
                            req["newpassword"] = input_str
                    self.sendToServer(req)
                    self.state = states.Login_wait
                # In command_interact stage , input and edit TCP MESSAGE(contain auto input (UPD))
                elif self.state == states.Command_interact:
                    command = []
                    req["username"] = self.username
                    if self.currentStage == 1:
                        input_str = input(instruction)
                        command = self.translate_command(input_str)

                    else:
                        if self.SendFilename != "":
                            command.append("UPD")
                    # judge and edit TCP message(Done)
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
                            req["filename"] = self.SendFilename
                            with open(self.SendFilename, "rb") as fp:
                                req["filedata"] = fp.read()
                            self.SendFilename = ""
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
                    self.state = states.response_wait
                elif self.state == states.exit:
                    return 0
            except Exception:
                print("Incorrect command.")
                continue

    # Done
    def start(self):
        recv_thread = threading.Thread(target=self.recv)
        recv_thread.setDaemon(True)
        recv_thread.start()
        send_thread = threading.Thread(target=self.send)
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
