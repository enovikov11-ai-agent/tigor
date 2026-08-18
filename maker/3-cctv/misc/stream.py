# libcamera-vid -t 0 --codec yuv420 --width 1920 --height 1080 --framerate 30 --inline --output - 2>/dev/null | ffmpeg -f rawvideo -pix_fmt yuv420p -s 1920x1080 -i - -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='%{gmtime\\:%Y-%m-%d %H-%M-%S UTC+0}':x=30:y=30:fontsize=60:fontcolor=white:borderw=5:bordercolor=black" -c:v h264_v4l2m2m -g 10 -b:v 4M -f mpegts - 2>/dev/null | python stream.py

import websockets, asyncio, logging, sys
from dataclasses import dataclass

# Queue size about 10 seconds (5 MB) before dropping peer
WS_HOST, WS_PORT = "0.0.0.0", 3321
WS_MAX_PEERS, WS_QUEUE_SIZE, WS_TIMEOUT = 3, 4000, 10

# Maximum we can send without fragmentation, typical MTU is 1500 bytes
MPEG_TS_PACKET_SIZE = 188
BATCH_SIZE = 7 * MPEG_TS_PACKET_SIZE


peers, peers_lock = {}, asyncio.Lock()
logging.basicConfig(level=logging.INFO)


@dataclass
class Peer:
    queue: asyncio.Queue
    task: asyncio.Task
    ws: websockets.ClientProtocol


async def peer_handler(peer: Peer):
    try:
        while True:
            packet = await asyncio.wait_for(peer.queue.get(), timeout=WS_TIMEOUT)
            await peer.ws.send(packet)
    except asyncio.TimeoutError:
        logging.info("Getting info for peer timed out")
    except websockets.ConnectionClosed:
        logging.info("Peer disconnected")
    except asyncio.CancelledError:
        logging.info("Peer ordered to drop")
    except Exception as e:
        logging.error(f"Error with peer: {e}")
    finally:
        async with peers_lock:
            peers.pop(peer.ws, None)
        await peer.ws.close()


async def accept_peer(ws_peer):
    async with peers_lock:
        if len(peers) < WS_MAX_PEERS:
            peer = Peer(queue=asyncio.Queue(maxsize=WS_QUEUE_SIZE), task=None, ws=ws_peer)
            peer.task = asyncio.create_task(peer_handler(peer))
            peers[ws_peer] = peer
        else:
            peer = None

    if peer:
        await peer.task
        return

    logging.warning("Max peers reached")
    await ws_peer.close()


def is_valid_mpeg_ts_batch(batch):
    return len(batch) == BATCH_SIZE and all(batch[i] == 0x47 for i in range(0, len(batch), MPEG_TS_PACKET_SIZE))


async def main():
    async with websockets.serve(accept_peer, WS_HOST, WS_PORT):
        logging.info(f"Server started on ws://{WS_HOST}:{WS_PORT}")

        loop = asyncio.get_running_loop()
        while True:
            try:
                batch = await loop.run_in_executor(None, sys.stdin.buffer.read, BATCH_SIZE)

                if not batch:
                    logging.error("Stream ended, exiting")
                    break

                if not is_valid_mpeg_ts_batch(batch):
                    logging.warning("Invalid MPEG-TS batch")
                    continue

                async with peers_lock:
                    for peer in peers.values():
                        try:
                            peer.queue.put_nowait(batch)
                        except asyncio.QueueFull:
                            logging.debug("Peer queue full, dropping peer")
                            peer.task.cancel()

            except Exception as e:
                logging.error(f"Main loop error: {e}")
                await asyncio.sleep(1)


asyncio.run(main())
