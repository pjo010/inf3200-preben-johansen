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

#logging.debug('This message should go to the log file')
#logging.debug('So should this')
#logging.warning('And this, too')
#logging.error('Error message')
#logging.critical('critical')
print "Hello World!"

MAX_CONTENT_LENGHT = 1024       # Maximum length of the content of the http request (1 kilobyte)
MAX_STORAGE_SIZE = 104857600    # Maximum total storage allowed (100 megabytes)
PORTNR = 8009
storageBackendNodes = list()
hashBackendNodes = list()




class BackendStorageHandler:
    def __init__(self):
        self.backmap = dict()
        self.hashmap = dict()
        self.maphash = dict()
        self.table = dict()
        self.size = 0
        self.numelements = 0
        self.nodeListReady = False
        self.expectedNodes = 0

        self.nextNode = None        #
        self.previousNode = None    #
        self.ownNode = None         #

        self.ownHash = None
        self.previousKey = None
        self.ownIndex = None
    #Hashes and sort the node list
    def hashAndSort(self):
        self.ownNode = socket.gethostname()
        self.ownNode = self.ownNode[:-6]
        logging.debug(self.ownNode)
        for nodes in storageBackendNodes:
            tempHashObj = hashlib.sha1(nodes)
            newHash = tempHashObj.hexdigest()
            logging.debug('Hash: %s, node: %s', newHash, nodes)
            hashBackendNodes.append(newHash)
            self.hashmap[nodes] = newHash
            self.maphash[newHash] = nodes
        hashBackendNodes.sort()
        for hashed in hashBackendNodes:
            logging.debug(self.hashToNode(hashed))
    #Helper functions to find hashes and nodes
    def nodeToHash(self, node):
        value = self.hashmap[node]
        logging.debug('node: %s, return: %s', node, value)
        return value

    def hashToNode(self, hashedNode):
        value = self.maphash[hashedNode]
        return value

    #Function which handles the nodes
    def handleNodes(self, key, value):
        self.expectedNodes = int(value)
        
        logging.debug('Handling nodes to library, %s, %s', key, value)

        storageBackendNodes.append(key)
        
        if self.expectedNodes is len(storageBackendNodes):


            self.hashAndSort()
            #Need to address the adresses
        
        
            self.ownIndex = hashBackendNodes.index(self.nodeToHash(self.ownNode))
            logging.debug(self.ownIndex)
            if self.ownIndex == self.expectedNodes - 1:
                self.nextHash = hashBackendNodes[0]
                self.nextNode = self.hashToNode(self.nextHash)
                self.nextHash = int(self.nextHash, 16)
            else:
                self.nextHash = hashBackendNodes[self.ownIndex + 1]
                self.nextNode = self.hashToNode(self.nextHash)
                self.nextHash = int(self.nextHash, 16)
            #Hashing the adress

            self.ownHash = int(self.nodeToHash(self.ownNode), 16)

            self.nodeListReady = True


    def handlePut(self, key, value, size):
        #Determinate if the key are present
        if self.nodeListReady != True:
            #Receive nodemap
            self.handleNodes(key, value)
        else:

            
            #Hashing the key to see if the key are represented on this node
            hashObj = hashlib.sha1(key)
            hashValue = int(hashObj.hexdigest(), 16)
            #if last node
            if  self.nextHash < self.ownHash:
                #if in span larger or lower then next
                if  hashValue > self.ownHash or hashValue < self.nextHash:

                
                    self.table[key] = hashValue
                    self.backmap[key] = value
                    self.size = self.size + size
                    self.numelements = self.numelements +1
                
                else:
                    
                    node = self.nextNode
                
                    try:
                        conn = httplib.HTTPConnection(node, PORTNR)
                        conn.request("PUT", key, value)
                        response = conn.getresponse()
                        if response.status != 200:
                            logging.error(response.status)
                            return False
                    except:
                        return False

            else:
                #if in span, store, else send further
                if hashValue > self.ownHash and hashValue < self.nextHash:
                    self.backmap[key] = value
                    self.table[key] = hashValue
                    self.size = self.size + size
                    self.numelements = self.numelements +1
                else:

                    node = self.nextNode
                    try:
                        conn = httplib.HTTPConnection(node, PORTNR)
                        conn.request("PUT", key, value)
                        response = conn.getresponse()
                        if response.status != 200:
                            return False
                    except:
                        return False
                    return True

            
    #Handles GET
    def handleGet(self, key):
        #Debug if key has been searched
        if key == self.previousKey:
            logging.debug('Has searched every node and found none')
        #return size
        if key == '/size':
            return self.size
        #Looks for value, if not found, look in the next
        value = self.backmap.get(key)
        if value:
            return value
        else:
            node = self.nextNode
            self.previousKey = key
            try:
                conn = httplib.HTTPConnection(node, PORTNR)
                conn.request("GET", key)
                response = conn.getresponse()
                if response.status != 200:
                    print response.reason
                    return False
                value = response.read()
            except:
                print "Unable to send GET request"
                return False
            return value
            
        





class BackendHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    global backend 
    backend = BackendStorageHandler()
    
    # Returns the 
    def do_GET(self):


        logging.debug(self.path)
        key = self.path
  
        value = backend.handleGet(key)
      
        # Write header
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()
        
        # Write Body
        self.wfile.write(value)
        
    def do_PUT(self):

        contentLength = int(self.headers['Content-Length'])

        backend.handlePut(self.path, self.rfile.read(contentLength), contentLength)
        
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write('garbage')
        
    def sendErrorResponse(self, code, msg):
        loggin.error(code)
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(msg)
        
class BackendHTTPServer(BaseHTTPServer.HTTPServer):
    
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
    # Start the webserver which handles incomming requests
    try:
        httpd = BackendHTTPServer(("",httpserver_port), BackendHttpHandler)
        server_thread = threading.Thread(target = httpd.serve)
        #The entire Python program exits when no alive non-daemon threads are left
        server_thread.daemon = True
        server_thread.start()
        
        def handler(signum, frame):
            print "Stopping http server..."
            httpd.stop()
        signal.signal(signal.SIGINT, handler)
    except:
        print "Error: unable to http server thread"
        logging.error('Error: unable to http server thread')
        

    
    # Wait for server thread to exit
    server_thread.join(100)

