"""
Module that wraps interaction with spotify API (using spotipy lib)
"""

import spotipy
import unicodedata
from spotipy.oauth2 import SpotifyClientCredentials
import numpy as np

class SpotifyWrapper:

	def __init__(self, client_id, client_secret):
		"""
		Constructor of the class

		@param client_id
		@param client_secret
		"""

		self.client_id = client_id
		self.client_secret = client_secret

		# Manage Authorization in Client Credentials mode
		client_credentials_manager = SpotifyClientCredentials(client_id=client_id, \
																													client_secret=client_secret, \
																													proxies=None)

		# create the spotipy client object
		self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


	def remove_accents(self, string):
			"""
			Removes the accents from the inout string
			@param string String to remove accents from
			@returns String without accents
			"""
			return ''.join((c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn'))


	def search_artist(self, band_name):
			"""
			Calls the Spotify API object and returns only one artist object
			@param band_name String with the band name
			@return Dictionary with the artist information
			"""
			
			# list with band names whose name will be changed
			manual_name_changes = {
					'chk chk chk' : '!!!',
					'other' : 'another'
			};
			
			try:

					# remove accents and make lowercase
					band_name = self.remove_accents(band_name).lower()
					
					# call api
					results = self.sp.search(q=band_name, limit=20, type='artist')
					#print("{} => {} artists found".format(band_name, len(results)))
					
					# some manual changes
					if band_name in list(manual_name_changes.keys()):
							band_name = manual_name_changes[band_name]

					# return only one artist
					if results['artists']['total'] > 0:
							return [artist for artist in results['artists']['items'] if self.remove_accents(artist['name']).lower() == band_name][0]
					else:
							return []

			except:
					print('Error searching artist')
					return []

	def search_song(self, artist_name, track_name):
			"""
			Calls the Spotify API object and returns only one song object
			@parsam artist_name String with the artist name
			@param track_name String with the song title
			@return Dictionary with the song information
			"""

			try:

					#print('Searching: {} - {}'.format(artist_name, track_name))

					# remove accents and make lowercase
					track_name = self.remove_accents(track_name.lower())
					artist_name = self.remove_accents(artist_name.lower())
					
					# call api
					results = self.sp.search(q='artist:' + artist_name + ' track:' + track_name, type='track')

					# return only 
					for r in results['tracks']['items']:
							#print('Found Debug: {} - {}'.format(r['artists'][0]['name'], r['name']))
							if artist_name == self.remove_accents(r['artists'][0]['name'].lower()):
									#print('    Found: {} - {}'.format(r['artists'][0]['name'], r['name']))
									return r
					
					# print('    Not Found\n')
					
			except:
					print('Error searching song')
					return []

	def get_albums_of_artist(self, artist_id):
			"""
			Gets the albums of the artist passed as argument
			@param artist_id Id of the artist
			@return Array of dictionaries, each one with the information of one album
			"""
			
			albums = []
			
			# call API
			results = self.sp.artist_albums(artist_id=artist_id, album_type='album', limit=50)
			
			# store results in array
			albums.extend(results['items'])

			# get more albums while more results are available...
			while results['next']:
					results = self.sp.next(results)
					albums.extend(results['items'])

			# skip duplicate albums (by album name)
			unique_albums = []
			unique_names = set()
			for album in albums:
					name = album['name'].lower()
					if not name in unique_names:  
							unique_albums.append(album)
							unique_names.add(name)
			
			return unique_albums

	def get_tracks_of_album(self, album_id):
			"""
			Gets the tracks of the album passed as argument
			@param album_id Id of the album
			@return Array of dictionaries, each one with the information of one track
			"""
			
			tracks = []
			
			# call API
			results = self.sp.album_tracks(album_id=album_id, limit=50)
			
			# store results in array
			tracks.extend(results['items'])
			
			# get more tracks while more results are available...
			while results['next']:
					results = self.sp.next(results)
					tracks.extend(results['items'])

			return tracks

	def get_audio_features_of_tracks(self, track_ids):
			"""
			Gets the audio features of the tracks passed as argument
			@param track_ids List of track ids
			@return Array of dictionaries, each one with the information of one track
			"""
					
			# call API
			features = self.sp.audio_features(tracks=track_ids)

			return features

	def get_audio_features_of_lots_of_tracks(self, tracks):
		"""
		Gets the audio features of the tracks passed as argument
		@param tracks List of dicts - each dict is a track with an id field
		@return tracks list of dicts with the audio features fields
		"""

		# define the maximum number of tracks to ask in a single api call
		num_tracks_per_api_call = 20

		# execute as many api call loops as needed
		num_tracks = len(tracks)
		for api_call in range(0, int(np.ceil(num_tracks/num_tracks_per_api_call))):

			# set first/last tracks to add in the call    
			first_track_idx = api_call * num_tracks_per_api_call
			last_track_idx = (api_call+1) * num_tracks_per_api_call - 1
			last_track_idx = last_track_idx if last_track_idx <= num_tracks else num_tracks - 1

			print('Api Call {} from {} to {}'.format(api_call,first_track_idx,last_track_idx))

			# get tracks audio features
			tracks_features = self.get_audio_features_of_tracks([t['id'] for t in tracks[first_track_idx:last_track_idx+1]])

			# put back audio features to track object
			for tf in tracks_features:
				found_track = list(filter(lambda tr: tr['id'] == tf['id'], tracks))[0]
				#found_track['audio_features'] = tf
				found_track.update(tf)

		return tracks
