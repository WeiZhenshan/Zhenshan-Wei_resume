import socket
import threading
import time
import datetime as dt
import sys
import os
import re


class File:
    type = "file"
    fileName = ""
    fileUploader = ""

    def __init__(self, uploader, filename):
        self.fileUploader = uploader
        self.fileName = filename

class User:
    username = ""
    password = ""
    # client socket
    client = None
    login = False

    def __init__(self, username, password):
        # chushihua
        self.username = username
        self.password = password
        # not used
        self.state = 0
        self.login = False
        self.client = None


class Message:
    type = "message"
    messageAuthor = ""
    messageContent = ""

    def __init__(self, message_author, message_content):
        self.messageAuthor = message_author
        self.messageContent = message_content


class UserManager:
    userFileName = ""
    userList = dict()

    def __init__(self, file_name):
        self.userList = dict()
        self.userFileName = file_name
        # Done
        if os.path.isfile(self.userFileName):
            with open(self.userFileName, 'r') as fe:
                for line in fe.readlines():
                    # 确保没有换行符，结果是有效信息+''的列表
                    line_1 = line.rstrip('\n')
                    split_line = line_1.split(' ')
                    if len(split_line) == 2:
                        username = split_line[0]
                        password = split_line[1]
                        # 创建新的用户对象，并保存在userList中
                        self.userList[username] = User(username, password)
                    else:
                        exit()

    # 创建新账户并登陆
    def createNewUser(self, username, password, client):
        self.userList[username] = User(username, password)
        self.userLogin(username, password, client)
        # 保存到本地文件中，a是追加
        with open(self.userFileName, 'a') as fe:
            fe.write('\n')
            fe.write(self.userList[username].username+" " +self.userList[username].password)
        return 0

    # 用户登录
    def userLogin(self, username, password, client):
        # 用户已存在
        if username in self.userList:
            user = self.userList[username]
            if user.login == False:
                if user.password == password:
                    user.login = True
                    user.client = client
                    return 0
                else:
                    return 2
            else:
                return 1
        return 3

    # 用户注销
    def userLogout(self, username):
        # 用户存在
        if username in self.userList:
            user = self.userList[username]
            if user.login == True:
                user.login = False
                return 0

    def findUserByClient(self, client):
        for user in self.userList:
            if self.userList[user].client == client:
                return self.userList[user]
        return None

    def userClientClose(self, client):
        user = self.findUserByClient(client)
        if user != None:
            self.userLogout(user.username)


class Thread:
    threadAuthor = ""
    threadTitle = ""

    threadMessageList = []

    threadFileList = []

    threadContent = []

    def __init__(self, thread_title, thread_author):
        self.threadTitle = thread_title
        self.threadAuthor = thread_author
        self.threadMessageList = []
        self.threadFileList = []
        self.threadContent = []
        with open(self.threadTitle, 'w') as f:
            f.write(self.threadAuthor)
            f.write('\n')


    # synchronize content of file(rewrite)
    def writeToFile(self):
        with open(self.threadTitle, 'w') as fe:
            fe.write(self.threadAuthor)
            fe.write("\n")
            i = 1
            for line in self.threadContent:
                if line.type == "message":
                    fe.write(str(i) + " ")
                    fe.write(line.messageAuthor+": "+line.messageContent)
                    fe.write('\n')
                    i += 1
                else:
                    fe.write(line.fileUploader+" uploaded "+line.fileName)
                    fe.write('\n')
        return

    def deleteFile(self):
        os.remove(self.threadTitle)
        for file in self.threadFileList:
            os.remove(self.threadTitle + "-" + file.fileName)


class ThreadManager:
    threadList = None

    def __init__(self):
        self.threadList = dict()

    def createThread(self, thread_title, thread_author):
        if thread_title not in self.threadList:
            self.threadList[thread_title] = Thread(thread_title, thread_author)
            return 0
        else:
            return 1

    def removeThread(self, thread_title, username):
        if thread_title in self.threadList:
            if self.threadList[thread_title].threadAuthor == username:
                del self.threadList[thread_title]

                os.remove(thread_title)
                return 0
            else:
                return 2
        else:
            return 1

    def listThreads(self, username):
        thread_titles = self.threadList.keys()
        str = ""
        for thread in thread_titles:
            str += thread
            str += "\n"
        return 0, str

    def postMessage(self, thread_title, message, username):
        if thread_title in self.threadList:
            msg = Message(username, message)
            self.threadList[thread_title].threadMessageList.append(msg)
            self.threadList[thread_title].threadContent.append(msg)
            self.threadList[thread_title].writeToFile()
            return 0
        else:
            return 1

    def deleteMessage(self, thread_title, message_number, username):
        if thread_title in self.threadList:
            if 1 <= message_number and message_number <= len(self.threadList[thread_title].threadMessageList):
                if self.threadList[thread_title].threadMessageList[message_number - 1].messageAuthor == username:
                    self.threadList[thread_title].threadContent.remove(self.threadList[thread_title].threadMessageList[message_number - 1])
                    self.threadList[thread_title].threadMessageList.remove(self.threadList[thread_title].threadMessageList[message_number - 1])
                    self.threadList[thread_title].writeToFile()
                    return 0
                else:
                    return 1
            else:
                return 2
        else:
            return 3

    def editMessage(self, thread_title, message_number, message, username):
        if thread_title in self.threadList:
            if 1 <= message_number and message_number <= len(self.threadList[thread_title].threadMessageList):
                if self.threadList[thread_title].threadMessageList[message_number - 1].messageAuthor == username:
                    self.threadList[thread_title].threadMessageList[message_number - 1].messageContent = message
                    self.threadList[thread_title].writeToFile()
                    return 0
                else:
                    return 1
            else:
                return 2

        else:
            return 3

    def readThread(self, thread_title, username):
        if thread_title in self.threadList:
            content = ""
            i = 1
            for line in self.threadList[thread_title].threadContent:
                if line.type == "message":
                    content += str(i) + " "
                    i += 1
                    content += line.messageAuthor + ": " + line.messageContent
                    content += "\n"
                else:
                    content += line.fileUploader + " uploaded " + line.fileName
                    content += '\n'
            return 0, content

        else:
            return 1, ""

    def uploadFile_confirm(self, thread_title, username, filename):
        if thread_title in self.threadList:
            for file in self.threadList[thread_title].threadFileList:
                if file.fileName == filename:
                    return 1
            return 0
        else:
            return 2

    def uploadFile_send(self, username, thread_title, filename, filedata):
        if thread_title in self.threadList:
            tmp_line = File(username, filename)
            self.threadList[thread_title].threadFileList.append(tmp_line)
            self.threadList[thread_title].threadContent.append(tmp_line)
            self.threadList[thread_title].writeToFile()
            with open(thread_title + "-" + filename, 'wb') as fe:
                fe.write(filedata)
            return 0
        else:
            return 2

    def downloadFile(self, username, thread_title, file_name):
        if thread_title in self.threadList:
            for file in self.threadList[thread_title].threadFileList:
                if file.fileName == file_name:
                    with open(thread_title + "-" + file_name, "rb") as fe:
                        return 0, fe.read()
            return 1, None
        else:
            return 2, None

    def writeToFile(self):
        for thread in self.threadList:
            thread.writeToFile()

    def deleteAllThread(self):
        for thread in self.threadList.values():
            thread.deleteFile()


def StrToCommand(str):
    # eval函数的作用是：把字符串当成表达式解析并求值
    return eval(str)


def CommandToStr(command):
    return str(command)


# done


class Server():
    serverPort = 0
    serverAddress = "127.0.0.1"
    serverAdminPassword = ""
    serverSocket = None
    userManager = None
    threadManager = None
    clientPool = []
    threadPool = []
    exit = False

    def __init__(self, serverPort, adminPassword):
        self.exit = False
        print("服务器初始化")
        self.serverPort = serverPort
        self.serverAdminPassword = adminPassword
        # 初始化服务器连接,尝试绑定socket地址
        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverSocket.bind((self.serverAddress, self.serverPort))

        except:
            print("服务器套接字绑定失败")
            exit()
            # manager initialized
        self.userManager = UserManager("credentials.txt")
        self.threadManager = ThreadManager()

    def shutdown(self, password):
        if self.serverAdminPassword == password:
            users = self.userManager.userList.values()
            for user in users:
                if user.login:
                    self.userManager.userLogout(user.username)
            return 0
        else:
            return 1

    # Done
    def sendToClient(self, msg, client):
        client.sendall(CommandToStr(msg).encode())

    def recvFromClient(self, client):
        username = ""
        isContinue = True
        while isContinue:
            try:
                req = StrToCommand(client.recv(1024).decode())

            # 突发意外情况，来自客户端的连接关闭
            except ConnectionError:
                print("连接错误，客户端意外关闭。")
                self.userManager.userClientClose(client)
                self.clientPool.remove(client)
                client.close()
                return
            else:
                res = dict()
                print(req["username"] + " issued " + req["id"] + " command ")
                # login or create new user ,Done
                if req["id"] == "ATE":
                    res["id"] = "ATE"
                    if req["stage"] == 1:
                        res["stage"] = 1
                        username = req["username"]
                        if username in self.userManager.userList:
                            if self.userManager.userList[username].login:
                                # end in stage 1
                                res["returncode"] = 2
                            else:
                                res["returncode"] = 0
                        else:
                            res["returncode"] = 1
                    elif req["stage"] == 2:
                        res["stage"] = 2
                        username = req["username"]
                        if "newpassword" in req:
                            newpassword = req["newpassword"]
                            self.userManager.createNewUser(username, newpassword, client)
                            res["returncode"] = 0
                            print("New user.")
                            print(req["username"] + " successful login.")
                        else:
                            password = req["password"]
                            return_code = self.userManager.userLogin(username, password, client)
                            if return_code == 0:
                                print(req["username"] + " successful login.")
                            else:
                                print("Incorrect password")
                            res["returncode"] = return_code
                # Create thread
                elif req["id"] == "CRT":
                    res["id"] = "CRT"
                    res["stage"] = 1
                    username = req["username"]
                    thread_title = req["threadtitle"]
                    return_code = self.threadManager.createThread(thread_title, username)
                    res["returncode"] = return_code
                    res["threadtitle"] = thread_title
                    if return_code == 0:
                        print("Thread " + thread_title + " created.")
                    else:
                        print("Thread " + thread_title + " exists.")
                # post message
                elif req["id"] == "MSG":
                    res["id"] = "MSG"
                    res["stage"] = 1
                    username = req["username"]
                    thread_title = req["threadtitle"]
                    message = req["message"]
                    return_code = self.threadManager.postMessage(thread_title, message, username)
                    res["returncode"] = return_code
                    res["threadtitle"] = thread_title
                    if return_code == 0:
                        print("Message posted to " + thread_title + " thread.")
                    else:
                        print(thread_title + " not existed.")
                # Delete message
                elif req["id"] == "DLT":
                    res["id"] = "DLT"
                    res["stage"] = 1
                    username = req["username"]
                    thread_title = req["threadtitle"]
                    message_number = req["messagenumber"]
                    return_code = self.threadManager.deleteMessage(thread_title, message_number, username)
                    res["returncode"] = return_code
                    res["threadtitle"] = thread_title
                    if res["returncode"] == 0:
                        print("Message in " + res["threadtitle"] + " have deleted.")
                    elif res["returncode"] == 1:
                        print("User don't have permission to delete messages.")
                    elif res["returncode"] == 2:
                        print("Message number don't exist.")
                    elif res["returncode"] == 3:
                        print("Thread " + res["threadtitle"] + " not exists.")
                # Read thread
                elif req["id"] == "RDT":
                    res["id"] = "RDT"
                    res["stage"] = 1
                    thread_title = req["threadtitle"]
                    res["threadtitle"] = thread_title
                    res["returncode"], res["content"] = self.threadManager.readThread(thread_title, username)
                    if res["returncode"] == 0:
                        if res["content"] == "":
                            print("Thread" + res["threadtitle"] + " is empty.")
                    else:
                        print("Thread" + res["threadtitle"] + " not exist.")
                # List threads
                elif req["id"] == "LST":
                    res["id"] = "LST"
                    res["stage"] = 1
                    username = req["username"]
                    res["returncode"], res["content"] = self.threadManager.listThreads(username)
                    if res["content"] == "":
                        print("No threads to list.")
                # Edit message
                elif req["id"] == "EDT":
                    res["id"] = "EDT"
                    res["stage"] = 1
                    res["threadtitle"] = req["threadtitle"]
                    username = req["username"]
                    thread_title = req["threadtitle"]
                    message_number = req["messagenumber"]
                    message = req["message"]
                    res["returncode"] = self.threadManager.editMessage(thread_title, message_number, message, username)
                    if res["returncode"] == 0:
                        print("Message in " + res["threadtitle"] + " have modify.")
                    elif res["returncode"] == 1:
                        print("User don't have permission to edit message.")
                    elif res["returncode"] == 2:
                        print("Message number not exist.")
                # Remove thread
                elif req["id"] == "RMV":
                    res["id"] = "RMV"
                    res["stage"] = 1
                    username = req["username"]
                    thread_title = req["threadtitle"]
                    res["threadtitle"] = req["threadtitle"]
                    res["returncode"] = self.threadManager.removeThread(thread_title, username)
                    if res["returncode"] == 0:
                        print("Thread " + res["threadtitle"] + " removed.")
                    elif res["returncode"] == 1:
                        print("Thread " + res["threadtitle"] + " not exist.")
                    elif res["returncode"] == 2:
                        print("The thread was created by another user and cannot be removed.")
                # Upload file
                elif req["id"] == "UPD":
                    res["id"] = "UPD"
                    username = req["username"]
                    thread_title = req["threadtitle"]
                    file_name = req["filename"]
                    res["filename"] = file_name
                    res["threadtitle"] = thread_title
                    if req["stage"] == 1:
                        res["stage"] = 1
                        res["returncode"] = self.threadManager.uploadFile_confirm(thread_title, username, file_name)
                        res["threadtitle"] = req["threadtitle"]
                        res["filename"] = req["filename"]
                        if res["returncode"] == 1:
                            print("File exist.")
                        else:
                            print("Thread not exist.")
                    elif req["stage"] == 2:
                        res["stage"] = 2
                        file_data = req["filedata"]
                        res["returncode"] = self.threadManager.uploadFile_send(username, thread_title, file_name,
                                                                               file_data)
                        print(res["filename"] + " uploaded to " + res["threadtitle"] + " thread.")
                # Download file
                elif req["id"] == "DWN":
                    res["id"] = "DWN"
                    username = req["username"]
                    thread_title = req["threadtitle"]
                    file_name = req["filename"]
                    res["threadtitle"] = thread_title
                    res["filename"] = file_name
                    res["returncode"], res["filedata"] = self.threadManager.downloadFile(username, thread_title,
                                                                                         file_name)
                    if res["returncode"] == 0:
                        print("File " + res["filename"] + " download.")
                    elif res["returncode"] == 1:
                        print("File not exist.")
                    elif res["returncode"] == 2:
                        print("Thread " + res["threadtitle"] + " not exist.")
                # Exit
                elif req["id"] == "XIT":
                    res["id"] = "XIT"
                    username = req["username"]
                    res["returncode"] = self.userManager.userLogout(username)
                    res["username"] = username
                    self.clientPool.remove(client)
                    isContinue = False
                    if res["returncode"] == 0:
                        print("User " + res["username"] + " logout.")
                        print("Goodbye.")
                    elif res["returncode"] == 1:
                        print("User " + res["username"] + " repeat logout.")
                    elif res["returncode"] == 2:
                        print("User " + res["username"] + " not exist.")
                # Shutdown
                elif req["id"] == "SHT":
                    res["id"] = "SHT"
                    username = req["username"]
                    password = req["password"]
                    res["returncode"] = self.shutdown(password)
                    if res["returncode"] == 0:
                        print("Goodbye. Server shutdown.")
                        for i in self.clientPool:
                            i.sendall(CommandToStr(res).encode())
                        self.exit = True
                    else:
                        print("Admin password incorrect.")
                self.sendToClient(res, client)

    # Done
    def accept(self):
        self.serverSocket.listen(20)
        print("Waiting for the only one client.")
        client, _ = self.serverSocket.accept()
        print("Client connected")
        self.clientPool.append(client)
        thread = threading.Thread(target=self.recvFromClient, args=(client,))
        thread.setDaemon(True)
        thread.start()

    # Done
    def start(self):
        thread = threading.Thread(target=self.accept)
        thread.setDaemon(True)
        thread.start()
        while True:
            if self.exit:
                self.threadManager.deleteAllThread()
                return


if __name__ == "__main__":
    server_port = int(sys.argv[1])
    admin_password = sys.argv[2]
    server = Server(server_port, admin_password)
    server.start()
