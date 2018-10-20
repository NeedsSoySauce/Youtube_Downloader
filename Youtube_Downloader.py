import json
import os
import youtube_dl
from appJar import gui
from log import YDL_Logger
import time

CONFIG = "config.json"

# These are used to label GUI widgets
SAVE_ENTRY = "savepath"
URL_LABEL = "URL(s) to download"
URL_LABEL_TEXT = "1. Enter YouTube URL(s) to download into the box below (one URL per line)\n2. Set the directory to save the downloaded files\n3. Click download!"
                    
URL_ENTRY = "URL(s)"
DL_BUTTON = "Download"

# These are set automatically, don't edit them
savepath = "" # This the path that's displayed in the GUI without the output template
max_threads = 0
running_threads = 0

# Arguments for youtube-dl
ydl_opts = {
    'format': 'bestaudio/best',
    'logger': YDL_Logger(),
    'progress_hooks': [],
    'outtmpl': '',
    'noplaylist': True,
    'writethumbnail': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio', 
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }, {
        'key': 'EmbedThumbnail',
    }],
}

app = gui("Youtube Downloader", useTtk=True)

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

# Writes cfg_dict to the config file
def update_config(cfg_dict):
    with open(CONFIG, 'w') as cfg_file:
        json.dump(cfg_dict, cfg_file, sort_keys=True, indent=4 )

# Loads config.json and returns it as a dict
def load_config():   
    with open(CONFIG, 'r') as cfg:
        config_opts = json.load(cfg)
    return config_opts

# Checks the options in the given config and corrects any that won't work
def validate_config(config_opts):
    keys = config_opts.keys()

    # If there is no savepath set in the config, we set it to the directory of this file,
    # otherwise we set savepath to whatever the value is in the config
    if ('savepath' not in keys or config_opts['savepath'] == ""):
        config_opts['savepath'] = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/").title()

    if ('max_dl_threads' not in keys or not isinstance(config_opts['max_dl_threads'], int) or config_opts['max_dl_threads'] <= 0):
        config_opts['max_dl_threads'] = os.cpu_count()
 
    update_config(config_opts)

# Applies config options to the appropriate values
def apply_config():
    global max_threads, savepath, ydl_opts

    config_opts = load_config()

    # Fix any invalid config values
    validate_config(config_opts)

    max_threads = config_opts['max_dl_threads']
    savepath = config_opts['savepath']
    ydl_opts['outtmpl'] = savepath + "/" + config_opts['output_template']

def update_save_path():
    global ydl_opts, savepath

    new_path = app.getEntry(SAVE_ENTRY)
    config_opts = load_config()

    savepath = new_path
    config_opts['savepath'] = new_path
    ydl_opts['outtmpl'] = new_path + "/" + config_opts['output_template']

    update_config(config_opts)

# Downloads the video from the given url and returns True if it's a success, False otherwise
def dl_URL(url):
    global running_threads
    running_threads += 1
    print("Thread started for:", url)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url]) # Note, the url must be passed as a list 
    except Exception as error:
        print('"%s" failed with error: %s' % (url, error))

    running_threads -= 1

# Takes a list of URLs to download and downloads them using max_threads at most
def dl_URLs(urls):
    videos = len(urls)
    count = 0

    # Download each video once at a time so that we can keep track of them
    # as they complete and continue downloading the rest if there's an error
    while videos > 0:
        if (running_threads < max_threads):
            app.thread(dl_URL, urls[count])
            videos -= 1
            count += 1
        time.sleep(0.1) # Wait for a few milliseconds before checking again
        
# Downloads all the URL's from the text area
def onButtonPress(button):
    if button == DL_BUTTON:
        urls = app.getTextArea(URL_ENTRY).splitlines()
        app.thread(dl_URLs, urls)
    
# Updates the savepath when the directory entries value is changed
def onDirectoryEntryChange(entry):
    if entry == SAVE_ENTRY:
        update_save_path()

def main():
    global ydl_opts

    apply_config()

    app.setTtkTheme("clam")
    # ydl_opts['progress_hooks'] = [dl_finished, dl_downloading, dl_error]
    
    # Window settings
    app.setPadding(10,10)

    # Adds a right-click edit menu to all entry widgets
    app.addMenuEdit()

    # URL entry
    app.addLabel(URL_LABEL, URL_LABEL_TEXT)
    app.setLabelAlign(URL_LABEL, "left")
    app.addScrolledTextArea(URL_ENTRY)

    # Save path selection
    app.addDirectoryEntry(SAVE_ENTRY)
    app.setEntryDefault(SAVE_ENTRY, savepath)
    app.setEntryChangeFunction(SAVE_ENTRY, onDirectoryEntryChange)

    # Download button
    app.addButtons([DL_BUTTON], onButtonPress)

    # Start GUI - nothing should happen after this
    app.go()

if __name__ == '__main__':
    main()
