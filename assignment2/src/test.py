import BaseHTTPServer
import sys
import getopt
import threading
import signal
import socket
import httplib
import random
import string
import logging
import hashlib

logging.basicConfig(filename=socket.gethostname() + 'node.log',level=logging.DEBUG, 
    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


print "Hello World!"


PORTNR = 27000


nodeList        = list()    #addresses
fullNodeList    = list()    #addresses and portnr
hashNodes       = list()    #hashed addresses


class LeaderElection:
    def __init__(self):
        self.ready          = False
        self.noLeader       = True
        self.lid            = None
        self.higherIndex    = None
        self.ownNode        = socket.gethostname()
        self.ownNode        = self.ownNode[:-6]
        self.index          = None
        self.higher         = None
    #Method to check key
    def evaluateKey(self, key):
        #GET
        if key == "/getCurrentLeader":
            return 1
        #GET
        elif key == "/getNodes":
            return 2
        #GET
        elif key == "/election":
            return 3
        #PUT
        elif key == "/coordinator":
            return 4
        #GET
        elif key == "/enqueueLeader":
            return 5
        elif key == "/imAlive":
            return 6
        elif key == "/testing":
            return 7
        #GET
        elif key == "/testSystem":
            return 8
        #GET
        elif key == "/startElection":
            return 9
        else:
            return 0

    def handlePut(self, key, value):
        #logging.debug("PUT key = " + key + " value = " + value)
        if self.ready == False:
            nodeList.sort()
            self.index = nodeList.index(self.ownNode)
            #logging.debug(self.index)
            if self.index + 1 > len(nodeList) - 1:
                self.higher = False
                self.lid = self.index
            else:
                self.higher = True
                self.higherIndex = self.index + 1
            self.ready = True
        #coordinator
        if self.evaluateKey(key) == 4:
            #logging.debug("New leader")

            self.noLeader = False
            self.lid = int(value)
            #logging.debug(nodeList[int(value)] + " is leader")
            if nodeList[self.index + 1] != nodeList[int(value)]:
                try:
                    conn = httplib.HTTPConnection(nodeList[self.index + 1], PORTNR)
                    #logging.debug("Has sent /coordinator to: " + nodeList[self.index + 1])
                    conn.request("PUT", "/coordinator", str(value))
                    response = conn.getresponse()
                    if response.status != 200:
                        #logging.error(response.status + response.reason)
                        return "something wong"
                    conn.close()
                    
                except (httplib.HTTPException, socket.error) as ex:
                    logging.error( "Error: %s" % ex )
            else:
                #logging.debug("next is leader")
                return

    def enqueueLeader(self):
        tmpNode = None
        for node in reversed(nodeList):
            if node != self.ownNode:
                tmpNode = node
                try:
                    conn = httplib.HTTPConnection(node, PORTNR)
                    logging.debug("Send EQL to: " + node)
                    conn.request("GET", "/enqueueLeader")
                    response = conn.getresponse()
                    if response.status != 200:
                        #logging.error(response.status + response.reason)
                        return False
                    if response.read() == "NoOK":
                        logging.debug("Received NoOK signal")
                    else:
                        break
                    logging.debug("something: " + respons.read())
                    conn.close()
                    return node
                except:
                    logging.error("Error when connecting for enqueue")
                    return False
        return tmpNode
    #Elect leader method
    def electLeader(self):
        j = 0
        if self.higher:
            for i in range(self.higherIndex, len(nodeList)):
                try:
                    conn = httplib.HTTPConnection(nodeList[i], PORTNR)
                    conn.request("GET", "/election")
                    response = conn.getresponse()
                    if response.status != 200:
                        logging.error(response.status + response.reason)
                        return False
                    if response.read() == "OK":
                        logging.debug("Received ok signal")
                        break
                    else:
                        nodeList.remove(nodeList[i])
                    conn.close()
                    return self.lid
                    
                except:
                    logging.error("Error when connecting for election")
                    return False
        else:
            logging.debug("Broadcasting me " + self.ownNode + "as leader")
            self.noLeader = False
            self.lid = self.index
            return self.lid
    #testNodes
    def testNodes(self):
        for node in nodeList:
            if node != self.ownNode:
                try:
                    conn = httplib.HTTPConnection(node, PORTNR)
                    conn.request("GET", "/testing")
                    response = conn.getresponse()
                    if response.status != 200:
                        logging.error(response.status + response.reason)
                        return False
                    if response.read() == "OK":
                        logging.debug("Received ok signal")
                    else:
                        logging.debug("Node: " + node +" is not responding")
                        nodeList.remove(node)
                    conn.close()
                    return True
                except:
                    logging.error("Error when connecting for testing")
                    return False

    #Handles GET
    def handleGet(self, key):
        #Indexing and sorting
        if self.ready == False:
            nodeList.sort()
            self.index = nodeList.index(self.ownNode)
            if self.index + 1 > len(nodeList) - 1:
                self.higher = False
            else:
                self.higher = True
                self.higherIndex = self.index + 1
            if self.index == 0:
                self.electLeader()
            self.ready = True

        #test if all alive
        if self.evaluateKey(key) == 7:
            return "OK"

        if self.evaluateKey(key) == 8:
            if self.testNodes():
                return "Test of system ok \n"
            else:
                return "Not all responding"
        #getCurrentLeader
        if self.evaluateKey(key) == 1:
            if self.noLeader == False:
                #Return leader

                s = ":"
                node = nodeList[self.lid]
                port = str(PORTNR)
                seq = (node, port)
                leaderString = s.join(seq) 
                return leaderString + "\n"
            else:
                s = ":"
                node = self.enqueueLeader()
                port = str(PORTNR)
                seq = (node, port)
                leaderString = s.join(seq)
                return leaderString + "\n"
                    


        #getNodes
        elif self.evaluateKey(key) == 2:
            #Return node pairs
            returnstring = ""
            s = ":"
            port = str(PORTNR)
            for node in nodeList:
                seq = (node, port)
                ss = s.join(seq)
                returnstring = returnstring + ss + "\n"
            return returnstring

        #election
        elif self.evaluateKey(key) == 3:
            logging.debug("Election called")
            returnValue = self.electLeader()
            self.lid = returnValue
            logging.debug("Returning ok signal")
            return "OK"
        #enqueueLeader
        elif self.evaluateKey(key) == 5:
            if self.noLeader == True:
                logging.debug("No leader")
                return "NoOK"
            else:
                logging.debug("EQL: " + self.ownNode)
                return self.ownNode





            
        





class leaderHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    global leader 
    leader = LeaderElection()
    
    # Returns the 
    def do_GET(self):

        #logging.debug("Starting do_GET")
        key = self.path
  
        value = leader.handleGet(key)

        # Write header
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()
        
        # Write Body
        self.wfile.write(value)
        #logging.debug("Ending do_GET")
        
    def do_PUT(self):
        #logging.debug("Starting do_PUT")
        contentLength = int(self.headers.get('Content-Length'))

        leader.handlePut(self.path, self.rfile.read(contentLength))
        
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write('garbage')
        #logging.debug("Ending do_PUT")
        
    def sendErrorResponse(self, code, msg):
        loggin.error("FAULT_CODE: " +str(code))
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(msg)
        
class leaderHTTPServer(BaseHTTPServer.HTTPServer):
    
    def server_bind(self):
        BaseHTTPServer.HTTPServer.server_bind(self)
        self.socket.settimeout(1)
        self.run = True

    def get_request(self):
        while self.run == True:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(None)
                return (sock, addr)
            except socket.timeout:
                if not self.run:
                    raise socket.error

    def stop(self):
        self.run = False

    def serve(self):
        while self.run == True:
            self.handle_request()

if __name__ == '__main__':


    httpserver_port = PORTNR
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'x', ['runtests', 'port='])
    except getopt.GetoptError:
        print sys.argv[0]
        sys.exit(2)
    
    if len(args) <= 0:
        print sys.argv[0]
        sys.exit(2)


    for node in args:
        if node.find("compute") != -1 and len(node) <= 12:
            nodeList.append(node)
            print "Added", node, "to the list of nodes"
            logging.debug(node)

    # Start the webserver which handles incomming requests
    try:
        httpd = leaderHTTPServer(("",httpserver_port), leaderHttpHandler)
        server_thread = threading.Thread(target = httpd.serve)
        #The entire Python program exits when no alive non-daemon threads are left
        server_thread.daemon = True
        server_thread.start()
        
        def handler(signum, frame):
            print "Stopping http server..."
            httpd.stop()
            sys.exit(0)
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
    except:
        print "Error: unable to http server thread"
        logging.error('Error: unable to http server thread')
        

    
    # Wait for server thread to exit
    server_thread.join(100)

