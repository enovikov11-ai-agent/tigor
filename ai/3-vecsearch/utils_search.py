# General
import json
import array
import hashlib
import humanize
import os
import time
import math
import sys

# Data
import numpy as np
import pickle

# AI
import openai
import openai_api_key
import tiktoken
import faiss

# Other
from tqdm import tqdm
import lmdb



def normalize_text(src_text):
    if isinstance(src_text, str):
        return src_text
    
    text = ""

    for item in src_text:
        text += item if isinstance(item, str) else item['text']
            
    return text

def hash_key(key):
    m = hashlib.sha256()
    m.update(key.encode('utf-8'))
    return m.digest()

class Format:
    def short(msg):
        return f"{msg.get('from', '')}: " + normalize_text(msg['text']).replace('\n', '\t')
    
    def long(msg):
        return f"{msg['from']}, [{msg['date']}]:\n{normalize_text(msg['text'])}"
    
    def json_short(msg):
        return json.dumps({'from': msg['from'], 'text': normalize_text(msg['text'])})

    def json_long(msg):
        return json.dumps({'text': normalize_text(msg['text']), 'from': msg['from'], 'date': msg['date']})

class Combine:
    def plain(messages):
        return [[x] for x in range(len(messages))]
    
    def consecutive(count):
        def combiner(messages):
            ids = list(range(len(messages)))
            combinations = []
            
            for i in range(0, len(ids), count):
                combinations.append(ids[i:i + count])
            
            return combinations
        return combiner
    
    def user_consec(count):
        raise Exception("Not implemented yet")

class Display:
    def default(messages, ids_groups, scores):
        return "\n\n".join(["\n".join([Format.short(messages[id]) for id in ids]) for ids in ids_groups])
    
    def debug(messages, ids, scores):
        return (messages, ids, scores)

class Mapper:
    def messages_only(msgs):
        return [m for m in msgs if m['type'] == 'message']
    
    def forwarded_as_sent(msgs):
        for msg in msgs:
            msg.pop('from')
            msg.pop('from_id')
            if 'forwarded_from' in msg:
                msg['from'] = msg.pop('forwarded_from')
        
        return msgs
    
    def text_only(msgs):
        return [m for m in msgs if 'text' in m and 'from' in m and m['text'] != '']
    
    def rename(name_from, name_to):
        def r(msgs):
            for msg in msgs:
                if msg.get('from') == name_from:
                    msg['from'] = name_to
            return msgs
        return r

class Index:
    def __init__(self, messages, mappers = [], format = Format.short, combines = [Combine.plain], max_tokens = 8191, db_name = 'cache.db'):
        encoding = tiktoken.get_encoding("cl100k_base")
        self.cache_db = lmdb.open(db_name, map_size=int(1e12), max_dbs=1000)
        self.db_name = db_name

        self._messages = messages.copy()
        for mapper in mappers:
            self._messages = mapper(self._messages)
        _formatted_messages = [format(m) for m in self._messages]
        _lens = [len(encoding.encode(m)) for m in _formatted_messages]
        
        self._combinations = []
        for combine in combines:
            self._combinations += combine(self._messages)
        
        _combined_messages = ["\n\n".join([_formatted_messages[id] for id in ids]) for ids in self._combinations]
        _combined_lens = [sum([_lens[id]+1 for id in ids]) for ids in self._combinations]
        self._combined_messages = [(msg, ln) for (msg, ln) in list(zip(_combined_messages, _combined_lens)) if ln <= max_tokens]
        
        with self.cache_db.begin(write=False) as txn:
            self._calc_values = [(msg, ln) for (msg, ln) in self._combined_messages if txn.get(hash_key(msg)) is None]

        if len(self._calc_values) == 0:
            self.build()

    def __repr__(self):
        tokens_count = sum([x[1] for x in (self._combined_messages if len(self._calc_values) == 0 else self._calc_values)])
        m = tokens_count / 1e6

        return ("Index" if len(self._calc_values) == 0 else "Update") + \
            f" complexity tokens(M): {m:.2f}, price: ${0.1 * m:.2f}, time: {humanize.naturaldelta(70 * m)}"

    def build(self):
        batches = []
        current_batch = []
        total_length = 0
        max_length = 32000

        for (value, value_length) in self._calc_values:
            if total_length + value_length > max_length:
                batches.append(current_batch)
                current_batch = []
                total_length = 0
            
            current_batch.append(value)
            total_length += value_length

        if current_batch:
            batches.append(current_batch)
        
        if batches:        
            for batch in tqdm(batches):
                embeddings = [m['embedding'] for m in openai.Embedding.create(input=batch, model="text-embedding-ada-002")['data']]
                with self.cache_db.begin(write=True) as txn:
                    for key, value in zip(batch, embeddings):
                        txn.put(hash_key(key), array.array('f', value).tobytes())
    
        with self.cache_db.begin(write=False) as txn:
            _embeddings = np.array([np.array(array.array('f', txn.get(hash_key(value)))) for value, ln in self._combined_messages])
        
        self._index = faiss.IndexFlatL2(_embeddings.shape[1])
        self._index.add(_embeddings)
        self._calc_values = []

    def search(self, query, display = Display.default, count = 3):
        if len(self._calc_values) != 0:
            return "Outdated index, run chat.build()"
        
        query_vector = np.array(openai.Embedding.create(input=[query], model="text-embedding-ada-002")['data'][0]['embedding'])
        scores, ids = self._index.search(query_vector.reshape(1, -1), count)
        
        return display(self._messages, [self._combinations[id] for id in list(ids[0])], list(scores[0]))
    
    def export(self, name):
        faiss.write_index(self._index, f"./model/{name}.faiss")

        with open(f"./model/{name}.json", 'w', encoding='utf-8') as f:
            json.dump([x[0] for x in self._combined_messages], f, ensure_ascii=False)
    
    def print_db_stats():
        size = os.path.getsize(f"./{self.db_name}/data.mdb")
        
        with cache_db.begin() as txn:
            with txn.cursor() as cursor:
                count = len(list(cursor))
        
        print(f"Count of lines in the database: {humanize.intcomma(count)}")
        print(f"Size of the database: {humanize.naturalsize(size)}")
        print(f"Size per item: {humanize.naturalsize(size / count)} per item")

class Chat(Index):
    def __init__(self, name, **kwargs):
        super().__init__(messages = json.load(open(f'./chats/{name}.json', 'r'))['messages'], **kwargs)

class Zchat(Chat):
    def __init__(self, **kwargs):
        super().__init__(
            name = "chat1", 
            mappers = [
                Mapper.messages_only,
                Mapper.forwarded_as_sent,
                Mapper.text_only,
                Mapper.rename('123', '456')
            ],
            **kwargs
        )

class Vchat(Chat):
    def __init__(self, **kwargs):
        super().__init__(
            name = "chat4",
            **kwargs
        )