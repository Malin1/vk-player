#! /opt/anaconda3/bin/python3

import requests
import subprocess
import config
import sys
import os
from utils import timeoutgetch, getch
import threading
import time
import psutil


class vkuser:
	def __init__(self):
		id = 0;
		screen_name = ''

	def __init__ (self, val):
		if not val.isdigit():
			self.id = get_user_id(val)
			self.screen_name = val
		else:
			self.id = val
			self.screen_name = val


def wrapper(func, arg1, arg2, res):
	del res[:]
	res.append(func(arg1, arg2))

def get_user_id (screen_name):
	query = 'https://api.vk.com/method/users.get?user_ids={}'.format(screen_name)
	r = requests.post(query)
	return r.json()['response'][0]['uid']

def get_tracks(owner_id, album_id):
	if not config.owners:
		print('Add ID of user with awesome playlist to the config file')

	if (album_id is not None):
		query = 'https://api.vk.com/method/audio.get?owner_id={}&album_id={}&access_token={}'.format(owner_id, album_id, config.token)
	else:
		query = 'https://api.vk.com/method/audio.get?owner_id={}&access_token={}'.format(owner_id, config.token)

	r = requests.post(query)
	try:
		return [[x['artist'], x['title'], divmod(x['duration'], 60), x['url'].split('?')[0], x ['aid']] for x in r.json()['response'][1:] if 'url' in x]
	except:
		return []

def add_track(owner_id, audio_id):
	query_add = 'https://api.vk.com/method/audio.add?audio_id={}&owner_id={}&access_token={}'.format(audio_id, owner_id, config.token)
	r = requests.post(query_add)
	return r.json()['response']

def get_albums(owner_id):
	query_get_alb = 'https://api.vk.com/method/audio.getAlbums?owner_id={}&access_token={}'.format(owner_id, config.token)
	r = requests.post(query_get_alb)
	try:
		return r.json()['response'][1:]
	except:
		return []

config.owners = [vkuser(x) for i, x in enumerate(config.owners)]

print('Choose wisely:')
[print('{}. {}'.format(num + 1, x.screen_name)) for num, x in enumerate(config.owners)]

try:
	playlist_num = int(getch()) - 1
	owner = config.owners[playlist_num]
except:
	print('Error: bad input')
	sys.exit(1)

res = []
thread = threading.Thread(target=wrapper, args=(get_tracks, owner.id, None, res))
thread.start()

while thread.isAlive():
	for x in '-\|/':  
		b = 'Loading ' + x
		print (b, end='\r')
		time.sleep(0.1)

all_tracks = res[0]

if not all_tracks:
	print('Error: cannot get playlist of the user {}'.format(owner.id))
	sys.exit(-1)

AUTHOR = 0
SONG_NAME = 1
TIME = 2
URL_POSITION = 3

isPaused = False
isRepeat = False
pointer = 0

while True:
	track = all_tracks[pointer]
	tmp = subprocess.Popen(['{}ffplay'.format(config.ffmpeg_path), '-nodisp', '-autoexit', track[URL_POSITION]], stderr=open(os.devnull, 'wb'))
	psProcess = psutil.Process(pid=tmp.pid)

	print("{}\n{} of {}\n{} - {} [{}:{}]".format('~'*40, pointer + 1, len (all_tracks), track[AUTHOR], track[SONG_NAME], track[TIME][0], track[TIME][1]))
	print('prev[q]   next[w]   exit[x]   pause[p]   repeat[r]   add track[a]   select album[b]')
	if (isRepeat):
		print ("Repeat ON")
	
	while tmp.poll() is None:
		x = timeoutgetch()
		if x is None:
			continue

		if x == 'q':
			tmp.kill()
			if pointer < 1: pointer = 1
			pointer -= 2
			isPaused = False
			break
		elif x == 'w':
			tmp.kill()
			if pointer > len(all_tracks) - 1: pointer = len(all_tracks) - 1
			isPaused = False
			break
		elif x == 'x':
			tmp.kill()
			sys.exit()
			break
		elif x == 'p':
			isPaused = not isPaused
			if (isPaused):
				print ("Paused")
				psProcess.suspend()
			else:
				print ("Resumed")
				psProcess.resume()
		elif x == 'r':
			isRepeat = not isRepeat
			if (isRepeat):
				print ("Repeat ON")
			else:
				print ("Repeat OFF")
		elif x == 'a':
			ret = add_track (track [4])
			print ("Track added. The id is: {}".format (ret))
		elif x == 'b':
			albums = get_albums(owner.id)			
			if albums is not None and len(albums) > 0:	
				print('\nChoose album. Press any non-digit key for cancel.')
				[print('{}. {}'.format(num + 1, x ['title'])) for num, x in enumerate(albums)]
					
				try:
					album_num = int(getch()) - 1
					album = albums[album_num]
					res = []
					thread = threading.Thread(target=wrapper, args=(get_tracks, owner.id, album ['album_id'], res))
					thread.start()

					while thread.isAlive():
						for x in '-\|/':  
							b = 'Loading ' + x
							print (b, end='\r')
							time.sleep(0.1)
					
					if res [0] is not None:
						if len (res [0]) > 0:
							all_tracks = res [0]							
							pointer = -1
							tmp.kill()
							print('Playing album #{} ({})'.format(album_num + 1, album ['title']))
						else:
							print('Album {} is empty'.format(album ['title']))
					else:
						print ('Can\'t load album. Keep playing old playlist.')					
				except:
					print ('Bad album number. Keep playing old playlist.')
			else:
				print('\n{} has no albums. Keep playing old playlist.'.format(owner.screen_name))

	if (tmp.poll () is not None and isRepeat):
		pass
	else:
		pointer += 1