from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse, FileResponse
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
    
@app.get("/large_asset_range.txt")
async def get_file(request: Request):
    file_path = ASSET_PATH
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Get Range header from the request, if present
    range_header = request.headers.get('Range', None)
    
    if range_header:
        # Parse Range header
        byte_range = range_header.strip().lower()
        if byte_range.startswith("bytes="):
            byte_range = byte_range[6:]
            start, end = byte_range.split("-")
            
            # If the start is missing, set it to the beginning of the file
            start = int(start) if start else 0
            
            # If the end is missing, set it to the end of the file
            end = int(end) if end else file_size - 1
            
            if start >= file_size:
                raise HTTPException(status_code=416, detail="Range Not Satisfiable")
            
            # Adjust the end byte to not exceed the file size
            end = min(end, file_size - 1)
            
            # Open the file and create a generator to yield the range
            def file_generator():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    yield f.read(end - start + 1)
            
            # Set status code to 206 (Partial Content)
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(end - start + 1),
                "Cache-Control": "max-age=3600",
            }
            return StreamingResponse(file_generator(), headers=headers, status_code=206)
    
    # If no Range header, return the full file
    return FileResponse(file_path)
