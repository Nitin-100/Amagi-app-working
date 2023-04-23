import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

import ffmpeg


class Chunker:
    def __init__(self):
        pass

    def process_chunks(self, video_path, image_path, chunk_duration):
        video_duration = float(ffmpeg.probe(video_path)['format']['duration'])
        chunks_count = int(video_duration // chunk_duration)

        for i in range(chunks_count):
            output_path = os.path.join(os.path.dirname(video_path), f'chunks/chunk_{i}.mp4')
            start = i * chunk_duration
            end = (i + 1) * chunk_duration if i != chunks_count - 1 else video_duration

            self.create_chunk(video_path, image_path, start, end, output_path)

    def create_chunk(self, video_path, image_path, start, end, output_path):
        overlay_height = 96
        overlay_width = 576

        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), mode=0o755)
            os.chmod(output_path, 0o755)

        input_video = ffmpeg.input(video_path)
        input_image = ffmpeg.input(image_path)

        filter_complex = f"[1:v]scale={overlay_width}:{overlay_height}[ov];[0:v][ov]overlay=(W-{overlay_width})/2:H-h-{overlay_height}"

        output = ffmpeg.output(input_video, input_image, filter_complex=filter_complex,
                               vcodec='libx264', preset='fast', b='2000k',
                               **{'s': '1280x720'}, t=end - start, filename=output_path)

        output.run()

    # Issue with intel uhd gpu so no hardware acceleration used
    def overlay_chunk(self, chunk_file, chunks_directory, overlay_chunks_directory, image_path, overlay_width,
                      overlay_height, resolution):
        command2 = f'ffmpeg -i {os.path.join(chunks_directory, chunk_file)} -i "{image_path}" -filter_complex "[1:v]scale={overlay_width}:{overlay_height}[ov];[0:v][ov]overlay=(W-{overlay_width})/2:H-h-{overlay_height},format=yuv420p[v]" -map "[v]" -map 0:a -c:v libx264 -c:a copy -preset veryfast -crf 22 -movflags +faststart -s {resolution} {os.path.join(overlay_chunks_directory, f"overlay_{chunk_file}")}'
        subprocess.call(command2, shell=True)

    def process_chunks_onego(self, video_path, image_path, chunk_duration, resolution):
        print("^^^^^^^^^^^^^")
        overlay_height = 96
        overlay_width = 576
        if resolution == '720p':
            resolution = '1280x720'
        video_directory = os.path.dirname(video_path)
        chunks_directory = os.path.join(video_directory, 'chunks')
        overlay_chunks_directory = os.path.join(chunks_directory, 'overlayed_output')
        if not os.path.exists(chunks_directory):
            os.makedirs(chunks_directory, mode=0o755)
            os.chmod(chunks_directory, 0o777)

        if not os.path.exists(overlay_chunks_directory):
            os.makedirs(overlay_chunks_directory, mode=0o755)
            os.chmod(overlay_chunks_directory, 0o777)

        print(video_directory)
        print(chunks_directory)
        print(overlay_chunks_directory)

        # Command to split the video into chunks
        command1 = f'ffmpeg -hwaccel auto -i "{video_path}" -c copy -map 0 -f segment -segment_time {chunk_duration} -reset_timestamps 1 {os.path.join(chunks_directory, "chunk%03d_output.mp4")}'
        subprocess.call(command1, shell=True)
        print("YYYYYYYY")

        # Extract chunk file names from the output of command1
        files = os.listdir(chunks_directory)

        # Filter out chunk files based on filename format
        chunk_files = [file for file in files if re.match(r'chunk\d+_output\.mp4', file)]

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    self.overlay_chunk, chunk_file, chunks_directory, overlay_chunks_directory, image_path,
                    overlay_width,
                    overlay_height, resolution
                )
                for chunk_file in chunk_files
            ]

            for future in futures:
                future.result()
        return overlay_chunks_directory

    def join_chunks_withoutTranscoding(self, chunks_directory):
        # Get a list of all files in the directory
        files = os.listdir(chunks_directory)

        # Filter the video chunk files and sort them by their numeric part
        chunk_files = sorted([f for f in files if f.startswith('overlay_chunk') and f.endswith('_output.mp4')])

        # Create the concat_list.txt file
        with open(os.path.join(chunks_directory, 'concat_list.txt'), 'w') as concat_list:
            for chunk_file in chunk_files:
                concat_list.write(f"file '{chunk_file}'\n")
        output_file = os.path.join(chunks_directory, 'output.mp4')
        concat_list_path = os.path.join(chunks_directory, 'concat_list.txt')
        command = f'ffmpeg -f concat -safe 0 -i {concat_list_path} -c copy {output_file}'
        subprocess.run(command, check=True)

        return output_file

    def join_chunks_withTranscoding(self, chunks_directory):
        # Extract chunk file names from the output of command1
        files = os.listdir(chunks_directory)

        transcoded_directory = os.path.join(chunks_directory, 'transcoded_directory')
        if not os.path.exists(transcoded_directory):
            os.makedirs(transcoded_directory, mode=0o755)
            os.chmod(transcoded_directory, 0o777)

        # Filter out chunk files based on filename format
        chunk_files = sorted([file for file in files if re.match(r'overlay_chunk\d+_output\.mp4', file)])

        # Get the encoding parameters of the first chunk
        first_chunk_path = os.path.join(chunks_directory, chunk_files[0])
        first_chunk_info_command = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height,avg_frame_rate -of csv=p=0 "{first_chunk_path}"'
        first_chunk_info_output = subprocess.check_output(first_chunk_info_command, shell=True, text=True).strip()
        width, height, avg_frame_rate = first_chunk_info_output.split(',')

        # Transcode each chunk to match the encoding parameters of the first chunk
        transcoded_chunk_files = []
        for chunk_file in chunk_files:
            input_file = os.path.join(chunks_directory, chunk_file)
            output_file = os.path.join(transcoded_directory, f'transcoded_{chunk_file}')
            transcoding_command = f'ffmpeg -i "{input_file}" -c:v libx264 -preset veryfast -crf 22 -vf "scale={width}:{height},setpts=PTS-STARTPTS" -c:a copy "{output_file}"'
            subprocess.run(transcoding_command, check=True, shell=True)
            transcoded_chunk_files.append(output_file)

        # Concatenate the transcoded .mp4 files without further transcoding
        output_file = os.path.join(chunks_directory, 'Final_out.mp4')
        concat_files = '|'.join(transcoded_chunk_files)

        # Get the number of audio streams in the concatenated file
        ffprobe_command = f'ffprobe -v error -show_entries stream=codec_type -of default=noprint_wrappers=1:nokey=1 "concat:{concat_files}"'
        ffprobe_output = subprocess.check_output(ffprobe_command, shell=True, text=True).strip()
        num_audio_streams = len([s for s in ffprobe_output.split('\n') if s.strip() == 'audio'])

        # Mix the audio streams if there is more than one
        if num_audio_streams > 1:
            audio_mix_filter = f'[0:a]'
            for i in range(1, num_audio_streams):
                audio_mix_filter += f'[a{i}]'
            audio_mix_filter += f'amix=inputs={num_audio_streams}:dropout_transition=2[aout]'
            map_command = '-map "[vout1]" -map "[aout]"'
        else:
            audio_mix_filter = ''
            map_command = '-map 0:v -map 0:a'

        # Build the filtergraph for the concatenation
        filtergraph = ''
        for i in range(len(transcoded_chunk_files)):
            filtergraph += f'[{i}:v][{i}:a]'
        filtergraph += f'concat=n={len(transcoded_chunk_files)}:v=1:a=1[vout][outa];[vout]setpts=PTS-STARTPTS[vout1];[outa]aresample=async=1[outa1]{audio_mix_filter}'

        command = f'ffmpeg -i "concat:{concat_files}" -filter_complex "{filtergraph}" {map_command}'
        subprocess.run(command, check=True, shell=True)
        return output_file
