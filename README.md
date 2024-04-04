Problem Statement:
Design and develop Overlay stitching pipeline with FFMPEG and Gstreamer, which will break
the problem into smaller chunks to overall reduce the time of Stitching an overlay ad.
Let’s assume if a 20 second video to stitch an overlay for entire 20 second takes 6 seconds, we
want to parallelize the transcoding activity into 6 or more transcoder which can break the video
into smaller chunks and stitch individually and than later Merge the stitched video back to 20
second Video.
Overall the goal is to parallelize the transcoding required for Overlay ad stitching by breaking
the larger video into smaller chunks and reducing the time required.

Develop this for any 720p and or 1080p video from youtube. The overlay creative can be
picked up from anywhere on the internet. Maintain the height of overlay to be 96p.
Make the solution available as an API.
Develop an Python REST API, that will take youtube URL or any other URL as input along with
locally available Overlay creative on the system. Video should be 1080p or 720 P and minimum
20 second worth of video.
The output/response of api can be an HLS stream - URL from GSTreamer or FFMPEG, which
can be directly opened in a browser.



How TO Run ?
Run app.py 
and run testing.py to test app

It downloads the video from youtube url.
Create MP4 chunks of the video using ffmpeg command without transcoding and restating timestamps.
Those MP4 chunks then overlayed with a png image via transcoding FFMPEG command on 6 threads at a time.
Overlayed MP4 chunks are joined using FFMPEG concat without re-encoding them into a final output.mp4.
Then output.mp4 is convereted to ts packets and m3u8 is generated for it which can be played, I played it via http server python and VLC.
