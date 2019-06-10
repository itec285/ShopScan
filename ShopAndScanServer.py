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

class GetTransactionItems_Meta(Resource):
#This returns products in an order, given a store code and OrderID.
	def get(self,store_code, OrderID, external_IPAddress, internal_IPAddress):
		
		real_IPAddress = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
		print ('\n\n\n-------------------\n New Request from: ' + real_IPAddress)
		
		print ('#######    GetTransactionItems Request - ' +  str(datetime.datetime.now()) + '    #######')
		
		#Connect to the databases
		conn = sqlite3.connect('ShopAndScan.db')
		logconn = sqlite3.connect('RequestLog.db')
		
		#Perform query and return row with that order's data
		#Note that the below is safe from SQL Injection attacks.  See https://www.athenic.net/posts/2017/Jan/21/preventing-sql-injection-in-python/
		query = conn.execute("SELECT * FROM OpenOrders WHERE RecordID = ? AND StoreCode =?", (OrderID, store_code.upper()))
		
		#Get the data in the results, and also get the column names which is the [0] result using the .description
		queryResult = (query.fetchone())
		
		#First, make sure that a valid row in the DB exists.
		if str(queryResult) == 'None':
			#Invalid store code, log the error and return 'Invalid Store Code'			
			print ('Error, supplied store_code ' + store_code.upper() + ' and OrderID ' + OrderID+ ' did not match any records')
			return ('ERROR:Invalid Store Code / OrderID')
		else:
			print ('Returned data for Order: ' + str(queryResult[2]) )
			
			
		#Before we query the request, log it
		now = datetime.datetime.now()
		requestType = 'GetTransactionItems'
		query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, Upc, ExternalIPAddress, InternalIPAddress, \
			RealIPAddress) VALUES(?,?,?,?,?,?,?)", (now, requestType, store_code.upper(), OrderID, external_IPAddress, internal_IPAddress, real_IPAddress))
				
		# Save (commit) the changes and close the DBs
		conn.commit()
		logconn.commit()
		conn.close()
		logconn.close()
		
		#Send an answer back.  
		return jsonify(str(queryResult[2]))

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
				item_list = contents[1:]
				print ('    [--Number of elements--] ' + str(len(contents)) + '    [--Store Code-]' + store_code + '    [--Item List-]' + str(item_list))
				
				#Insert the data that we determined above into the OpenOrders Table in the ShopAndScan.db file
				query = conn.execute("INSERT INTO OpenOrders (StoreCode, ItemList) VALUES(?,?)", (str(store_code.upper()), str(item_list)))
				
				#Get the rowid just added and write/close the database
				returnString = {'data':query.lastrowid}
				conn.commit()
				conn.close()
								
				#Before we do anything else, log the request and the result.
				now = datetime.datetime.now()
				requestType = 'SendTransactionItems'
				query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, UPC, RealIPAddress, RequestHeaders, RequestData) \
					VALUES(?,?,?,?,?,?,?)", (now, requestType, store_code.upper(), str(item_list), real_IPAddress,str(request.headers),str(request.data.decode('utf-8'))))
				logconn.commit()
				logconn.close()
				
				return returnString
				
			else:
				now = datetime.datetime.now()
				requestType = 'SendTransactionItems'
				query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, UPC, RealIPAddress, RequestHeaders, RequestData) \
					VALUES(?,?,?,?,?,?,?)", (now, requestType, store_code.upper(), str(item_list), real_IPAddress,str(request.headers),str(request.data.decode('utf-8'))))
				return "ERROR: Invalid Content-Type"		
				

				
#URLs below
api.add_resource(GetItemInfo_Meta, '/grabber/api/v1.0/GetItemInfo/<string:store_code>/<string:upc>/<string:external_IPAddress>/<string:internal_IPAddress>')
api.add_resource(SendTransactionItems_Meta, '/grabber/api/v1.0/SendTransactionItems')
api.add_resource(GetTransactionItems_Meta, '/grabber/api/v1.0/GetTransactionItems/<string:store_code>/<string:OrderID>/<string:external_IPAddress>/<string:internal_IPAddress>')

if __name__ == '__main__':
#	app.run()		
# Do the below for the app to run from external hosts (Dangerous)
	app.run(host='0.0.0.0')
