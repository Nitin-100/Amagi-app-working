# Amagi-app-working
Run app.py 
and run testing.py to test app

It downloads the video from youtube url.
Create MP4 chunks of the video using ffmpeg command without transcoding and restating timestamps.
Those MP4 chunks then overlayed with a png image via transcoding FFMPEG command on 6 threads at a time.
Overlayed MP4 chunks are joined using FFMPEG concat without re-encoding them into a final output.mp4.
Then output.mp4 is convereted to ts packets and m3u8 is generated for it which can be played, I played it via http server python and VLC.
