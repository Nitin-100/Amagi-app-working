import os
import re
import subprocess


class HLS:
    def __init__(self):
        pass

    import os
    import subprocess

    def generate_hls_stream(self, overlayed_file):
        # Get the directory of the input file
        input_directory = os.path.dirname(overlayed_file)

        # Create the "ts" folder inside the input directory
        ts_directory = os.path.join(input_directory, 'ts')
        os.makedirs(ts_directory, exist_ok=True)

        # Set the output file path for the HLS playlist
        output_m3u8 = os.path.join(ts_directory, 'output.m3u8')

        # Construct the FFmpeg command to generate the HLS stream
        ffmpeg_command = [
            'ffmpeg', '-i', overlayed_file,
            '-codec:v', 'libx264', '-codec:a', 'aac',
            '-preset', 'fast', '-g', '48',
            '-hls_time', '8',
            '-hls_list_size', '0',
            '-f', 'hls',
            output_m3u8
        ]

        # Execute the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)

        # Return the path to the HLS playlist (M3U8 file)
        return output_m3u8


























