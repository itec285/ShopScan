#!rest-api/bin/python

from flask import Flask, request, jsonify#, copy_current_request_context
from flask_restful import Resource, Api
from json import dumps
import datetime, socket, sqlite3

app = Flask(__name__)
api = Api(app)

class GetItemInfo_Meta(Resource):
#This returns a single item information, given a store code and upc.
	def get(self,store_code, upc, external_IPAddress, internal_IPAddress):
		
		real_IPAddress = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
		print ('\n\n\n-------------------\n New Request from: ' + real_IPAddress)
		
		print ('#######    NEW ITEM INFO REQUEST - ' +  str(datetime.datetime.now()) + '    #######')
		
		#Connect to the databases
		conn = sqlite3.connect('ShopAndScan.db')
		logconn = sqlite3.connect('RequestLog.db')
		
		#Perform query and return row with that store's data
		#Note that the below is safe from SQL Injection attacks.  See https://www.athenic.net/posts/2017/Jan/21/preventing-sql-injection-in-python/
		query = conn.execute("SELECT * FROM Products WHERE UPC = ? AND StoreCode =?", (upc, store_code.upper()))
		
		#Get the data in the results, and also get the column names which is the [0] result using the .description
		queryResult = (query.fetchone())
		
		#First, make sure that a valid row in the DB exists.
		if str(queryResult) == 'None':
			#Invalid store code, log the error and return 'Invalid Store Code'			
			print ('Error, supplied store_code ' + store_code.upper() + ' and UPC ' + upc+ ' did not match any records')
			return ('ERROR:Invalid Store Code')
		else:
			print ('Returned data for UPC ' + str(queryResult[2]) )
			columns = [desc[0] for desc in query.description]
			# Since we have at least one result, make a dictionary format answer of column name and resulting values
			# e.g. 'RecordID': 4, 'StoreCode': '0001', 'Upc': '005', 'Fineline': 'DEPOSIT'
			# See https://stackoverflow.com/questions/12270679/how-to-use-column-names-when-creating-json-object-python for information on this.
			answer = dict(zip(columns, queryResult))
			
		#Before we query the request, log it
		now = datetime.datetime.now()
		requestType = 'GetItemInfo'
		query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, Upc, ExternalIPAddress, InternalIPAddress, \
			RealIPAddress) VALUES(?,?,?,?,?,?,?)", (now, requestType, store_code.upper(), upc, external_IPAddress, internal_IPAddress, real_IPAddress))
				
		# Save (commit) the changes and close the DBs
		conn.commit()
		logconn.commit()
		conn.close()
		logconn.close()
		
		#Send an answer back.  Note that there's a lot of ways to do this below.  I worked with Matt 
		# to come up with the best way to send data back for him.
		#return str(queryResult) #Return the raw answer in text form
		#return str(queryResult[1]) #Return a single element of the result (1 field)
		#return jsonify(str(queryResult))
		#return jsonify({'Data': (queryResult)})
		#return jsonify({'Data':queryResult[1]})
		#return jsonify({'Upc': (returnedUpc), 'ReportDescription':(returnedReportDescription)})
		return jsonify(answer) #Return a JSON list like the following 'RecordID': 4, 'StoreCode': '0001', 'Upc': '005', 'Fineline': 'DEPOSIT'

class SendTransactionItems_Meta(Resource):
#This is the opposite of many of the functions and actually takes data via a POST request.  It then records items in a new transaction and returns the trxid

		#@copy_current_request_context
		def post(self):
			
			real_IPAddress = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
			print ('-------------------\n New Request from: ' + real_IPAddress)	
			print ('    [--Start of Request Headers--] \n' + str(request.headers) + '    [--End of Request Headers--] \n')	
			print ('    [--Start of Request Text--] \n' + str(request.data.decode('utf-8')) + '    [--End of Request Text--] \n')	
			
			#Connect to the databases
			conn = sqlite3.connect('ShopAndScan.db')
			logconn = sqlite3.connect('RequestLog.db')
				
			
			if request.headers['Content-Type'] == 'text/plain':
			
				#Get the contents of what I was sent
				contents = request.data.decode('utf-8')
				#Now, split it based on comma.  
				contents = contents.split(",")
								
				store_code = contents[0].upper()
				print ('    [--Number of elements--] ' + len(contents) + '    [--Store Code-]' + store_code)	
				
				# #Get the individual modules from the contents (note there are 26 modules including module 0
				# module0, module1, module2, module3, module4, module5, module6, module7, module8, module9, \
				# module10, module11, module12, module13, module14, module15, module16, module17, module18, \
				# module19, module20, module21, module22, module23, module24, module25 = contents[1:27] 
								
				# numberOfClients = contents[27]
				# serialNumber = contents[28]
				# version = contents[29]
				# location0Name = contents[30]
				# location0Address = contents[31]
				# location0Phone = contents[32]
				
				# #For debug purposese only
				# '''
				# returnString = "Store Code and modules 0 and 25: " + " " + store_code + " " + module0 + " " + module25 			
				# returnString += "|  Number of Clients:" + numberOfClients 
				# returnString += "|  Serial Number:" + serialNumber 
				# returnString += "|  Version:" + version 
				# returnString += "|  Location 0 Name:" + location0Name 
				# returnString += "|  Location 0 Address:" + location0Address 
				# returnString += "|  Location 0 Phone:" + location0Phone 
				# return returnString
				# '''
				
				# #Insert the data that we determined above into the ReportedModules Table in the licenseKey.db file
				# query = conn.execute("INSERT INTO ReportedModules (StoreCode, Module0, Module1, Module2, Module3, \
				# Module4, Module5, Module6, Module7, Module8, Module9, Module10, Module11, Module12, Module13, \
				# Module14, Module15, Module16, Module17, Module18, Module19, Module20, Module21, Module22, Module23, \
				# Module24, Module25, NumberOfClients, SerialNumber, Version, Location0Name, Location0Address, Location0Phone) \
				# VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (store_code, \
				# module0, module1, module2, module3, module4, module5, module6, module7, module8, module9, \
				# module10, module11, module12, module13, module14, module15, module16, module17, module18, \
				# module19, module20, module21, module22, module23, module24, module25, numberOfClients, serialNumber, \
				# version, location0Name, location0Address, location0Phone))
				
				# returnString = {'data':query.lastrowid}
				
				# #Before we do anything else, log the request and the result.
				# now = datetime.datetime.now()
				# requestType = 'SendModules'
				# query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, SerialNumber, RealIPAddress, RequestHeaders, RequestData) VALUES(?,?,?,?,?,?,?)", (now, requestType, store_code.upper(), serialNumber, real_IPAddress,str(request.headers),str(request.data.decode('utf-8'))  ))
						
				# return returnString
				
			# else:
				# now = datetime.datetime.now()
				# requestType = 'SendModules'
				# query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, SerialNumber, RealIPAddress, RequestHeaders, RequestData) VALUES(?,?,?,?,?,?,?)", (now, requestType, 'INVALID CONTENT TYPE', '', real_IPAddress,str(request.headers),str(request.data.decode('utf-8')) ))
				# return "ERROR: Invalid Content-Type"		
					
#URLs below
api.add_resource(GetItemInfo_Meta, '/grabber/api/v1.0/GetItemInfo/<string:store_code>/<string:upc>/<string:external_IPAddress>/<string:internal_IPAddress>')
api.add_resource(SendTransactionItems_Meta, '/grabber/api/v1.0/SendTransactionItems')

if __name__ == '__main__':
#	app.run()		
# Do the below for the app to run from external hosts (Dangerous)
	app.run(host='0.0.0.0')
