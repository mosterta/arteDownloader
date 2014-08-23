#!/usr/bin/python
# March 8, 2014
import urllib, urllib2
from HTMLParser import HTMLParser
import sys
import argparse
import re
import requests
import time
import os.path
import os

#from ID3 import *

class ArteHTMLParser(HTMLParser):
  tvguide_json = []
  def getTvGuideURL(self):
    return self.tvguide_json
  
  def handle_starttag(self, tag, attrs):
     if tag == 'div':
       for attr in attrs:
	 if attr[0] == 'class':
	   if attr[1] <> 'video-container':
	     return 
	 if attr[0] == 'arte_vp_lang':
	   if attr[1] <> 'de_DE':
	     return 
	 if attr[0] == 'arte_vp_url':
	   if attr[1].find('PLUS7-D') <> -1:
	      self.tvguide_json = attr[1]
	   
class ArteDownload:
   def __init__(self, url, verbose, tags):
      self.url = url
      self.verbose = verbose
      self.tags = tags
      self.download_progress = 0
      self.current_time = time.time()
      self.titleList = []
      self.artistList = []
      self.streamURLlist = self.getStreamURLlist(self.url)

   def getStreamURLlist(self, url):
      streamList = []
      tracks = []
      api = "{0}".format(url)
      if api.find("http://") == -1 and api.find("https://") == -1:
         api = "http://{0}".format(url)
      r = requests.get(api)
      parser = ArteHTMLParser()
      parser.feed(r.text)
      jsonURL = parser.getTvGuideURL()
      r = requests.get(jsonURL)

      #print r.json()
      jsonPlayer = r.json()['videoJsonPlayer']
      title = jsonPlayer['VTI']
      jsonVSR = jsonPlayer['VSR']
      jsonVideo = jsonVSR['HTTP_MP4_SQ_1']
      if jsonVideo['versionShortLibelle'] <> 'DE':
	jsonVideo = jsonVSR['HTTP_MP4_SQ_2']
      self.titleList.append(title)
      videoUrl = jsonVideo['url']
      streamList.append(videoUrl)
      return streamList

   def addID3(self, title, artist):
      try:
         id3info = ID3("{0}.mp3".format(title))
         # Slicing is to get the whole track name
         # because SoundCloud titles usually have
         # a dash between the artist and some name
         split = title.find("-")
         if not split == -1:
            id3info['TITLE'] = title[(split + 2):] 
            id3info['ARTIST'] = title[:split] 
         else:
            id3info['TITLE'] = title
            id3info['ARTIST'] = artist
         print "\nID3 tags added"
      except InvalidTagError, err:
         print "\nInvalid ID3 tag: {0}".format(err)
   
   def downloadSongs(self):
      done = False
      for title, streamURL in zip(self.titleList, self.streamURLlist):
         if not done:
            filename = self.getTitleFilename(title)
            filename = "{0}.mp4".format(filename)
            sys.stdout.write("\nDownloading: {0}\n\r".format(filename))
	    if not os.path.isfile(filename):
	      filename, headers = urllib.urlretrieve(url=streamURL, filename=filename, reporthook=self.report)
	      #self.addID3(title, artist)
	      # reset download progress to report multiple track download progress correctly
	      self.download_progress = 0
	    else:
	      print "File Exists"
   
   def report(self, block_no, block_size, file_size):
      self.download_progress += block_size
      if int(self.download_progress / 1024 * 8) > 1000:
         speed = "{:03.03f} Mbps".format(round((self.download_progress / 1024 / 1024 * 8) / (time.time() - self.current_time), 2))
      else:
         speed = "{:33.03f} Kbps".format(round((self.download_progress / 1024 * 8) / (time.time() - self.current_time), 2))
      rProgress = round(self.download_progress/1024.00/1024.00, 2)
      rFile = round(file_size/1024.00/1024.00, 2)
      percent = round(100 * float(self.download_progress)/float(file_size))
      sys.stdout.write("\r                                                                             ")
      sys.stdout.write("\r {3} ({0:2.2f}/{1:2.2f}MB): {2:2.0f}%".format(rProgress, rFile, percent, speed))
      sys.stdout.flush()

        ## Convenience Methods
   def getTitleFilename(self, title):
                '''
                Cleans a title from Soundcloud to be a guaranteed-allowable filename in any filesystem.
                '''
                allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789-_()"
                title = title.replace("/", "_")
                return ''.join(c for c in title if c in allowed)

if __name__ == "__main__":
   if (int(requests.__version__[0]) == 0):
      print "Your version of Requests needs updating\nTry: '(sudo) pip install -U requests'"
      sys.exit()

   # parse arguments
   parser = argparse.ArgumentParser()
   parser.add_argument("-v", "--verbose", help="increase output verbosity",
      action="store_true")
   parser.add_argument("-t", "--id3tags", help="add id3 tags",
      action="store_true")
   parser.add_argument("ARTE_URL", help="ARTE URL")
   args = parser.parse_args()
   verbose = bool(args.verbose)
   tags = bool(args.id3tags)
   download = ArteDownload(args.ARTE_URL, verbose, tags)
   download.downloadSongs()
