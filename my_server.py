import socket
import threading
import time
import subprocess
import re
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from rtt_and_clients import clients, rtt_times

ping_lock = threading.Lock()

def perform_ping(clients, rtt_times):
    while True:
        try:
            with ping_lock:
                for client_address, client_socket in list(clients.items()):
                    try:
                        ping_cmd = ['ping', '-q', '-c', '10', client_address]
                        result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=20)
                        avg_time = parse_output(result.stdout)
                        rtt_times[client_address] = avg_time
                        rtt_values = list(rtt_times.values())
                        rtt_values = [value for value in rtt_values if value is not None]
                        rtt_values = np.array(rtt_values)
                        k = 1
                        kmeans = KMeans(n_clusters=k, random_state=0).fit(rtt_values.reshape(-1, 1))
                        cluster_centers=kmeans.cluster_centers_
                        labels=kmeans.labels_
                        
                        plt.figure(figsize=(8,6))
                        plt.scatter(rtt_values, np.zeros_like(rtt_values), c=labels, cmap='viridis', s=50)
                        plt.scatter(cluster_centers, np.zeros_like(cluster_centers), marker='x', color='blue', s=200, label='Cluster Centers')
                        plt.title('1D KMeans Clustering of RTT Times')
                        plt.xlabel('Average RTT(ms)')
                        plt.legend()
                        plt.grid(True)
                        plt.tight_layout()
                        plt.show()
                    except subprocess.CalledProcessError as e:
                        print(f"[*]Error running ping command for {client_address}: {e}")
                        rtt_times[client_address] = None
                    except subprocess.TimeoutExpired as e:
                        print(f"[*]Timeout occurred while pinging {client_address}! Exception: {e}")
                        rtt_times[client_address] = None
            time.sleep(15)  # Ping every 60 seconds
        except Exception as e:
            print(f"[*]Error in perform_ping: {e}")

def parse_output(ping_stdout):
    pattern = r"rtt min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) ms"
    match = re.search(pattern, ping_stdout)
    if match:
        avg = float(match.group(2))
        return avg
    else:
        return None

def handle_clients(client_socket, client_address):
    global clients, rtt_times

    with ping_lock:
        clients[client_address[0]] = client_socket
        print(f"[*] {client_address[0]} has joined. Number of clients = {len(clients)}")
        ping_thread = threading.Thread(target=perform_ping, args=(clients, rtt_times), daemon=True)
        ping_thread.start()
    try:
        while True:
            message = client_socket.recv(1024).decode()
            print(f"[*] Message from {client_address[0]}: {message}")
    except Exception as e:
        print(f"[*] Error encountered with client {client_address[0]}: {e}")
    finally:
        with ping_lock:
            del clients[client_address[0]]
            print(f"[*] {client_address[0]} has left. Number of clients = {len(clients)}")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = '0.0.0.0'
PORT = 12345

server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"[*] Server started and listening on {HOST}:{PORT}")



while True:
    try:
        client_socket, client_address = server_socket.accept()
        print(client_socket)
        print(client_address)
        print(f"[*] New connection from {client_address}")
        client_handler = threading.Thread(target=handle_clients, args=(client_socket, client_address))
        client_handler.start()
    except Exception as e:
        print(f"[*] Server has been stopped. Exiting... {e}")
        server_socket.close()
        break

