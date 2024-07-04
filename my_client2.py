import socket
import time
import threading

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HOST = '192.168.2.2'
PORT = 12345
message = '...'

print("Starting connection to server...")
try:
	client_socket.connect((HOST, PORT))
	print("Successfully connected to server!")
except Exception as e:
	print("Error while connecting to the server!")
	print(f"{e}")
try:
	while True:
		try:
			client_socket.send(message.encode())
			time.sleep(60)
		except:
			print("Error while sending message to server.")
			break

except Exception as e:
	print("Error encountered!")
	print(f"{e}")
	client_socket.close()
	
