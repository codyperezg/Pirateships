import socket
import threading

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5555

rooms = {}  # Dictionary to store room info: room_name -> {'host_conn': conn, 'client_conn': conn, 'host_addr': addr} 
shutdown_flag = False

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    current_room = None
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            try:
                decoded_data = data.decode('utf-8')
            except UnicodeDecodeError as e:
                print(f"UnicodeDecodeError: {e}")
                print(f"Raw data received: {data}")
                # Optionally, you can close the connection or continue based on your needs
                break
            # Proceed with the decoded data
            command_parts = data.strip().split(' ')
            command = command_parts[0]
            params = command_parts[1:]

            if command == 'CREATE_ROOM':
                room_name = params[0]
                host_ip = addr[0]
                rooms[room_name] = {'host_conn': conn, 'client_conn': None, 'host_addr': addr}
                conn.sendall(f"ROOM_CREATED {room_name}".encode())
                current_room = room_name
                print(f"Room created: {room_name} by {host_ip}")
            
            elif command == 'LIST_ROOMS':
                room_list = ','.join(rooms.keys())
                conn.sendall(f"ROOM_LIST {room_list}".encode())
            
            elif command == 'JOIN_ROOM':
                room_name = params[0]
                if room_name in rooms:
                    if rooms[room_name]['client_conn'] is None:
                        rooms[room_name]['client_conn'] = conn  # Set client connection
                        conn.sendall(f"JOINED_ROOM {room_name}".encode())
                        current_room = room_name
                        print(f"Player from {addr[0]} joined room {room_name}")
                        # Inform host that the client has joined
                        host_conn = rooms[room_name]['host_conn']
                        host_conn.sendall(f"CLIENT_JOINED {addr[0]}".encode())
                    else:
                        conn.sendall("ERROR Room already has a client".encode())
                else:
                    conn.sendall("ERROR Room not found".encode())
            
            elif command == 'MESSAGE':
                # Forward message to the other player
                message = ' '.join(params)
                if current_room in rooms:
                    room = rooms[current_room]
                    if conn == room['host_conn']:
                        # Forward host's message to client
                        client_conn = room['client_conn']
                        if client_conn:
                            client_conn.sendall(f"MESSAGE_FROM_HOST {message}".encode())
                    elif conn == room['client_conn']:
                        # Forward client's message to host
                        host_conn = room['host_conn']
                        if host_conn:
                            host_conn.sendall(f"MESSAGE_FROM_CLIENT {message}".encode())
                else:
                    conn.sendall("ERROR Not in a room".encode())
            
            else:
                conn.sendall("ERROR Invalid command".encode())
    
    except ConnectionResetError:
        pass
    finally:
        # Cleanup when a player disconnects
        if current_room and current_room in rooms:
            room = rooms[current_room]
            if conn == room['host_conn']:
                print(f"Host disconnected from room {current_room}")
                # Notify client that the host disconnected
                if room['client_conn']:
                    room['client_conn'].sendall("HOST_DISCONNECTED".encode())
                del rooms[current_room]
            elif conn == room['client_conn']:
                print(f"Client disconnected from room {current_room}")
                # Notify host that the client disconnected
                if room['host_conn']:
                    room['host_conn'].sendall("CLIENT_DISCONNECTED".encode())
                room['client_conn'] = None
        conn.close()

def console_listener():
    global shutdown_flag
    while not shutdown_flag:
        command = input()
        if command.strip().lower() == 'shutdown':
            print("Shutdown command received. Shutting down server.")
            shutdown_flag = True
            break

def start_server():
    global shutdown_flag
    print("Server starting...")
    # Start the console listener in a separate thread
    threading.Thread(target=console_listener, daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0)  # Set a timeout for accept()
        print(f"Server listening on port {PORT}")
        while not shutdown_flag:
            try:
                conn, addr = s.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue  # Loop again to check shutdown_flag
        print("Server has been shut down.")

if __name__ == '__main__':
    start_server()
