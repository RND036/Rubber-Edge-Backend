import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/ws/core/"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")
            
            # Receive welcome message
            message = await websocket.recv()
            print(f"Received: {message}")
            
            # Send ping
            await websocket.send(json.dumps({"action": "ping"}))
            print("Sent: ping")
            
            # Receive pong
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")

asyncio.run(test())
