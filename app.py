import time
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Lock

import ffmpeg
from flask import Flask, request, jsonify
from YT_Download_Services.download_yt import Downloader
from FFMpeg_Services.chunk_service import Chunker
from HLS_Service.HLS import HLS

app = Flask(__name__)
processing_queue = Queue()
processing_queue_lock = Lock()
thread_pool = ThreadPoolExecutor(max_workers=5)


@app.route('/process_singlethreaded', methods=['POST'])
def process_request_singlethreaded():
    data = request.get_json()
    youtube_url = data['youtube_url']
    resolution = data['resolution']
    image_path = data['image_path']
    chunk_duration = data['chunk_duration']


    # Download video and create chunks in the same thread
    downloader = Downloader()
    start_time = time.time()
    video_path = downloader.download(youtube_url, resolution)
    end_time = time.time()
    print(f"Video download time: {end_time - start_time} seconds")

    # Set chunk duration, by default it is 10 secs
    video_duration = downloader.get_video_duration(youtube_url)
    if video_duration <= 200:
        chunk_duration = 10
    elif 200 < video_duration <= 400:
        chunk_duration = 20
    elif 400 < video_duration <= 800:
        chunk_duration = 40
    else:
        chunk_duration = 60

    if video_path:
        # Create chunks and overlay image
        chunker = Chunker()
        start_time = time.time()
        print(video_path)
        overlay_chunks_directory = chunker.process_chunks_onego(video_path, image_path, chunk_duration, resolution)
        end_time = time.time()
        print(f"Chunking process time: {end_time - start_time} seconds")

        start_time = time.time()
        overlayed_file = chunker.join_chunks_withoutTranscoding(overlay_chunks_directory)
        end_time = time.time()
        print(f"Final overlayed output creation process time: {end_time - start_time} seconds")

        hlsgenerator = HLS()
        start_time = time.time()
        hls_stream_url = hlsgenerator.generate_hls_stream(overlayed_file)
        end_time = time.time()
        print(f"Final overlayed output creation process time: {end_time - start_time} seconds")


    return jsonify({'status': 'processing', 'output_url': hls_stream_url}), 202


@app.route('/process', methods=['POST'])
def process_request_threaded():
    data = request.get_json()
    youtube_url = data['youtube_url']
    resolution = data['resolution']
    image_path = data['image_path']
    chunk_duration = data['chunk_duration']

    # Initiate video download in separate thread
    downloader_thread = Thread(target=download_video, args=(youtube_url, resolution, image_path, chunk_duration))
    downloader_thread.start()

    return jsonify({'status': 'processing'}), 202


def download_video(youtube_url, resolution, image_path, chunk_duration):
    # Download video
    downloader = Downloader()
    start_time = time.time()
    video_path = downloader.download(youtube_url, resolution)
    end_time = time.time()
    print(f"Video download time: {end_time - start_time} seconds")
    '''
    # Create chunks and overlay image and create final overlayed output as well.
    chunker = Chunker()
    start_time = time.time()
    overlay_chunks_directory = chunker.process_chunks(video_path, image_path, chunk_duration)
    end_time = time.time()
    print(f"Chunking process time: {end_time - start_time} seconds")
    
    '''
    if video_path:
        # Add video path, image path, and chunk duration to processing queue
        with processing_queue_lock:
            processing_queue.put({'video_path': video_path, 'image_path': image_path, 'chunk_duration': chunk_duration})

        # Submit chunk processing to thread pool
        thread_pool.submit(perform_chunking)
        '''


def perform_chunking():
    while True:
        # Get video path, image path, and chunk duration from processing queue
        with processing_queue_lock:
            if not processing_queue.empty():
                job = processing_queue.get()
                video_path = job['video_path']
                image_path = job['image_path']
                chunk_duration = job['chunk_duration']
            else:
                # If queue is empty, exit the loop
                break

        # Create chunks and overlay image
        chunker = Chunker()
        start_time = time.time()
        chunker.process_chunks(video_path, image_path, chunk_duration)
        end_time = time.time()
        print(f"Chunking process time: {end_time - start_time} seconds")

    '''
if __name__ == '__main__':
    app.run()
