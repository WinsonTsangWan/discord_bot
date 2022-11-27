import youtube_dl
import urllib
import re

from random import shuffle

YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}

class Queue:
    def __init__(self) -> None:
        # self.queue and self.history are both list of dicts
        # each dict is the info dict, output by ytdl.extract_info()
        # note: for queue, 0 = oldest, -1 = latest
        # note: for history, 0 = latest, -1 = oldest
        self.queue = []
        self.curr_song_info = {}
        self.history = []

    def add_song(self, ctx):
        # Search for query on Youtube, get URL of top search result
        query = "+".join(ctx.message.content.split()[1:])
        url = "https://www.youtube.com/results?search_query=" + query
        search_result_page = urllib.request.urlopen(url)
        video_results = re.findall(r"watch\?v=(\S{11})", search_result_page.read().decode())
        top_result_ID = video_results[0]
        top_result_url = "https://www.youtube.com/watch?v=" + top_result_ID
        
        # Download Youtube video audio, add info to self.queue 
        # (note: info is a dictionary with all the information for 
        # the YouTube webpage given by top_result_url)
        with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ytdl:
            info = ytdl.extract_info(top_result_url, download = False)
            info["page_url"] = top_result_url 
        self.queue.append(info)
        return info

    def next_song(self):
        if self.curr_song_info:
            self.history.insert(0, self.curr_song_info)
        self.curr_song_info = self.queue.pop(0)
        return self.curr_song_info

    def get_history(self):
        return self.history

    def get_current_song(self):
        return self.curr_song_info

    def get_queue(self):
        return self.queue
    
    def get_size(self):
        return len(self.queue)
    
    def repeat_song(self):
        self.queue.insert(0, self.curr_song_info)

    def clear_queue(self):
        self.queue = []

    def shuffle(self):
        shuffle(self.queue)
