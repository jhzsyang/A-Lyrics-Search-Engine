import re
import pickle
from stemming.porter2 import stem
from collections import defaultdict
from math import log10


# tokenization
def preprocessing(text):
    words = []
    words.extend(re.findall(r'[\w]+', text))
    words = [word.lower() for word in words]
    words = [stem(word) for word in words]
    return words


# Boolean operator
def op_not(docs_list, inverted_idx):
    docs = set()
    for word in inverted_idx:
        for artist, index in inverted_idx[word]:
            docs.add((artist, index))
    docs_diff = docs.difference(docs_list)
    return sorted(list(docs_diff), key=lambda x: x[0])


def op_and(a, b):
    res = set(a).intersection(set(b))
    return sorted(list(res), key=lambda x: x[0])


def op_or(a, b):
    res = set(a).union(set(b))
    return sorted(list(res), key=lambda x: x[0])


# search method
def word_search(inverted_idx, word):
    docs_list = []
    word = stem(word.lower())
    if word in inverted_idx:
        for artist, index in inverted_idx[word]:
            docs_list.append((artist, index))

    return docs_list


def proximity_search(inverted_idx, word_1, word_2, proximity=1):
    res = []
    word_1 = stem(word_1.lower())
    word_2 = stem(word_2.lower())
    if word_1 in inverted_idx and word_2 in inverted_idx:
        for (artist, index) in inverted_idx[word_1]:
            if (artist, index) not in inverted_idx[word_2]:
                continue
            else:
                pos_1 = inverted_idx[word_1][artist, index]
                pos_2 = inverted_idx[word_2][artist, index]
                i = 0
                j = 0

                while i < len(pos_1) and j < len(pos_2):
                    if pos_1[i] > pos_2[j] + proximity:
                        j += 1
                    elif pos_1[i] < pos_2[j] - proximity:
                        i += 1
                    else:
                        res.append((artist, index))
                        break
    return res


def phrase_search(inverted_idx, query):
    is_not = False
    if query.find('#') != -1:
        start = query.index('(')
        end = query.index(')')
        proximity = int(query[query.index('#') + 1: start])
        p = query[start + 1: end].replace(',', ' ').split()
        return proximity_search(inverted_idx, p[0], p[1], proximity)
    elif query.find('NOT') != -1:
        query = query.replace('NOT', '')
        is_not = True

    words = query.replace('"', ' ').split()

    if len(words) == 1:
        res = word_search(inverted_idx, words[0])
    else:
        res = word_search(inverted_idx, words[0])
        words = [stem(word.lower()) for word in words]
        for k in range(0, len(words) - 1):
            res_k = []
            if words[k] in inverted_idx and words[k + 1] in inverted_idx:
                for (artist, index) in inverted_idx[words[k]]:
                    if (artist, index) not in inverted_idx[words[k + 1]]:
                        continue
                    else:
                        pos_1 = inverted_idx[words[k]][artist, index]
                        pos_2 = inverted_idx[words[k + 1]][artist, index]
                        i = 0
                        j = 0

                        while i < len(pos_1) and j < len(pos_2):
                            if pos_1[i] < pos_2[j]:
                                if pos_1[i] + 1 == pos_2[j]:
                                    res_k.append((artist, index))
                                    break
                                else:
                                    i += 1
                            elif pos_1[i] > pos_2[j]:
                                j += 1

            res = op_and(res, res_k)

    if is_not:
        res = op_not(res, inverted_idx)
    return res


def evaluate(query):
    q = re.split(" (AND|OR) ", query)
    res = []
    for elem in q:
        if elem[0] == '(' and elem[-1] == ')':
            res.append(elem[0])
            res.append(elem[1:-1])
            res.append(elem[-1])
        elif elem[0] == '(':
            res.append(elem[0])
            res.append(elem[1:])
        elif elem[-1] == ')':
            res.append(elem[:-1])
            res.append(elem[-1])
        else:
            res.append(elem)
    return res


def boolean_search(inverted_idx, query):
    def is_op(t):
        if t in ['AND', 'OR', '(', ')']:
            return True
        else:
            return False

    res = list()
    docs_stack = []
    ops_stack = []
    for i in range(len(query)):
        if query[i] == '(':
            ops_stack.append(query[i])
        elif not is_op(query[i]):
            docs_list = phrase_search(inverted_idx, query[i])
            docs_stack.append(docs_list)
        elif query[i] == ')':
            while len(ops_stack) != 0 and ops_stack[-1] != '(':
                docs_list1 = docs_stack.pop()
                docs_list2 = docs_stack.pop()
                op = ops_stack.pop()
                new_docs = []
                if op == 'OR':
                    new_docs = op_or(docs_list1, docs_list2)
                elif op == 'AND':
                    new_docs = op_and(docs_list1, docs_list2)
                docs_stack.append(new_docs)
            ops_stack.pop()
        else:
            ops_stack.append(query[i])

    while len(ops_stack) != 0:
        docs_list1 = docs_stack.pop()
        docs_list2 = docs_stack.pop()
        op = ops_stack.pop()
        new_docs = []
        if op == 'OR':
            new_docs = op_or(docs_list1, docs_list2)
        elif op == 'AND':
            new_docs = op_and(docs_list1, docs_list2)
        docs_stack.append(new_docs)
    res = docs_stack[-1]
    return res


def rank(query, inverted_index):
    tfidf = defaultdict(int)
    words = preprocessing(query)
    songs = set()
    for word in inverted_index:
        for (artist, index) in inverted_index[word]:
            songs.add((artist, index))
    songs_num = len(songs)
    for word in words:
        tf_dict = {}
        if word not in inverted_index:
            continue
        else:
            for (artist, index) in inverted_index[word]:
                tf_dict[artist, index] = len(inverted_index[word][artist, index])

            df = len(inverted_index[word])
            for (artist, index) in tf_dict:
                tfidf[artist, index] += (1 + log10(tf_dict[artist, index])) * log10(songs_num / df)

    sorted_tfidf = sorted(tfidf.items(), key=lambda x: x[1], reverse=True)
    return sorted_tfidf


def rank_BM25(query, docs, inv_idx_docs, idx_docs):
    tf = defaultdict(float)
    idf = defaultdict(float)
    tfidf = defaultdict(float)
    words = preprocessing(query)
    k1 = 1.5
    b = 0.75

    songs_num = len(docs)
    docs_len = {}
    avg_len = 0.0
    for (artist, index) in idx_docs:
        docs_len[artist, index] = 0
        for word in idx_docs[artist, index]:
            docs_len[artist, index] += idx_docs[artist, index][word]

        avg_len += docs_len[artist, index]
    avg_len /= float(len(docs))

    for word in words:
        if word not in inv_idx_docs:
            continue
        else:
            df = len(inv_idx_docs[word])
            idf[word] = log10((songs_num - df + 0.5) / (df + 0.5))

    for (artist, index) in idx_docs:
        for word in words:
            if word not in idx_docs[artist, index]:
                continue
            else:
                tf[word] = idx_docs[artist, index][word] / docs_len[artist, index]
                K = k1 * (1 - b + b * docs_len[artist, index] / avg_len)
                tfidf[artist, index] += tf[word] * (k1 + 1) / (tf[word] + K) * idf[word]
    sorted_tfidf = sorted(tfidf.items(), key=lambda x: x[1], reverse=True)
    return sorted_tfidf


def find_keyword(query, lyrics):
    res = ""
    words = evaluate(query)
    if len(words) == 1:
        words = words[0].split(' ')
    words = [word.lower() for word in words]
    s = lyrics.lower()

    if s.find(query) != -1:
        pos = s.find(query)
        start = pos
        end = pos
        while s[start: start + 1] != '\n' and start > 0:
            start -= 1
        while s[end: end + 1] != '\n' and end < len(s) - 1:
            end += 1
        res = lyrics[start: end + 1]
    else:
        locations = set()
        for word in words:
            if s.find(word) != -1:
                pos = s.find(word)
                start = pos
                end = pos
                while s[start: start + 1] != '\n' and start > 0:
                    start -= 1
                while s[end: end + 1] != '\n' and end < len(s) - 1:
                    end += 1
                locations.add((start, end))
        for start, end in locations:
            res += lyrics[start + 1: end + 1] + ' '
    return res


def find_stem_keyword(query, lyrics):
    res = ""
    words = evaluate(query)
    if len(words) == 1:
        words = words[0].split(' ')
    words = [word.lower() for word in words]
    s = lyrics.lower()

    if s.find(stem(query)) != -1:
        pos = s.find(stem(query))
        start = pos
        end = pos
        while s[start: start + 1] != '\n' and start > 0:
            start -= 1
        while s[end: end + 1] != '\n' and end < len(s) - 1:
            end += 1
        res = lyrics[start: end + 1]
    else:
        locations = set()
        for word in words:
            if s.find(word) != -1:
                pos = s.find(word)
                start = pos
                end = pos
                while s[start: start + 1] != '\n' and start > 0:
                    start -= 1
                while s[end: end + 1] != '\n' and end < len(s) - 1:
                    end += 1
                locations.add((start, end))
            elif s.find(stem(word)) != -1:
                pos = s.find(stem(word))
                start = pos
                end = pos
                while s[start: start + 1] != '\n' and start > 0:
                    start -= 1
                while s[end: end + 1] != '\n' and end < len(s) - 1:
                    end += 1
                locations.add((start, end))
        for start, end in locations:
            res += lyrics[start + 1: end + 1] + ' '
    return res


class Algorithm:

    def __init__(self):
        self.title, self.artist, self.album, self.lyrics, self.texts, self.date, self.title_reverse_indexer, self.artist_reverse_indexer, self.album_reverse_indexer, self.lyrics_reverse_indexer, self.reverse_indexer, self.title_words_count, self.artist_words_count, self.album_words_count, self.lyrics_words_count, self.words_count, self.artist_link, self.album_link, self.link = self.input_data()

    @staticmethod
    def input_data():
        with open('./app/data/pickle/title.pickle', 'rb') as f:
            title = pickle.load(f)
        with open('./app/data/pickle/artist.pickle', 'rb') as f:
            artist = pickle.load(f)
        with open('./app/data/pickle/album.pickle', 'rb') as f:
            album = pickle.load(f)
        with open('./app/data/pickle/lyrics.pickle', 'rb') as f:
            lyrics = pickle.load(f)
        with open('./app/data/pickle/texts.pickle', 'rb') as f:
            texts = pickle.load(f)

        with open('./app/data/pickle/title_reverse_index.pickle', 'rb') as f:
            title_reverse_indexer = pickle.load(f)
        with open('./app/data/pickle/artist_reverse_index.pickle', 'rb') as f:
            artist_reverse_indexer = pickle.load(f)
        with open('./app/data/pickle/album_reverse_index.pickle', 'rb') as f:
            album_reverse_indexer = pickle.load(f)
        with open('./app/data/pickle/lyrics_reverse_index.pickle', 'rb') as f:
            lyrics_reverse_indexer = pickle.load(f)
        with open('./app/data/pickle/reverse_index.pickle', 'rb') as f:
            reverse_indexer = pickle.load(f)

        with open('./app/data/pickle/title_words_count.pickle', 'rb') as f:
            title_words_count = pickle.load(f)
        with open('./app/data/pickle/artist_words_count.pickle', 'rb') as f:
            artist_words_count = pickle.load(f)
        with open('./app/data/pickle/album_words_count.pickle', 'rb') as f:
            album_words_count = pickle.load(f)
        with open('./app/data/pickle/lyrics_words_count.pickle', 'rb') as f:
            lyrics_words_count = pickle.load(f)
        with open('./app/data/pickle/words_count.pickle', 'rb') as f:
            words_count = pickle.load(f)

        with open('./app/data/pickle/date.pickle', 'rb') as f:
            date = pickle.load(f)
        with open('./app/data/pickle/artist_link.pickle', 'rb') as f:
            artist_link = pickle.load(f)
        with open('./app/data/pickle/album_link.pickle', 'rb') as f:
            album_link = pickle.load(f)
        with open('./app/data/pickle/link.pickle', 'rb') as f:
            link = pickle.load(f)

        return title, artist, album, lyrics, texts, date, title_reverse_indexer, artist_reverse_indexer, album_reverse_indexer, lyrics_reverse_indexer, reverse_indexer, title_words_count, artist_words_count, album_words_count, lyrics_words_count, words_count, artist_link, album_link, link

    def algorithm(self, choice, query):
        res = dict()
        i = 1
        p = re.split(r' (AND|OR) ', query)

        if choice == 'song':
            if len(p) == 1:
                search_result = phrase_search(self.title_reverse_indexer, query)
                tfidf = rank_BM25(query, self.title, self.title_reverse_indexer, self.title_words_count)
                backup, backup_1, backup_2, backup_3, backup_4 = [], [], [], [], []
                for (artist, index), _ in tfidf:
                    if (artist, index) in search_result:
                        if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                                self.date[artist, index] != '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            res[i] = line
                            i += 1
                        elif self.album[artist, index] != 'Unreleased Songs':
                            if self.album[artist, index] == '' or self.date[artist, index] == '':
                                line = [self.title[artist, index], artist, self.album[artist, index],
                                        self.date[artist, index],
                                        self.link[artist, index], self.artist_link[artist, index],
                                        self.album_link[artist, index]]
                                backup_1.append(line)
                        else:
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_2.append(line)
                    else:
                        if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                                self.date[artist, index] != '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_1.append(line)
                        elif self.album[artist, index] != 'Unreleased Songs':
                            if self.album[artist, index] == '' or self.date[artist, index] == '':
                                line = [self.title[artist, index], artist, self.album[artist, index],
                                        self.date[artist, index],
                                        self.link[artist, index], self.artist_link[artist, index],
                                        self.album_link[artist, index]]
                                backup_3.append(line)
                        else:
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_4.append(line)
                add_list = backup + backup_1 + backup_3 + backup_2 + backup_4
                for k in range(len(add_list)):
                    res[i] = add_list[k]
                    i += 1

            else:
                query = evaluate(query)
                search_result = boolean_search(self.title_reverse_indexer, query)
                backup_1, backup_2 = [], []
                for (artist, index) in search_result:
                    if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                            self.date[artist, index] != '':
                        line = [self.title[artist, index], artist, self.album[artist, index],
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index],
                                self.album_link[artist, index]]
                        res[i] = line
                        i += 1
                    elif self.album[artist, index] != 'Unreleased Songs':
                        if self.album[artist, index] == '' or self.date[artist, index] == '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_1.append(line)
                    else:
                        line = [self.title[artist, index], artist, self.album[artist, index],
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index],
                                self.album_link[artist, index]]
                        backup_2.append(line)
                add_list = backup_1 + backup_2
                for k in range(len(add_list)):
                    res[i] = add_list[k]
                    i += 1

        elif choice == 'artist':
            if len(p) == 1:
                search_result = phrase_search(self.artist_reverse_indexer, query)
                tfidf = rank_BM25(query, self.artist, self.artist_reverse_indexer, self.artist_words_count)
                backup, backup_1, backup_2, backup_3, backup_4 = [], [], [], [], []
                for (artist, index), _ in tfidf:
                    if (artist, index) in search_result:
                        if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                                self.date[artist, index] != '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            res[i] = line
                            i += 1
                        elif self.album[artist, index] != 'Unreleased Songs':
                            if self.album[artist, index] == '' or self.date[artist, index] == '':
                                line = [self.title[artist, index], artist, self.album[artist, index],
                                        self.date[artist, index],
                                        self.link[artist, index], self.artist_link[artist, index],
                                        self.album_link[artist, index]]
                                backup_1.append(line)
                        else:
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_2.append(line)
                    else:
                        if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                                self.date[artist, index] != '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup.append(line)
                        elif self.album[artist, index] != 'Unreleased Songs':
                            if self.album[artist, index] == '' or self.date[artist, index] == '':
                                line = [self.title[artist, index], artist, self.album[artist, index],
                                        self.date[artist, index],
                                        self.link[artist, index], self.artist_link[artist, index],
                                        self.album_link[artist, index]]
                                backup_3.append(line)
                        else:
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_4.append(line)
                add_list = backup + backup_1 + backup_3 + backup_2 + backup_4
                for k in range(len(add_list)):
                    res[i] = add_list[k]
                    i += 1
            else:
                query = evaluate(query)
                search_result = boolean_search(self.artist_reverse_indexer, query)
                backup_1, backup_2 = [], []
                for (artist, index) in search_result:
                    if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                            self.date[artist, index] != '':
                        line = [self.title[artist, index], artist, self.album[artist, index],
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index],
                                self.album_link[artist, index]]
                        res[i] = line
                        i += 1
                    elif self.album[artist, index] != 'Unreleased Songs':
                        if self.album[artist, index] == '' or self.date[artist, index] == '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_1.append(line)
                    else:
                        line = [self.title[artist, index], artist, self.album[artist, index],
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index],
                                self.album_link[artist, index]]
                        backup_2.append(line)
                add_list = backup_1 + backup_2
                for k in range(len(add_list)):
                    res[i] = add_list[k]
                    i += 1

        elif choice == 'album':
            if len(p) == 1:
                search_result = phrase_search(self.album_reverse_indexer, query)
                tfidf = rank_BM25(query, self.album, self.album_reverse_indexer, self.album_words_count)
                backup, backup_1, backup_2, backup_3, backup_4 = [], [], [], [], []
                for (artist, index), _ in tfidf:
                    if (artist, index) in search_result:
                        if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                                self.date[artist, index] != '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            res[i] = line
                            i += 1
                        elif self.album[artist, index] != 'Unreleased Songs':
                            if self.album[artist, index] == '' or self.date[artist, index] == '':
                                line = [self.title[artist, index], artist, self.album[artist, index],
                                        self.date[artist, index],
                                        self.link[artist, index], self.artist_link[artist, index],
                                        self.album_link[artist, index]]
                                backup_1.append(line)
                        else:
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_2.append(line)
                    else:
                        if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                                self.date[artist, index] != '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup.append(line)
                        elif self.album[artist, index] != 'Unreleased Songs':
                            if self.album[artist, index] == '' or self.date[artist, index] == '':
                                line = [self.title[artist, index], artist, self.album[artist, index],
                                        self.date[artist, index],
                                        self.link[artist, index], self.artist_link[artist, index],
                                        self.album_link[artist, index]]
                                backup_3.append(line)
                        else:
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_4.append(line)

                add_list = backup + backup_1 + backup_3 + backup_2 + backup_4
                for k in range(len(add_list)):
                    res[i] = add_list[k]
                    i += 1
            else:
                query = evaluate(query)
                search_result = boolean_search(self.album_reverse_indexer, query)
                backup_1, backup_2 = [], []
                for (artist, index) in search_result:
                    if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                            self.date[artist, index] != '':
                        line = [self.title[artist, index], artist, self.album[artist, index],
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index],
                                self.album_link[artist, index]]
                        res[i] = line
                        i += 1
                    elif self.album[artist, index] != 'Unreleased Songs':
                        if self.album[artist, index] == '' or self.date[artist, index] == '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_1.append(line)
                    else:
                        line = [self.title[artist, index], artist, self.album[artist, index],
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index],
                                self.album_link[artist, index]]
                        backup_2.append(line)
                add_list = backup_1 + backup_2
                for k in range(len(add_list)):
                    res[i] = add_list[k]
                    i += 1

        elif choice == 'lyrics':
            if len(p) == 1:
                search_result = phrase_search(self.lyrics_reverse_indexer, query)
                tfidf = rank_BM25(query, self.lyrics, self.lyrics_reverse_indexer, self.lyrics_words_count)
                for (artist, index), _ in tfidf:
                    if (artist, index) in search_result:
                        if find_keyword(query, self.lyrics[artist, index]) != '':
                            line = [find_keyword(query, self.lyrics[artist, index]), self.title[artist, index], artist,
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index]]
                            res[i] = line
                            i += 1
                for (artist, index), _ in tfidf:
                    if (artist, index) not in search_result:
                        if find_keyword(query, self.lyrics[artist, index]) != '':
                            line = [find_keyword(query, self.lyrics[artist, index]), self.title[artist, index], artist,
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index]]
                            res[i] = line
                            i += 1
                for (artist, index), _ in tfidf:
                    if (artist, index) in search_result:
                        if find_keyword(query, self.lyrics[artist, index]) == '':
                            line = [find_stem_keyword(query, self.lyrics[artist, index]), self.title[artist, index],
                                    artist,
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index]]
                            res[i] = line
                            i += 1
                for (artist, index), _ in tfidf:
                    if (artist, index) not in search_result:
                        if find_keyword(query, self.lyrics[artist, index]) == '':
                            line = [find_stem_keyword(query, self.lyrics[artist, index]), self.title[artist, index],
                                    artist,
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index]]
                            res[i] = line
                            i += 1
            else:
                q = query
                query = evaluate(query)
                search_result = boolean_search(self.lyrics_reverse_indexer, query)
                for (artist, index) in search_result:
                    if find_keyword(query, self.lyrics[artist, index]) != '':
                        line = [find_keyword(q, self.lyrics[artist, index]), self.title[artist, index], artist,
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index]]
                        res[i] = line
                        i += 1
                for (artist, index) in search_result:
                    if find_keyword(query, self.lyrics[artist, index]) == '':
                        line = [find_stem_keyword(query, self.lyrics[artist, index]), self.title[artist, index], artist,
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index]]
                        res[i] = line
                        i += 1
        else:
            if len(p) == 1:
                search_result = phrase_search(self.title_reverse_indexer, query)
                tfidf = rank_BM25(query, self.texts, self.reverse_indexer, self.words_count)
                backup, backup_1, backup_2, backup_3, backup_4 = [], [], [], [], []
                for (artist, index), _ in tfidf:
                    if (artist, index) in search_result:
                        if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                                self.date[artist, index] != '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            res[i] = line
                            i += 1
                        elif self.album[artist, index] != 'Unreleased Songs':
                            if self.album[artist, index] == '' or self.date[artist, index] == '':
                                line = [self.title[artist, index], artist, self.album[artist, index],
                                        self.date[artist, index],
                                        self.link[artist, index], self.artist_link[artist, index],
                                        self.album_link[artist, index]]
                                backup_1.append(line)
                        else:
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_2.append(line)
                    else:
                        if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                                self.date[artist, index] != '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup.append(line)
                        elif self.album[artist, index] != 'Unreleased Songs':
                            if self.album[artist, index] == '' or self.date[artist, index] == '':
                                line = [self.title[artist, index], artist, self.album[artist, index],
                                        self.date[artist, index],
                                        self.link[artist, index], self.artist_link[artist, index],
                                        self.album_link[artist, index]]
                                backup_3.append(line)
                        else:
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_4.append(line)

                add_list = backup + backup_1 + backup_3 + backup_2 + backup_4
                for k in range(len(add_list)):
                    res[i] = add_list[k]
                    i += 1
            else:
                q = query
                query = evaluate(query)
                search_result = boolean_search(self.reverse_indexer, query)
                backup_1, backup_2 = [], []
                for (artist, index) in search_result:
                    if self.album[artist, index] != 'Unreleased Songs' and self.album[artist, index] != '' and \
                            self.date[artist, index] != '':
                        line = [self.title[artist, index], artist, self.album[artist, index],
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index],
                                self.album_link[artist, index]]
                        res[i] = line
                        i += 1
                    elif self.album[artist, index] != 'Unreleased Songs':
                        if self.album[artist, index] == '' or self.date[artist, index] == '':
                            line = [self.title[artist, index], artist, self.album[artist, index],
                                    self.date[artist, index],
                                    self.link[artist, index], self.artist_link[artist, index],
                                    self.album_link[artist, index]]
                            backup_1.append(line)
                    else:
                        line = [self.title[artist, index], artist, self.album[artist, index],
                                self.date[artist, index],
                                self.link[artist, index], self.artist_link[artist, index],
                                self.album_link[artist, index]]
                        backup_2.append(line)
                add_list = backup_1 + backup_2
                for k in range(len(add_list)):
                    res[i] = add_list[k]
                    i += 1

        return res
