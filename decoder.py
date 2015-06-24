#BitTorrent Protocol
#Cristina Chu
#Samarth Paliwal

#----------Parse Torrent file to output metainfo {} ----------#
from bencode import *
from hashlib import sha1
import struct
import socket

torrentFile = "alibaba.torrent"
metainfo_file = open(str(torrentFile), 'rb')
metainfo = bdecode(metainfo_file.read())
info = metainfo['info']
torrentDir = info['name']
metainfo_file.close()
info_hash=sha1(bencode(metainfo['info'])).digest()

#Get IP address of Peers/Seeders from File (ideally Tracker)

#If there is a text file with lines: peer IP, peer port
def getPeers(filename):
	f = open(filename, 'r')
	peers = []
	for x in f.readlines():
		x = x.split(",")
		peers.append(x[0],x[1])

	f.close()
	return peers

#using only 1 peer
peerIp='127.0.0.1'
peerPort=62348 #TODO: CHECK this from bittorent
self_ID="-BOWAOC-YYYYYYYYYYYY"

#----------Bind Sockets to Torrent Client----------#
host = peerIp
port = peerPort
recv_size = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #tcp socket 
s.connect((host,port))#connect

#----------Initiating handshake----------#
pstrlen = 19
pstr = "BitTorrent protocol"
send_packet = (chr(pstrlen) + pstr + 8*chr(0) + info_hash + self_ID)

s.send(send_packet) 
handshake_response = s.recv(recv_size)

hs_pstr = handshake_response[0:20]
hs_hash = handshake_response[28:48]

while hs_hash!=info_hash and hs_pstr!=pstr:
	s.send(send_packet) 
	handshake_response = s.recv(recv_size)

	hs_pstr = handshake_response[0:20]
	hs_hash = handshake_response[28:48]

#-------------------------------------------------------------#
#-------------------------------------------------------------#
#print 'handshake_response: ', handshake_response
#print 
#print "pstr: " + handshake_response[0:20]
#print
#print "info_hash: "+info_hash
#print "handshake: "+handshake_response[28:48]
#print 
#print "End of handshake_response"
#print "---------"
#-------------------------------------------------------------#
#-------------------------------------------------------------#

def parseMessage(message):
	i = message[0]
	while i<len(message):
		length = message[0:4]

		if length == 1:
			return "choke"

#-------Showing interest and receiving unchoke----------#
send_packet1=struct.pack('!IB', 1, 2)
s.send(send_packet1)
interest_response = s.recv(recv_size)
interest_unpacked = struct.unpack('!IB', interest_response[0:5])

while interest_unpacked != (1,1):
	s.send(send_packet1)
	interest_response = s.recv(recv_size)
	interest_unpacked = struct.unpack('!IB', interest_response[0:5])

#print 'Show interest & receive unchoke:', struct.unpack('!IB', interest_response[0:5])
#print (struct.unpack('!IB', interest_response[0:5]) == (1,1)) 		#print True if message is unchoke
#print len(interest_response)
#print "End of interest/unchoke"
#print "----------"

#------Requesting Packets------#
file_len = metainfo['info']['length']
piece_len = metainfo['info']['piece length']
num_pieces = file_len//piece_len
leftovers = file_len%piece_len

#creating dictionary that will contain all the pieces as they come in
fileDict = {}
for i in range(num_pieces):
	fileDict[i] = {}

if leftovers != 0:
	fileDict[num_pieces] = {}
	num_pieces=num_pieces+1

#variables to keep track of progress
count_pieces = 0	#counter of pieces that have arrived
index1 = 0 	#piece that it is being asked
index2 = 0 	#block in the piece
bytesLeft = piece_len 	#bytes that are left to get
piece_complete = ""

while count_pieces != num_pieces-1: 		#while you dont have all the pieces of the file
	send_packet=struct.pack('!IBIII', 13, 6, index1, index2, 16384)
	s.send(send_packet)
	request_response = s.recv(16397)

	#check it is a piece packet
	received = struct.unpack('!IBII', request_response[0:13])
	if received[1] == 7:		
		#put it in correct place in dictionary
		fileDict[received[2]][received[3]] = request_response[13:]		#add the block receive to the dictionary
		index2 += 1
		bytesLeft -= len(request_response[13:])
		print "bytesleft",bytesLeft
		
	if bytesLeft == 0:
		#combine all the blocks for the piece
		for x in fileDict[index1]:
			piece_complete += fileDict[index1][x]

		#check match on hash
		p = (index1+1)*20
		print "piece",len(piece_complete)
		hash1 = sha1((struct.unpack('20s', metainfo['info']['pieces'][0:20]))[0])#[p-20:p]))[0])
		hash2 = sha1(piece_complete)

		print hash1
		print hash2

		if hash1 == hash2:
			print "correct"
			index1 += 1
			index2 = 0
			bytesLeft = piece_len
		else:
			fileDict[index1] = {}
			index2 = 0
			bytesLeft = piece_len

#getting the final piece
send_packet=struct.pack('!IBIII', 13, 6, index1, index2, leftovers)
s.send(send_packet)
request_response = s.recv(leftovers+13)

fileDict[index1][index2]

#---------Combine all the info and write it to a file------------#
f = open("alibabaText.txt", "w")

for i in fileDict:
	for y in fileDict[i]: 
		f.write(fileDict[i][y])

f.close()



print metainfo

	#TODO: verify is the correct thing

s.close()

#-------------------------------------------------------------#
#-------------------------------------------------------------#
#print metainfo['info']['piece length']

#send_packet=struct.pack('!IBIII', 13, 6, 0, 0, 131)
#s.send(send_packet)
#request_response = s.recv(144)

#print len(request_response)
#print "HERE:" + request_response

#print 'Received:', struct.unpack('!IBIII', request_response[0:17])
##block_bytes += struct.unpack('!131s', request_response[13:])
#print "--------"

#block = struct.unpack('131s', request_response[13:])[0]
#print block

#print "info"
#print metainfo

##Check if correct piece
#hash1 = sha1((struct.unpack('20s', metainfo['info']['pieces'][0:20]))[0])
#hash2 = sha1(block)

#print hash1 
#print hash2

#-------------------------------------------------------------#
#-------------------------------------------------------------#





