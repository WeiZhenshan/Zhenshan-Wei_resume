import socket
import threading
import time
import datetime as dt
import sys
import os
import re



def StrToCommand(str):
    # eval函数的作用是：把字符串当成表达式解析并求值
    return eval(str)


def CommandToStr(command):
    return str(command)


class File:
    type = "file"
    fileName = ""
    fileUploader = ""

    def __init__(self, uploader, filename):
        self.fileUploader = uploader
        self.fileName = filename

    def toString(self):
        return self.fileUploader + " uploaded " + self.fileName


class Message:
    type = "message"
    messageAuthor = ""
    messageContent = ""

    def __init__(self, message_author, message_content):
        self.messageAuthor = message_author
        self.messageContent = message_content

    def toString(self):
        return self.messageAuthor + ": " + self.messageContent


class Thread:
    threadAuthor = ""
    threadTitle = ""
    # 专门装串的message的list，方便内容变动时编号的改变
    threadMessageList = []
    # 只装串的file的list
    threadFileList = []
    # 即装串的message 也装串的文件的列表
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

    def postMessage(self, message, username):
        tmp_line = Message(username, message)
        self.threadMessageList.append(tmp_line)
        self.threadContent.append(tmp_line)
        self.writeToFile()
        return 0

    def deleteMessage(self, message_number, username):
        if 1 <= message_number and message_number <= len(self.threadMessageList):
            if self.threadMessageList[message_number - 1].messageAuthor == username:
                self.threadContent.remove(self.threadMessageList[message_number - 1])
                self.threadMessageList.remove(self.threadMessageList[message_number - 1])
                self.writeToFile()
                return 0
            else:
                return 1
        else:
            return 2

    def readThread(self, username):
        content = ""
        i=1
        for line in self.threadContent:
            if line.type=="message":
                content+=str(i)+" "
                i+=1
            content+=line.toString()
            content+='\n'
        return 0,content

    def editMessage(self, message_number, message, username):
        if 1 <= message_number and message_number <= len(self.threadMessageList):
            if self.threadMessageList[message_number - 1].messageAuthor == username:
                self.threadMessageList[message_number-1].messageContent=message
                self.writeToFile()
                return 0
            else:
                return 1
        else:
            return 2

    def uploadFile_confirm(self,username,filename):
        for file in self.threadFileList:
            if file.fileName==filename:
                return 1
        return 0

    def uploadFile_send(self, username, thread_title, file_name, file_data):
        tmp_line=File(username,file_name)
        self.threadFileList.append(tmp_line)
        self.threadContent.append(tmp_line)
        self.writeToFile()
        with open(thread_title+"-"+file_name,'wb') as fp:
            fp.write(file_data)
        return 0

    def downloadFile(self, username, thread_title, filename):
        for file in self.threadFileList:
            if file.fileName==filename:
                with open(thread_title+"-"+filename,"rb") as fp:
                    return 0, fp.read()
        return 1, None

    def writeToFile(self):
        with open(self.threadTitle, 'w') as fe:
            fe.write(self.threadAuthor)
            fe.write("\n")
            i = 1
            for line in self.threadContent:
                if line.type == "message":
                    fe.write(str(i) + " ")
                    fe.write(line.toString)
                    fe.write('\n')
                    i += 1
                else:
                    fe.write(line.toString())
                    fe.write('\n')
        return

    def deleteFile(self):
        os.remove(self.threadTitle)
        for file in self.threadFileList:
            os.remove(self.threadTitle+"-"+file.fileName)

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
                # 删除串对应的文件（同文件夹）
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
            #下层的同名函数
            return self.threadList[thread_title].postMessage(message, username)
        else:
            return 1

    def deleteMessage(self, thread_title, message_number, username):
        if thread_title in self.threadList:
            return self.threadList[thread_title].deleteMessage(message_number, username)
        else:
            return 3

    def editMessage(self, thread_title, message_number, message, username):
        if thread_title in self.threadList:
            return self.threadList[thread_title].editMessage(message_number, message, username)
        else:
            return 3

    def readThread(self, thread_title, username):
        if thread_title in self.threadList:
            return self.threadList[thread_title].readThread(username)
        else:
            return 1,""

    def uploadFile_confirm(self, thread_title, username, filename):
        if thread_title in self.threadList:
            return self.threadList[thread_title].uploadFile_confirm(username,filename)
        else:
            return 2

    def uploadFile_send(self, username, thread_title, filename, filedata):
        if thread_title in self.threadList:
            return self.threadList[thread_title].uploadFile_send(username,thread_title,filename,filedata)
        else:
            return 2

    def downloadFile(self, username, thread_title, file_name):
        if thread_title in self.threadList:
            return self.threadList[thread_title].downloadFile(username,thread_title,file_name)
        else:
            return 2,None

    def writeToFile(self):
        for thread in self.threadList:
            thread.writeToFile()

    def deleteAllThread(self):
        for thread in self.threadList.values():
            thread.deleteFile()


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

    # not necessary
    def toString(self):
        return self.username + " " + self.password


class UserManager:
    userFileName = ""
    userList = dict()

    def __init__(self, file_name):
        self.userList = dict()
        self.userFileName = ""
        print("用户管理器初始化")
        self.userFileName = file_name
        print("从文件：", self.userFileName)
        # 读取文件内容，并转换为字典{username：passsword}
        if os.path.isfile(self.userFileName):
            with open(self.userFileName, 'r') as fp:
                for line in fp.readlines():
                    # 确保没有换行符，结果是有效信息+''的列表
                    line = line.split('\n')
                    split_rst = line[0].split(' ')
                    if len(split_rst) == 2:
                        username = split_rst[0]
                        password = split_rst[1]
                        # 创建新的用户对象，并保存在userList中
                        self.userList[username] = User(username, password)
                        # print(username)
                        # print(password)
                    else:
                        print("credentials格式错误")
                        exit()
        else:
            pass

    # 创建新账户并登陆
    def createNewUser(self, username, password, client):
        self.userList[username] = User(username, password)
        self.userLogin(username, password, client)
        # 保存到本地文件中，a是追加
        with open(self.userFileName, 'a') as fp:
            fp.write('\n')
            fp.write(self.userList[username].toString())
        return 0

    # 用户登录
    def userLogin(self, username, password, client):
        # 用户已存在
        if username in self.userList:
            user = self.userList[username]
            if user.login == True:
                return 1
            else:
                if user.password == password:
                    user.login = True
                    user.client = client
                    return 0
                else:
                    return 2
        return 3

    # 用户注销
    def userLogout(self, username):
        # 用户存在
        if username in self.userList:
            user=self.userList[username]
            if user.login==True:
                user.login=False
                return 0
            else:
                return 1
        # 用户不存在
        return 2

    def findUserByClient(self, client):
        for user in self.userList:
            if self.userList[user].client==client:
                return self.userList[user]
        return None

    def userClientClose(self, client):
        user = self.findUserByClient(client)
        if user != None:
            self.userLogout(user.username)


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

    def sendToClient(self, msg, client):
        client.sendall(CommandToStr(msg).encode())

    def recvFromClient(self, client):
        username = ""
        isContinue = True
        while isContinue:
            try:
                req = StrToCommand(client.recv(1024).decode())

            # 突发意外情况，来自客户端的连接关闭
            except ConnectionError as e:
                print("连接错误，客户端意外关闭。")
                self.userManager.userClientClose(client)
                self.clientPool.remove(client)
                client.close()
                return
            else:
                res = dict()
                print(req["username"] + " issued " + req["id"] + " command ")
                # login or create new user
                if req["id"] == "ATE":
                    res["id"] = "ATE"
                    if req["stage"] == 1:
                        res["stage"] = 1
                        username = req["username"]
                        if username in self.userManager.userList:
                            res["returncode"] = 0
                            if self.userManager.userList[username].login:
                                res["returncode"] = 2
                        else:
                            res["returncode"] = 1
                    elif req["stage"] == 2:
                        res["stage"] = 2
                        username = req["username"]
                        if "newpassword" in req:
                            newpassword = req["newpassword"]
                            self.userManager.createNewUser(username, newpassword, client)
                            res["returncode"] = 0
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
                        print(thread_title + " created.")
                    else:
                        print(thread_title + " existed.")
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
                    res["returncode"] = self.threadManager.readThread(thread_title, username)
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

    # 同时服务多个客户端的线程方式
    def acceptclient(self):
        self.serverSocket.listen(20)
        print("Waiting for the only one client.")
        client, _ = self.serverSocket.accept()
        print("Client connected")
        self.clientPool.append(client)
        thread = threading.Thread(target=self.recvFromClient, args=(client,))
        thread.setDaemon(True)
        thread.start()

    def start(self):
        thread = threading.Thread(target=self.acceptclient)
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

#python HK201119010/server.py 8080 12345