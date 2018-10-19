import youtube_dl
from log import YDL_Logger
import json

def dl_finished(d):
    status = d['status']
    if status == 'finished':
        print('Done downloading, now converting ...')

def dl_downloading(d):
    status = d['status']
    if status == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        message = '%s: %.1f%%' % (d['filename'], percent)
        print(message)

def dl_error(d):
    status = d['status']
    if status == 'error':
        print(d['Error downloading:'], d['filename'])

ydl_opts = {
    'format': 'bestaudio/best',
    'writethumbnail': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio', 
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }, 
        {'key': 'EmbedThumbnail'},
        {'key': 'FFmpegMetadata'},
    ],
    'logger': YDL_Logger(),
    'progress_hooks': [dl_finished, dl_downloading, dl_error],
}

# Load config options
with open('config.json') as f:
    ydl_opts.update(json.load(f))

def main():
    url = input("Enter the URL of the youtube video you want to download:\n")
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == '__main__':
    main()
