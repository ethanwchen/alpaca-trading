import socket
import json


# Server details (must match the server's settings)
HOST = "127.0.0.1"  # Localhost
PORT = 9995         # Port of the running finance server


def connect_to_server():
    """Connect to the TCP server and receive streaming data."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))


    print(f"Connected to server at {HOST}:{PORT}")

    while True:
        try:
            # Receive data from the server
            data = client.recv(1024).decode()

            if not data:
                break  # Stop if server disconnects
           
            # Parse the received JSON data
            try:
                stock_data = json.loads(data.strip())
                print("Received Data:", stock_data)

            except json.JSONDecodeError as e:
                print("Error parsing JSON:", e)

        except Exception as e:
            print("Error:", e)
            break

    client.close()

def send_order(order, host="127.0.0.1", port=9999):
    """
    Connect to the trading system at (host, port) and send a trade order in JSON format.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            order_message = json.dumps(order)
            sock.sendall(order_message.encode("utf-8"))
            print("Order sent:", order_message)
            # Optional: read the response
            response = sock.recv(1024).decode("utf-8")
            print("Received response:", response)
    except Exception as e:
        print("Error sending order:", e)

if __name__ == "__main__":
    connect_to_server()

