import asyncio
import os
import time

import websockets

n_conn = 500
total_bytes_sent_global = 0
throughputs = []

test_duration = 10  # in seconds
message = "x" * 1024  # 1 KB of data


client_done_counter = 0
all_clients_done_event = asyncio.Event()


async def send_data(websocket):
    start_time = time.time()
    total_bytes_sent = 0
    global total_bytes_sent_global
    global client_done_counter

    while time.time() - start_time < test_duration:
        await websocket.send(message)
        total_bytes_sent += len(message)
        await asyncio.sleep(
            0
        )  # Allow other tasks to run otherwise this behaves blocking

    client_done_counter += 1
    if client_done_counter == n_conn:
        all_clients_done_event.set()

    total_bytes_sent_global += total_bytes_sent
    await websocket.send("close")
    end_time = time.time()
    throughput = total_bytes_sent / (end_time - start_time)  # bytes per second
    throughputs.append(throughput)
    print(f"Throughput: {throughput / 1024 } KB/s")
    await websocket.close()


async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)


def print_stats():
    print("Total bytes sent: ", total_bytes_sent_global / 1024, "KB")
    print("Total throughput: ", total_bytes_sent_global / 1024 / test_duration, "KB/s")
    print(f"Average throughput: {sum(throughputs) / len(throughputs) / 1024} KB/s")
    print(
        "Average data sent: ",
        total_bytes_sent_global / 1024 / len(throughputs),
        "KB",
    )


async def start_server():
    server = await websockets.serve(send_data, "localhost", 8765)
    await all_clients_done_event.wait()
    server.close()
    await server.wait_closed()
    print_stats()


if __name__ == "__main__":
    # print process id
    print(f"Process ID: {os.getpid()}")
    asyncio.get_event_loop().run_until_complete(start_server())
