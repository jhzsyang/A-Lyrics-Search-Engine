import os
import re
import json
import pickle
from stemming.porter2 import stem


# tokenization
def preprocessing(text):
    words = []
    words.extend(re.findall(r'[\w]+', text))
    words = [word.lower() for word in words]
    words = [stem(word) for word in words]
    return words


def clean_data(error, artist_url, title_name, album_name, album_url, lyrics_content, url, release_date):
    error_songs = []
    for i in reversed(error):
        error_songs.append([i, artist_url[i], title_name[i], album_name[i], album_url[i], lyrics_content[i], url[i],
                            release_date[i]])
        del artist_url[i]
        del title_name[i]
        del album_name[i]
        del album_url[i]
        del lyrics_content[i]
        del url[i]
        del release_date[i]
    for k in range(len(error_songs) - 1, -1, -1):
        index, temp_artist_url, temp_title_name, temp_album_name, temp_album_url, temp_lyrics_content, temp_url, temp_release_date = \
            error_songs[k]
        artist_url.append(temp_artist_url)
        title_name.append(temp_title_name)
        album_name.append(temp_album_name)
        album_url.append(temp_album_url)
        lyrics_content.append(temp_lyrics_content)
        url.append(temp_url)
        release_date.append(temp_release_date)
    return artist_url, title_name, album_name, album_url, lyrics_content, url, release_date


class Indexer:

    def __init__(self):
        self.title, self.artist, self.album, self.lyrics, self.texts, self.date, self.title_reverse_index, self.artist_reverse_index, self.album_reverse_index, self.lyrics_reverse_index, self.reverse_index, self.title_words_count, self.artist_words_count, self.album_words_count, self.lyrics_words_count, self.words_count, self.artist_link, self.album_link, self.link = self.build_index()

    @staticmethod
    def build_index():
        title, artist, album, lyrics, texts, date = {}, {}, {}, {}, {}, {}
        title_reverse_index, artist_reverse_index, album_reverse_index, lyrics_reverse_index, reverse_index = {}, {}, {}, {}, {}
        title_words_count, artist_words_count, album_words_count, lyrics_words_count, words_count = {}, {}, {}, {}, {}
        artist_link, album_link, link = {}, {}, {}

        for root, dirs, files in os.walk('./data/json files'):
            for filename in files:
                file_path = './data/json files/' + filename
                with open(file_path) as f:
                    songs = json.load(f)
                name = songs['name']
                artist_url = [songs['url'] for _ in songs['songs']]
                title_name = [song['title'] for song in songs['songs']]
                album_name = []
                album_url = []
                for song in songs['songs']:
                    if song['album'] is not None:
                        album_name.append(song['album']['name'])
                        album_url.append(song['album']['url'])
                    else:
                        album_name.append('')
                        album_url.append('about:blank')
                lyrics_content = [song['lyrics'] for song in songs['songs']]
                url = [song['url'] for song in songs['songs']]
                release_date = [song['release_date'] for song in songs['songs']]

                # clean data
                error, error1, error2, error3 = [], [], [], []
                for i in range(len(url)):
                    if url[i][-6:] != 'lyrics':
                        error.append(i)
                for i in reversed(error):
                    del artist_url[i]
                    del title_name[i]
                    del album_name[i]
                    del album_url[i]
                    del lyrics_content[i]
                    del url[i]
                    del release_date[i]
                error1 = []
                for i in range(len(album_name)):
                    if album_name[i] == 'Unreleased Songs':
                        error1.append(i)
                error2 = []
                for i in range(len(album_name)):
                    if album_name[i] == '':
                        error2.append(i)
                error3 = []
                for i in range(len(release_date)):
                    if release_date[i] is None:
                        error3.append(i)
                artist_url, title_name, album_name, album_url, lyrics_content, url, release_date = clean_data(error1,
                                                                                                              artist_url,
                                                                                                              title_name,
                                                                                                              album_name,
                                                                                                              album_url,
                                                                                                              lyrics_content,
                                                                                                              url,
                                                                                                              release_date)
                artist_url, title_name, album_name, album_url, lyrics_content, url, release_date = clean_data(error2,
                                                                                                              artist_url,
                                                                                                              title_name,
                                                                                                              album_name,
                                                                                                              album_url,
                                                                                                              lyrics_content,
                                                                                                              url,
                                                                                                              release_date)
                artist_url, title_name, album_name, album_url, lyrics_content, url, release_date = clean_data(error3,
                                                                                                              artist_url,
                                                                                                              title_name,
                                                                                                              album_name,
                                                                                                              album_url,
                                                                                                              lyrics_content,
                                                                                                              url,
                                                                                                              release_date)

                # process artist
                for index in range(len(artist_url)):
                    artist[name, index] = name
                    texts[name, index] = name
                    artist_link[name, index] = artist_url[index]
                    words = preprocessing(artist[name, index])
                    for i in range(len(words)):
                        word = words[i]
                        pos = i
                        if word in artist_reverse_index:
                            if (name, index) in artist_reverse_index[word]:
                                artist_reverse_index[word][name, index].append(pos)
                            else:
                                artist_reverse_index[word][name, index] = [pos]
                        else:
                            artist_reverse_index[word] = {(name, index): [pos]}

                        if (name, index) in artist_words_count:
                            if word in artist_words_count[name, index]:
                                artist_words_count[name, index][word] += 1
                            else:
                                artist_words_count[name, index][word] = 1
                        else:
                            artist_words_count[name, index] = {word: 1}

                        if word in reverse_index:
                            if (name, index) in reverse_index[word]:
                                reverse_index[word][name, index].append(pos)
                            else:
                                reverse_index[word][name, index] = [pos]
                        else:
                            reverse_index[word] = {(name, index): [pos]}

                        if (name, index) in words_count:
                            if word in words_count[name, index]:
                                words_count[name, index][word] += 1
                            else:
                                words_count[name, index][word] = 1
                        else:
                            words_count[name, index] = {word: 1}

                # process title
                for index, text in enumerate(title_name):
                    title[name, index] = str(text)
                    texts[name, index] += title[name, index]
                    words = preprocessing(title[name, index])
                    for i in range(len(words)):
                        word = words[i]
                        pos = i
                        if word in title_reverse_index:
                            if (name, index) in title_reverse_index[word]:
                                title_reverse_index[word][name, index].append(pos)
                            else:
                                title_reverse_index[word][name, index] = [pos]
                        else:
                            title_reverse_index[word] = {(name, index): [pos]}

                        if (name, index) in title_words_count:
                            if word in title_words_count[name, index]:
                                title_words_count[name, index][word] += 1
                            else:
                                title_words_count[name, index][word] = 1
                        else:
                            title_words_count[name, index] = {word: 1}

                        if word in reverse_index:
                            if (name, index) in reverse_index[word]:
                                reverse_index[word][name, index].append(pos)
                            else:
                                reverse_index[word][name, index] = [pos]
                        else:
                            reverse_index[word] = {(name, index): [pos]}

                        if (name, index) in words_count:
                            if word in words_count[name, index]:
                                words_count[name, index][word] += 1
                            else:
                                words_count[name, index][word] = 1
                        else:
                            words_count[name, index] = {word: 1}

                # process album
                for index, text in enumerate(album_name):
                    album[name, index] = str(text)
                    texts[name, index] += album[name, index]
                    album_link[name, index] = album_url[index]
                    words = preprocessing(album[name, index])
                    for i in range(len(words)):
                        word = words[i]
                        pos = i
                        if word in album_reverse_index:
                            if (name, index) in album_reverse_index[word]:
                                album_reverse_index[word][name, index].append(pos)
                            else:
                                album_reverse_index[word][name, index] = [pos]
                        else:
                            album_reverse_index[word] = {(name, index): [pos]}

                        if (name, index) in album_words_count:
                            if word in album_words_count[name, index]:
                                album_words_count[name, index][word] += 1
                            else:
                                album_words_count[name, index][word] = 1
                        else:
                            album_words_count[name, index] = {word: 1}

                        if word in reverse_index:
                            if (name, index) in reverse_index[word]:
                                reverse_index[word][name, index].append(pos)
                            else:
                                reverse_index[word][name, index] = [pos]
                        else:
                            reverse_index[word] = {(name, index): [pos]}

                        if (name, index) in words_count:
                            if word in words_count[name, index]:
                                words_count[name, index][word] += 1
                            else:
                                words_count[name, index][word] = 1
                        else:
                            words_count[name, index] = {word: 1}

                # process lyrics
                for index, text in enumerate(lyrics_content):
                    temp = re.sub("\[.*\]", '', str(lyrics_content[index]))
                    lyrics[name, index] = temp.replace(name, '')
                    texts[name, index] += lyrics[name, index]
                    link[name, index] = url[index]
                    words = preprocessing(lyrics[name, index])
                    for i in range(len(words)):
                        word = words[i]
                        pos = i
                        if word in lyrics_reverse_index:
                            if (name, index) in lyrics_reverse_index[word]:
                                lyrics_reverse_index[word][name, index].append(pos)
                            else:
                                lyrics_reverse_index[word][name, index] = [pos]
                        else:
                            lyrics_reverse_index[word] = {(name, index): [pos]}

                        if (name, index) in lyrics_words_count:
                            if word in lyrics_words_count[name, index]:
                                lyrics_words_count[name, index][word] += 1
                            else:
                                lyrics_words_count[name, index][word] = 1
                        else:
                            lyrics_words_count[name, index] = {word: 1}

                        if word in reverse_index:
                            if (name, index) in reverse_index[word]:
                                reverse_index[word][name, index].append(pos)
                            else:
                                reverse_index[word][name, index] = [pos]
                        else:
                            reverse_index[word] = {(name, index): [pos]}

                        if (name, index) in words_count:
                            if word in words_count[name, index]:
                                words_count[name, index][word] += 1
                            else:
                                words_count[name, index][word] = 1
                        else:
                            words_count[name, index] = {word: 1}

                # process release dates
                for index, text in enumerate(release_date):
                    date[name, index] = str(text)
                    if date[name, index] == 'None':
                        date[name, index] = ''

        title_reverse_index = dict(sorted(title_reverse_index.items(), key=lambda x: x[0]))
        artist_reverse_index = dict(sorted(artist_reverse_index.items(), key=lambda x: x[0]))
        album_reverse_index = dict(sorted(album_reverse_index.items(), key=lambda x: x[0]))
        lyrics_reverse_index = dict(sorted(lyrics_reverse_index.items(), key=lambda x: x[0]))
        reverse_index = dict(sorted(reverse_index.items(), key=lambda x: x[0]))
        return title, artist, album, lyrics, texts, date, title_reverse_index, artist_reverse_index, album_reverse_index, lyrics_reverse_index, reverse_index, title_words_count, artist_words_count, album_words_count, lyrics_words_count, words_count, artist_link, album_link, link

    def store_data(self):
        with open('./data/pickle/title.pickle', 'wb') as f1:
            pickle.dump(self.title, f1, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/title_reverse_index.pickle', 'wb') as f2:
            pickle.dump(self.title_reverse_index, f2, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/title_words_count.pickle', 'wb') as f3:
            pickle.dump(self.title_words_count, f3, protocol=pickle.HIGHEST_PROTOCOL)

        with open('./data/pickle/artist.pickle', 'wb') as f4:
            pickle.dump(self.artist, f4, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/artist_reverse_index.pickle', 'wb') as f5:
            pickle.dump(self.artist_reverse_index, f5, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/artist_words_count.pickle', 'wb') as f6:
            pickle.dump(self.artist_words_count, f6, protocol=pickle.HIGHEST_PROTOCOL)

        with open('./data/pickle/album.pickle', 'wb') as f7:
            pickle.dump(self.album, f7, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/album_reverse_index.pickle', 'wb') as f8:
            pickle.dump(self.album_reverse_index, f8, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/album_words_count.pickle', 'wb') as f9:
            pickle.dump(self.album_words_count, f9, protocol=pickle.HIGHEST_PROTOCOL)

        with open('./data/pickle/lyrics.pickle', 'wb') as f10:
            pickle.dump(self.lyrics, f10, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/lyrics_reverse_index.pickle', 'wb') as f11:
            pickle.dump(self.lyrics_reverse_index, f11, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/lyrics_words_count.pickle', 'wb') as f12:
            pickle.dump(self.lyrics_words_count, f12, protocol=pickle.HIGHEST_PROTOCOL)

        with open('data/pickle/texts.pickle', 'wb') as f13:
            pickle.dump(self.texts, f13, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/reverse_index.pickle', 'wb') as f14:
            pickle.dump(self.reverse_index, f14, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/words_count.pickle', 'wb') as f15:
            pickle.dump(self.words_count, f15, protocol=pickle.HIGHEST_PROTOCOL)

        with open('data/pickle/date.pickle', 'wb') as f16:
            pickle.dump(self.date, f16, protocol=pickle.HIGHEST_PROTOCOL)

        with open('data/pickle/artist_link.pickle', 'wb') as f17:
            pickle.dump(self.artist_link, f17, protocol=pickle.HIGHEST_PROTOCOL)
        with open('data/pickle/album_link.pickle', 'wb') as f18:
            pickle.dump(self.album_link, f18, protocol=pickle.HIGHEST_PROTOCOL)
        with open('data/pickle/link.pickle', 'wb') as f19:
            pickle.dump(self.link, f19, protocol=pickle.HIGHEST_PROTOCOL)


indexer = Indexer()
indexer.store_data()
