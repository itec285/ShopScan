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
		
		#Perform query and return row with that store and items base data
		#Note that the below is safe from SQL Injection attacks.  See https://www.athenic.net/posts/2017/Jan/21/preventing-sql-injection-in-python/
		query = conn.execute("SELECT RecordID, StoreCode, Upc, Fineline, LinkedItem, ReportDescription,	PosDescription,	ProductActive, \
			PriceMethod, RegularRetail, BreakQty, SpecialPrice FROM Products WHERE UPC = ? AND StoreCode =?", (upc, store_code.upper()))
				
		#Get the data in the results, and also get the column names which is the [0] result using the .description
		queryResult = (query.fetchone())
		
		#First, make sure that a valid row in the DB exists.
		if str(queryResult) == 'None':
			#Invalid store code, log the error and return 'Invalid Store Code'			
			print ('Error, supplied store_code ' + store_code.upper() + ' and UPC ' + upc+ ' did not match any records')
			return ('ERROR:Invalid Store Code or item')
		else:
			print ('Returned base data for UPC ' + str(queryResult[2]) )
			columns = [desc[0] for desc in query.description]
			# Since we have at least one result, make a dictionary format answer of column name and resulting values
			# e.g. 'RecordID': 4, 'StoreCode': '0001', 'Upc': '005', 'Fineline': 'DEPOSIT'
			# See https://stackoverflow.com/questions/12270679/how-to-use-column-names-when-creating-json-object-python for information on this.
			answer1 = dict(zip(columns, queryResult))
		
		#Perform query and return row with that store and items tax data
		#Note that the below is safe from SQL Injection attacks.  See https://www.athenic.net/posts/2017/Jan/21/preventing-sql-injection-in-python/
		query = conn.execute("SELECT Tax1Status, Tax1Rate, Tax2Status, Tax2Rate, Tax3Status, Tax3Rate, Tax4Status, Tax4Rate, Tax5Status, Tax5Rate, \
			Tax6Status, Tax6Rate, Tax7Status, Tax7Rate, Tax8Status, Tax8Rate, Tax9Status, Tax9Rate, Tax10Status, Tax10Rate, Tax11Status, Tax11Rate, \
			Tax12Status, Tax12Rate, Tax13Status, Tax13Rate, Tax14Status, Tax14Rate, Tax15Status, Tax15Rate, Tax16Status, Tax16Rate, Tax17Status, Tax17Rate, \
			Tax18Status, Tax18Rate, Tax19Status, Tax19Rate, Tax20Status, Tax20Rate, Tax21Status, Tax21Rate, Tax22Status, Tax22Rate, Tax23Status, Tax23Rate, \
			Tax24Status, Tax24Rate, Tax25Status, Tax25Rate, Tax26Status, Tax26Rate, Tax27Status, Tax27Rate, Tax28Status, Tax28Rate, Tax29Status, Tax29Rate, \
			Tax30Status, Tax30Rate, Tax31Status, Tax31Rate, Tax32Status, Tax32Rate, Tax33Status, Tax33Rate, Tax34Status, Tax34Rate, Tax35Status, Tax35Rate, \
			Tax36Status, Tax36Rate, Tax37Status, Tax37Rate, Tax38Status, Tax38Rate, Tax39Status, Tax39Rate, Tax40Status, Tax40Rate \
			FROM Products WHERE UPC = ? AND StoreCode =?", (upc, store_code.upper()))
				
		#Get the data in the results, and also get the column names which is the [0] result using the .description
		queryResult = (query.fetchone())
		
		#First, make sure that a valid row in the DB exists.
		if str(queryResult) == 'None':
			#Invalid store code, log the error and return 'Invalid Store Code'			
			print ('Error, supplied store_code ' + store_code.upper() + ' and UPC ' + upc+ ' did not match any records')
			return ('ERROR:Invalid Store Code or item')
		else:
			print ('Returned tax data for UPC ' + upc )
			columns = [desc[0] for desc in query.description]
			# Since we have at least one result, make a dictionary format answer of column name and resulting values
			# e.g. 'RecordID': 4, 'StoreCode': '0001', 'Upc': '005', 'Fineline': 'DEPOSIT'
			# See https://stackoverflow.com/questions/12270679/how-to-use-column-names-when-creating-json-object-python for information on this.
			answer2 = dict(zip(columns, queryResult))
					
			#Iterate through the answer2 and create a new nested dictionary in the format Matt B. likes it.
			#
			# Taxes
			#	|
			#	----0
			#		|- Status: True
			#		|- Rate: 5.00
			#	----1
			#		|- Status: False
			#		|- Rate: 
			#	...and so on..
			
			#Initialize the taxes dictionary
			taxes = {}
			
			#For each line in answers 2, add to a sub-dictionary
			for k, v in answer2.items():
				#print (k,v)
				
				#Get about the number for this item. e.g. Tax40status becomes 40, tax2status becomes 2.
				number = ''.join(x for x in k if x.isdigit())
								
				#initialize the dictionary for this number *if* it doesn't already exist
				if not number in taxes: 
					taxes[number] = {}
				
				#Add the status or rate depending on which this is
				if "Status" in k:
					taxes[number]['status'] = v
					#print (taxes[number])
				elif "Rate" in k:
					taxes[number]['rate'] = v
					#print (taxes[number])
				else:
					print ("Error - neither status nor rate")
			
		#Add the taxes dictionary (including all sub-dictionaries) to the answer1.  This will have the key taxes and the values of the "taxes" dictionary, thus creating 
		# a multi level dictionary like the one shown above
		answer1.update( {'taxes' : taxes} )
		
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
		
		#Send an answer back.  Note that there's a lot of ways to do this below.  I worked with Matt in it was preferable for him to use JSON. 
		return jsonify(answer1)

		
class CheckValidStore_Meta(Resource):
#This returns confirms if a store code is valid, returning either true or false.
	def get(self,store_code, external_IPAddress, internal_IPAddress):
		
		real_IPAddress = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
		print ('\n\n\n-------------------\n New Request from: ' + real_IPAddress)
		
		print ('#######    New CheckValidStore request - ' +  str(datetime.datetime.now()) + '    #######')
		
		#Connect to the databases
		conn = sqlite3.connect('ShopAndScan.db')
		logconn = sqlite3.connect('RequestLog.db')
		
		#Before we query the request, log it
		now = datetime.datetime.now()
		requestType = 'CheckValidStore'
		query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, ExternalIPAddress, InternalIPAddress, \
			RealIPAddress) VALUES(?,?,?,?,?,?)", (now, requestType, store_code.upper(), external_IPAddress, internal_IPAddress, real_IPAddress))
				
		#Perform query to check for a valid store
		#Note that the below is safe from SQL Injection attacks.  See https://www.athenic.net/posts/2017/Jan/21/preventing-sql-injection-in-python/
		query = conn.execute("SELECT * FROM Stores WHERE StoreCode = ?", ([store_code.upper()]))
		
		#Get the data in the results, and also get the column names which is the [0] result using the .description
		queryResult = (query.fetchone())
	
		# Save (commit) the changes and close the DBs
		conn.commit()
		logconn.commit()
		conn.close()
		logconn.close()
			
		#Vary answer based on if a valid row in the DB exists.
		if str(queryResult) == 'None':
			#Invalid store code, log the error and return 'Invalid Store Code'			
			print ('Error, supplied store_code ' + store_code.upper() + ' did not match any records')
			return ('False')
		else:
			print ('Returned data for UPC ' + str(queryResult) )
			return ('True')
			

	
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
			print ('-------------------\n New SendTransactionItems Request from: ' + real_IPAddress)	
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
								
				#Before we do anything else, log the request.
				now = datetime.datetime.now()
				requestType = 'SendTransactionItems'
				query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, UPC, RealIPAddress, RequestHeaders, RequestData) \
					VALUES(?,?,?,?,?,?,?)", (now, requestType, store_code.upper(), str(item_list), real_IPAddress,str(request.headers),str(request.data.decode('utf-8'))))
				logconn.commit()
				logconn.close()
				
				print ('------------------- END of SendTransactionItems Request from: ' + real_IPAddress + '\n\n')	
				
				return returnString
				
			else:
				print ('------------------- Error SendTransactionItems Request from: ' + real_IPAddress + ' was invalid.\n\n')	
				now = datetime.datetime.now()
				requestType = 'SendTransactionItems'
				query = logconn.execute("INSERT INTO RequestLog(DateTime, RequestType, StoreCode, UPC, RealIPAddress, RequestHeaders, RequestData) \
					VALUES(?,?,?,?,?,?,?)", (now, requestType, store_code.upper(), str(item_list), real_IPAddress,str(request.headers),str(request.data.decode('utf-8'))))
				return "ERROR: Invalid Content-Type"		
				

				
#URLs below
api.add_resource(GetItemInfo_Meta, '/grabber/api/v1.0/GetItemInfo/<string:store_code>/<string:upc>/<string:external_IPAddress>/<string:internal_IPAddress>')
api.add_resource(CheckValidStore_Meta, '/grabber/api/v1.0/CheckValidStore/<string:store_code>/<string:external_IPAddress>/<string:internal_IPAddress>')
api.add_resource(SendTransactionItems_Meta, '/grabber/api/v1.0/SendTransactionItems')
api.add_resource(GetTransactionItems_Meta, '/grabber/api/v1.0/GetTransactionItems/<string:store_code>/<string:OrderID>/<string:external_IPAddress>/<string:internal_IPAddress>')

if __name__ == '__main__':
#	app.run()		
# Do the below for the app to run from external hosts (Dangerous)
	app.run(host='0.0.0.0')
