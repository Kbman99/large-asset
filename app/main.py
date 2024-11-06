from fastapi import FastAPI
from fastapi.responses import StreamingResponse, PlainTextResponse
import os
import asyncio

app = FastAPI()

# Path to the large asset (adjust the file path as needed)
ASSET_PATH = "large_asset.txt"

async def generate_file_chunks(file_path, chunk_size=1024, delay=1):
    """
    A generator that reads the file in chunks and yields each chunk with a delay.
    - file_path: Path to the file to serve.
    - chunk_size: Size of each chunk in bytes (default is 1 KB).
    - delay: Delay (in seconds) between serving each chunk.
    """
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(chunk_size):
                await asyncio.sleep(delay)  # Introduce a delay before sending the next chunk
                yield chunk
    except Exception as e:
        print(f"Error reading file: {e}")

@app.get("/large_asset_chunked.txt")
async def get_large_asset_chunked(chunks: int = 1):
    """
    Endpoint to serve the file in chunks with a delay between each chunk.
    This simulates serving a file slowly (1 second per chunk).
    """
    if os.path.exists(ASSET_PATH):
        large_asset_size = os.path.getsize(ASSET_PATH)
        chunk_size = int(large_asset_size/chunks)
        # Create a streaming response with the generator that sends chunks
        return StreamingResponse(generate_file_chunks(ASSET_PATH, chunk_size=chunk_size, delay=1), headers={"content-type": "text", "cache-control": "max-age=3600"})
    else:
        return {"error": "File not found"}

@app.get("/large_asset.txt")
async def get_large_asset():
    """
    Endpoint to serve a plaintext response containing the large_asset.txt
    """
    if os.path.exists(ASSET_PATH):
        content = None
        with open(ASSET_PATH, 'rb') as file:
            content = file.read()
        return PlainTextResponse(content, headers={"content-type": "text", "cache-control": "max-age=3600"})
    else:
        return {"error": "File not found"}