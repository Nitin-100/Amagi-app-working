import asyncio
import aiohttp
from aiohttp import ClientTimeout
async def send_request(session, url, resolution, image_path, chunk_duration):
    data = {
        'youtube_url': url,
        'resolution': resolution,
        'image_path': image_path,
        'chunk_duration': chunk_duration,
    }

    async with session.post('http://localhost:5000/process_request_multiprocess_endpoint', json=data) as response:
        print(await response.text())

async def main():
    youtube_urls = [
        'https://www.youtube.com/watch?v=tbnzAVRZ9Xc',
        'https://www.youtube.com/watch?v=1V11Eby8ESc',
        'https://www.youtube.com/watch?v=-ESQmzDbnL8',
        'https://www.youtube.com/watch?v=q8w1d01Y2vY',
    ]

    resolution = '720p'
    image_path = 'C:\\Users\\nchaudhary\\Desktop\\Amagi-YT-FFMPEG\\overlay.png'
    chunk_duration = 10

    timeout = ClientTimeout(total=10 * 80)  # Set the timeout to 10 minutes
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []
        for url in youtube_urls:
            task = asyncio.ensure_future(send_request(session, url, resolution, image_path, chunk_duration))
            tasks.append(task)
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
