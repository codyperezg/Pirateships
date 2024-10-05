import socket
import threading

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5555

rooms = {}  # Dictionary to store room info: room_name -> {'host_ip': ip, 'port': port} 
shutdown_flag = False

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            command_parts = data.strip().split(' ')
            command = command_parts[0]
            params = command_parts[1:]

            if command == 'CREATE_ROOM':
                room_name = params[0]
                host_ip = addr[0]
                rooms[room_name] = {'host_ip': host_ip, 'port': addr[1]}
                conn.sendall(f"ROOM_CREATED {room_name}".encode())
                print(f"Room created: {room_name} by {host_ip}")
            elif command == 'LIST_ROOMS':
                room_list = ','.join(rooms.keys())
                conn.sendall(f"ROOM_LIST {room_list}".encode())
            elif command == 'GET_ROOM':
                room_name = params[0]
                if room_name in rooms:
                    host_ip = rooms[room_name]['host_ip']
                    host_port = rooms[room_name]['port']
                    conn.sendall(f"ROOM_INFO {host_ip} {host_port}".encode())
                else:
                    conn.sendall("ERROR Room not found".encode())
            elif command == 'UPDATE_ROOM_PORT':
                # Update the room's port number
                host_port = int(params[0])
                for room in rooms.values():
                    if room['host_ip'] == addr[0]:
                        room['port'] = host_port
                        print(f"Updated port for room hosted by {addr[0]} to {host_port}")
                        break
                conn.sendall("PORT_UPDATED".encode())
            else:
                conn.sendall("ERROR Invalid command".encode())
    except ConnectionResetError:
        pass
    finally:
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
