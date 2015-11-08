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

logging.basicConfig(filename='frontend.log',level=logging.DEBUG, 
    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


PORTNR = 27000

storageBackendNodes = list()
httpdServeRequests = True

class StorageServerFrontend:


	def sendGET(self, key):

		node = random.choice(storageBackendNodes)
		try:
			conn = httplib.HTTPConnection(node, PORTNR)
			conn.request("GET", key)
			response = conn.getresponse()
			if response.status != 200:
				print response.reason
				return False
			value = response.read()
			return value
		except:
			print "Unable to send GET request"
			logging.debug('Unable to send Get request')

		
	def sendPUT(self, key, value, size):

		self.size = self.size + size
		node = random.choice(storageBackendNodes)

	
		try:
			conn = httplib.HTTPConnection(node, PORTNR)
			conn.request("PUT", key, value)
			response = conn.getresponse()
			if response.status != 200:
				logging.error(response.status)
				return False
		except:
			return False
		return True





class FrontendHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	global frontend 
	frontend = StorageServerFrontend()
	
	# Returns the 
	def do_GET(self):

		logging.debug('Do_Get_Path: %s', self.path)
		key = self.path
		value = frontend.sendGET(key)
		
		if value is None:
			self.sendErrorResponse(404, "Key not found")
			return
		
		# Write header
		self.send_response(200)
		self.send_header("Content-type", "application/octet-stream")
		self.end_headers()
		
		# Write Body
		self.wfile.write(value)
		
	def do_PUT(self):

		contentLength = int(self.headers['Content-Length'])
		logging.debug('Do_Put_Path: %s', self.path)
		if contentLength <= 0 or contentLength > MAX_CONTENT_LENGHT:
			self.sendErrorResponse(400, "Content body to large")
			return
		
		frontend.size += contentLength
		if frontend.size > MAX_STORAGE_SIZE:
			self.sendErrorResponse(400, "Storage server(s) exhausted")
			return
		
		# Forward the request to the backend servers
		frontend.sendPUT(self.path, self.rfile.read(contentLength), contentLength)
		
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		
	def sendErrorResponse(self, code, msg):
		self.send_response(code)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(msg)
		
class FrontendHTTPServer(BaseHTTPServer.HTTPServer):
	
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
		
class StorageServerTest:

	testsToRun = 100

	def __init__(self, url, portnumber):
		self.url = url
		self.portnumber = portnumber
		
	def generateKeyValuePair(self):
		key = ''
		value = ''
		
		for i in range(random.randint(10, 20)):
			key += random.choice(string.letters)
		
		for i in range(random.randint(20, 40)):
			value += random.choice('1234567890')
		
		return key, value

	def run(self):
		keyValuePairs = dict()
		
		# Generate random unique key, value pairs
		for i in range(self.testsToRun):
			while True:
				key, value = self.generateKeyValuePair()
				if key not in keyValuePairs:
					break
			keyValuePairs[key] = value
		
		# Call put to insert the key/value pairs
		for key, value in keyValuePairs.iteritems():
			if self.putTestObject(key, value) != True:
				print "Error putting", key, value
				return False
		
		# Validate that all key/value pairs are found
		for key, value in keyValuePairs.iteritems():
			if self.getTestObject(key, value) != True:
				print "Error getting", key, value
				return False
		
		return True
	
	
	def getTestObject(self, key, value):
		print "GET(key, value):", key, value
		
		try:
			conn = httplib.HTTPConnection("localhost", PORTNR)
			conn.request("GET", key)
			response = conn.getresponse()
			if response.status != 200:
				print response.reason
				return False
				
			retrievedValue = response.read()
		except:
			print "Unable to send GET request"
			return False
		
		if value != retrievedValue:
			print "Value is not equal to retrieved value", value, "!=", retrievedValue
			return False
		
		return True
	
	def putTestObject(self, key, value):
		print "PUT(key, value):", key, value
		
		try:
			conn = httplib.HTTPConnection("localhost", PORTNR)
			conn.request("PUT", key, value)
			response = conn.getresponse()
			
		except:
			return False
		
		return True
		
if __name__ == '__main__':
	
	run_tests = False
	httpserver_port = PORTNR
	
	try:
		optlist, args = getopt.getopt(sys.argv[1:], 'x', ['runtests', 'port='])
	except getopt.GetoptError:
		print sys.argv[0] + ' [--port portnumber(default=8000)] [--runtests] compute-1-1 compute-1-1 ... compute-N-M'
		sys.exit(2)
	
	if len(args) <= 0:
		print sys.argv[0] + ' [--port portnumber(default=8000)] [--runtests] compute-1-1 compute-1-1 ... compute-N-M'
		sys.exit(2)
	

	# Nodelist
	for node in args:
		storageBackendNodes.append(node)
		print "Added", node, "to the list of nodes"
	print len(storageBackendNodes)
	# Start the webserver which handles incomming requests
	try:
		httpd = FrontendHTTPServer(("",httpserver_port), FrontendHttpHandler)
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
	
	# Run a series of tests to verify the storage integrity
	if run_tests:
		print "Running tests..."
		tests = StorageServerTest("localhost", httpserver_port)
		tests.run()

		httpd.stop()
	# Wait for server thread to exit
	server_thread.join(100)

      

