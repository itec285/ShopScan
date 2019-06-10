echo
echo \##########TESTING GetItemInfo####################################
#curl -i http://localhost:5000/starplus/api/v1.0/storecodes
curl -i http://10.10.99.99:5000/grabber/api/v1.0/GetItemInfo/0001/005/216.123.248.66/10.10.99.99



echo \##########TESTING SendTransactionItems###########################
curl -H "Content-type: text/plain" -X POST http://10.10.99.99:5000/grabber/api/v1.0/SendTransactionItems -d "test01,05770001052,01234567890,44447777777,05770001052,005,010"


echo
echo \##########TESTING GetTransactionItems############################
#curl -i http://localhost:5000/starplus/api/v1.0/storecodes
curl -i http://10.10.99.99:5000/grabber/api/v1.0/GetTransactionItems/Test01/13/216.123.248.66/10.10.99.99


#Uncomment the below to test the live server
#curl -H "Content-type: text/plain" -X POST https://keys.auto-star.com/starplus/api/v1.0/sendmodules -d "test01,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,8,AAA1,8.2.7,Ivans Store,123 Main Street Medicine Hat AB,403-555-1234"
echo \##############################################################

#echo \##########TESTING ON NGINX######################################
#curl -i http://keys.auto-star.com/starplus/api/v1.0/getmodules/abcp01/24.244.1.123/10.10.1.1
#curl -i https://keys.auto-star.com/starplus/api/v1.0/getmodules/abcp01/24.244.1.123/10.10.1.1
