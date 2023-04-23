import argparse
from HLS_Service import HLS

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input directory path')
    args = parser.parse_args()

    hls_generator = HLS()
    hls_stream_url = hls_generator.generate_hls_stream(args.input)
    print(f"HLS stream URL: {hls_stream_url}")
