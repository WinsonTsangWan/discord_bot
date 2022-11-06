import discord
import youtube_dl
import urllib
import re

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
        self.size = 0
        pass

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
        self.size += 1
        return info

    def next_song(self):
        self.size -= 1
        self.curr_song_info= self.queue.pop(0)
        self.history.insert(0, self.curr_song_info)
        return self.curr_song_info

    def current_song(self):
        return self.curr_song_info

    def clear(self):
        self.queue = []
        self.size = 0
    
