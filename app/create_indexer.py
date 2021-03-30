import os
import re
import json
import pickle
from stemming.porter2 import stem
from gensim import corpora, models


# tokenization
def preprocessing(text):
    words = []
    words.extend(re.findall(r'[\w]+', text))
    words = [word.lower() for word in words]
    words = [stem(word) for word in words]
    return words


class Indexer:

    def __init__(self):
        self.title, self.artist, self.album, self.lyrics, self.date, self.title_reverse_indexer, self.artist_reverse_indexer, self.album_reverse_indexer, self.lyrics_reverse_indexer, self.title_word_counts, self.artist_word_counts, self.album_word_counts, self.lyrics_word_counts, self.artist_link, self.album_link, self.link = self.build_index()

    @staticmethod
    def build_index():
        title, artist, album, lyrics, date = dict(), dict(), dict(), dict(), dict()
        title_reverse_indexer, artist_reverse_indexer, album_reverse_indexer, lyrics_reverse_indexer = dict(), dict(), dict(), dict()
        title_word_counts, artist_word_counts, album_word_counts, lyrics_word_counts = dict(), dict(), dict(), dict()
        artist_link, album_link, link = dict(), dict(), dict()
        for root, dirs, files in os.walk('./data/json files'):
            for filename in files:
                file_path = './data/json files/' + filename
                with open(file_path) as f:
                    songs = json.load(f)
                name = songs['name']

                # process artist
                artist_url = [songs['url'] for _ in songs['songs']]
                for index in range(len(artist_url)):
                    artist[name, index] = name
                    artist_link[name, index] = artist_url[index]
                    words = preprocessing(artist[name, index])
                    for i in range(len(words)):
                        word = words[i]
                        pos = i
                        if word in artist_reverse_indexer:
                            if (name, index) in artist_reverse_indexer[word]:
                                artist_reverse_indexer[word][name, index].append(pos)
                            else:
                                artist_reverse_indexer[word][name, index] = [pos]
                        else:
                            artist_reverse_indexer[word] = {(name, index): [pos]}

                        if (name, index) in artist_word_counts:
                            if word in artist_word_counts[name, index]:
                                artist_word_counts[name, index][word] += 1
                            else:
                                artist_word_counts[name, index][word] = 1
                        else:
                            artist_word_counts[name, index] = {word: 1}

                # process title
                title_name = [song['title'] for song in songs['songs']]
                for index, text in enumerate(title_name):
                    title[name, index] = str(text)
                    words = preprocessing(title[name, index])
                    for i in range(len(words)):
                        word = words[i]
                        pos = i
                        if word in title_reverse_indexer:
                            if (name, index) in title_reverse_indexer[word]:
                                title_reverse_indexer[word][name, index].append(pos)
                            else:
                                title_reverse_indexer[word][name, index] = [pos]
                        else:
                            title_reverse_indexer[word] = {(name, index): [pos]}

                        if (name, index) in title_word_counts:
                            if word in title_word_counts[name, index]:
                                title_word_counts[name, index][word] += 1
                            else:
                                title_word_counts[name, index][word] = 1
                        else:
                            title_word_counts[name, index] = {word: 1}

                # process album
                album_name = []
                album_url = []
                for song in songs['songs']:
                    if song['album'] is not None:
                        album_name.append(song['album']['name'])
                        album_url.append(song['album']['url'])
                    else:
                        album_name.append('')
                        album_url.append('about:blank')
                for index, text in enumerate(album_name):
                    album[name, index] = str(text)
                    album_link[name, index] = album_url[index]
                    words = preprocessing(album[name, index])
                    for i in range(len(words)):
                        word = words[i]
                        pos = i
                        if word in album_reverse_indexer:
                            if (name, index) in album_reverse_indexer[word]:
                                album_reverse_indexer[word][name, index].append(pos)
                            else:
                                album_reverse_indexer[word][name, index] = [pos]
                        else:
                            album_reverse_indexer[word] = {(name, index): [pos]}

                        if (name, index) in album_word_counts:
                            if word in album_word_counts[name, index]:
                                album_word_counts[name, index][word] += 1
                            else:
                                album_word_counts[name, index][word] = 1
                        else:
                            album_word_counts[name, index] = {word: 1}

                # process lyrics
                lyrics_content = [song['lyrics'] for song in songs['songs']]
                url = [song['url'] for song in songs['songs']]
                for index, text in enumerate(lyrics_content):
                    lyrics[name, index] = str(text).replace(name.lower(), '')
                    link[name, index] = url[index]
                    words = preprocessing(lyrics[name, index])
                    for i in range(len(words)):
                        word = words[i]
                        pos = i
                        if word in lyrics_reverse_indexer:
                            if (name, index) in lyrics_reverse_indexer[word]:
                                lyrics_reverse_indexer[word][name, index].append(pos)
                            else:
                                lyrics_reverse_indexer[word][name, index] = [pos]
                        else:
                            lyrics_reverse_indexer[word] = {(name, index): [pos]}

                        if (name, index) in lyrics_word_counts:
                            if word in lyrics_word_counts[name, index]:
                                lyrics_word_counts[name, index][word] += 1
                            else:
                                lyrics_word_counts[name, index][word] = 1
                        else:
                            lyrics_word_counts[name, index] = {word: 1}

                # process release dates
                release_date = [song['release_date'] for song in songs['songs']]
                for index, text in enumerate(release_date):
                    date[name, index] = str(text)
                    if date[name, index] == 'None':
                        date[name, index] = ''

        title_reverse_indexer = dict(sorted(title_reverse_indexer.items(), key=lambda x: x[0]))
        artist_reverse_indexer = dict(sorted(artist_reverse_indexer.items(), key=lambda x: x[0]))
        album_reverse_indexer = dict(sorted(album_reverse_indexer.items(), key=lambda x: x[0]))
        lyrics_reverse_indexer = dict(sorted(lyrics_reverse_indexer.items(), key=lambda x: x[0]))

        return title, artist, album, lyrics, date, title_reverse_indexer, artist_reverse_indexer, album_reverse_indexer, lyrics_reverse_indexer, title_word_counts, artist_word_counts, album_word_counts, lyrics_word_counts, artist_link, album_link, link

    def build_topic_list(self):
        common_texts = []
        topic_related_words = {}

        with open('./englishST.txt', encoding='utf-8') as f:
            stop_words = f.read().split()
        for (artist, index) in self.lyrics.keys():
            words = []
            words.extend(re.findall(r'[\w]+', self.lyrics[artist, index]))
            words = [word.lower() for word in words]
            words = [word for word in words if word not in stop_words]
            common_texts.append(words)

        common_dictionary = corpora.Dictionary(common_texts)
        common_dictionary.filter_extremes(no_below=10, no_above=0.5, keep_n=10000, keep_tokens=None)
        bow = [common_dictionary.doc2bow(words) for words in common_texts]
        lda = models.LdaModel(bow, num_topics=100, id2word=common_dictionary, random_state=1)
        topics = lda.show_topics(num_topics=100, num_words=5, formatted=False)
        topics_words = [[word[0] for word in topic[1]] for topic in topics]
        for words, (artist, index) in zip(common_texts, self.lyrics.keys()):
            doc_bow = common_dictionary.doc2bow(words)
            topic_related_words[artist, index] = topics_words[lda[doc_bow][0][0]]
        return topic_related_words

    def store_data(self):
        with open('./data/pickle/title.pickle', 'wb') as f:
            pickle.dump(self.title, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/title_reverse_indexer.pickle', 'wb') as f:
            pickle.dump(self.title_reverse_indexer, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/title_words_count.pickle', 'wb') as f:
            pickle.dump(self.title_word_counts, f, protocol=pickle.HIGHEST_PROTOCOL)

        with open('./data/pickle/artist.pickle', 'wb') as f:
            pickle.dump(self.artist, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/artist_reverse_indexer.pickle', 'wb') as f:
            pickle.dump(self.artist_reverse_indexer, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/artist_words_count.pickle', 'wb') as f:
            pickle.dump(self.artist_word_counts, f, protocol=pickle.HIGHEST_PROTOCOL)

        with open('./data/pickle/album.pickle', 'wb') as f:
            pickle.dump(self.album, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/album_reverse_indexer.pickle', 'wb') as f:
            pickle.dump(self.album_reverse_indexer, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/album_words_count.pickle', 'wb') as f:
            pickle.dump(self.album_word_counts, f, protocol=pickle.HIGHEST_PROTOCOL)

        with open('./data/pickle/lyrics.pickle', 'wb') as f:
            pickle.dump(self.lyrics, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/lyrics_reverse_indexer.pickle', 'wb') as f:
            pickle.dump(self.lyrics_reverse_indexer, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('./data/pickle/lyrics_words_count.pickle', 'wb') as f:
            pickle.dump(self.lyrics_word_counts, f, protocol=pickle.HIGHEST_PROTOCOL)

        with open('data/pickle/date.pickle', 'wb') as f:
            pickle.dump(self.date, f, protocol=pickle.HIGHEST_PROTOCOL)

        with open('data/pickle/artist_link.pickle', 'wb') as f:
            pickle.dump(self.artist_link, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('data/pickle/album_link.pickle', 'wb') as f:
            pickle.dump(self.album_link, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open('data/pickle/link.pickle', 'wb') as f:
            pickle.dump(self.link, f, protocol=pickle.HIGHEST_PROTOCOL)


indexer = Indexer()
indexer.store_data()
