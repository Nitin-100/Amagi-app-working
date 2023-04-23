import os
import shutil
import uuid
import youtube_dl
from pytube import YouTube
import yt_dlp


class Downloader:
    def download(self, url, resolution):
        unique_id = str(uuid.uuid4())
        output_dir = f'videos\\{unique_id}'
        os.makedirs(output_dir, mode=0o777)
        os.chmod(output_dir, 0o777)

        file_path = None
        for _ in range(2):
            try:
                file_path = self.download_yt_dlp(url, resolution, output_dir)
                if file_path:
                    break
            except Exception as e:
                print(f"yt-dlp error: {e}")
                self.close_open_files(output_dir)
                shutil.rmtree(output_dir)

            try:
                file_path = self.download_youtube_dl(url, resolution, output_dir)
                if file_path:
                    break
            except Exception as e:
                print(f"youtube-dl error: {e}")
                self.close_open_files(output_dir)
                shutil.rmtree(output_dir)

            try:
                file_path = self.download_pytube(url, resolution, output_dir)
                if file_path:
                    break
            except Exception as e:
                print(f"pytube error: {e}")
                self.close_open_files(output_dir)
                shutil.rmtree(output_dir)

        if not file_path:
            self.close_open_files(output_dir)
            raise Exception("Failed to download video after multiple attempts")

        self.close_open_files(output_dir)
        return file_path

    def close_open_files(self, output_dir):
        # Get all open files in the directory
        open_files = []
        for dirpath, dirnames, filenames in os.walk(output_dir):
            for file in filenames:
                try:
                    open_files.append(open(os.path.join(dirpath, file), 'r'))
                except IOError:
                    pass

        # Close all open files
        for file in open_files:
            file.close()

    def download_youtube_dl(self, url, resolution, output_dir):
        ydl_opts = {
            'format': f'bestvideo[ext=mp4][height<={resolution}]+bestaudio[ext=m4a]/best[ext=mp4][height<={resolution}]',
            'outtmpl': f'{output_dir}/download_%(count)s.%(ext)s',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        video_path = os.path.join(output_dir, os.listdir(output_dir)[0])
        return video_path

    def download_pytube(self, url, resolution, output_dir):
        yt = YouTube(url)
        stream = yt.streams.filter(file_extension='mp4', res=resolution).first()
        file_path = stream.download(output_path=output_dir, filename=f'download_{unique_id}')

        return file_path

    def download_yt_dlp(self, url, resolution, output_dir):
        ydl_opts = {
            'format': f'bestvideo[ext=mp4][height<={resolution}]+bestaudio[ext=m4a]/best[ext=mp4][height<={resolution}]',
            'outtmpl': f'{output_dir}\\download_%(count)s.%(ext)s',
            'socket_timeout': 2,  # Increase the socket timeout
            'retries': 10,  # Increase the number of retries
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        video_path = os.path.join(output_dir, os.listdir(output_dir)[0])
        return video_path

    def get_video_duration(self, youtube_url):
        video_duration = None

        # Try to fetch video duration using yt_dlp
        try:
            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                video_duration = info['duration']
                return video_duration
        except Exception:
            pass

        # Try to fetch video duration using youtube_dl
        try:
            with youtube_dl.YoutubeDL() as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                video_duration = info['duration']
                return video_duration
        except Exception:
            pass

        # Try to fetch video duration using pytube
        try:
            yt = YouTube(youtube_url)
            video_duration = yt.length
            return video_duration
        except Exception:
            pass

        return None