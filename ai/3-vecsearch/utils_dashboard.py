# General
import os
import json
import datetime
import math
import array
import hashlib
import humanize
import unicodedata

# Data
import pandas as pd
import numpy as np
import pickle

# AI
import openai
import openai_api_key
import tiktoken
import faiss

# Other

from tqdm import tqdm
import pytz
import lmdb
import matplotlib.pyplot as plt

def reduce_keys(messages, keep_keys = ['date', 'id', 'text', 'from', 'poll', 'via_bot']):
    """
    Remove the unwanted keys from the messages.

    Args:
    messages (list): A list of dictionaries where each dictionary represents a message with different keys.
    keep_keys (list): A list of keys to keep in messages, default keys are 'date', 'id', 'text', 'from', 'poll', 'via_bot'

    Returns:
    (list): A list of dictionaries where each dictionary is message having only required keys.
    """

    return [{key: msg[key] for key in keep_keys if key in msg} for msg in messages]

def is_worktime(item):
    """
    Check if the time is worktime or not based on "Europe/Moscow" timezone.

    Args:
    item (dict): A dictionary with message details, 'date_unixtime' key should exist in the dictionary.

    Returns:
    (bool): True if the time is worktime, False otherwise.
    """

    dt = datetime.datetime.fromtimestamp(int(item['date_unixtime']), pytz.timezone('Europe/Moscow'))
    return 0 <= dt.weekday() <= 4 and 10 <= dt.hour < 19

def get_text(messages):
    """
    Returns the list of messages where text is not empty and message contains 'from' key.

    Args:
    messages (list): A list of dictionaries where each dictionary is a message.

    Returns:
    (list): A list of dictionaries where each dictionary is a message with non-empty 'text' and having 'from' key.
    """

    return [m for m in messages if m['text'] != '' and 'from' in m]

def flatten_list(nested_list):
    """
    Flattens a nested list.

    Args:
    nested_list (list): A list to flatten, it can contain other lists as elements.

    Returns:
    (list): A flat list containing all elements of nested list.
    """

    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list

def get_embeddings(values):
    """
    Get embeddings for each value in the values list.

    Args:
    values (list): A list of values.

    Returns:
    (list): A list of embeddings, where each embedding is in form of a list.
    """

    def hash_key(key):
        m = hashlib.sha256()
        m.update(key.encode('utf-8'))
        return m.digest()

    with cache_db.begin(write=False) as txn:
        calc_values = [v for v in values if txn.get(hash_key(v)) is None]
    batches = []
    current_batch = []
    total_length = 0
    max_length = 32000

    for value in calc_values:
        value_length = len(encoding.encode(value))
        
        if total_length + value_length > max_length:
            batches.append(current_batch)
            current_batch = []
            total_length = 0
        
        current_batch.append(value)
        total_length += value_length
    
    if current_batch:
        batches.append(current_batch)

    if batches:        
        for batch in tqdm(batches, leave=False):
            embeddings = [m['embedding'] for m in openai.Embedding.create(input=batch, model="text-embedding-ada-002")['data']]
            with cache_db.begin(write=True) as txn:
                for key, value in zip(batch, embeddings):
                    txn.put(hash_key(key), array.array('f', value).tobytes())

    with cache_db.begin(write=False) as txn:
        return [list(array.array('f', txn.get(hash_key(value)))) for value in values]    

def make_search(values):
    """
    Make a function to get similar entities for a query.

    Args:
    values (list): A list of values for which embeddings are calculated.

    Returns:
    (function): A function where when a query is given returns the similar entities for the query.
    """

    embeddings = np.array(get_embeddings(values))
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    
    def search(query, count = 5):
        query_vector = np.array(openai.Embedding.create(input=[query], model="text-embedding-ada-002")['data'][0]['embedding'])
        similarities, ids = index.search(query_vector.reshape(1, -1), count)
        return (list(similarities[0]), list(ids[0]))
    
    return search

def get_combinations(messages, max_next = 10, max_self = 10):
    """
    Get all possible combinations of messages.

    Args:
    messages (list): A list of dictionaries, where each dictionary represents a message.
    max_next (int): Maximum number of next messages to consider for getting combination of messages, default is 10.
    max_self (int): Maximum number of messages of the same 'from' key to consider for getting combination of messages, default is 10.

    Returns:
    (list): A list of lists, where each list represents the ids of messages in a combination.
    """

    def deduplicate(arr):
        seen = set()
        unique_arrays = []
        for a in arr:
            serialized_a = tuple(a)
            if serialized_a not in seen:
                unique_arrays.append(a)
                seen.add(serialized_a)
        return unique_arrays
    
    names = [m.get('from') for m in messages]
    ids = list(range(len(messages)))
    next1 = [None if id == len(messages) - 1 else id + 1 for id in ids]
    next2 = [None for id in ids]
    
    last_seen = {}
    for id in ids:
        name = names[id]
        if name in last_seen:
            next2[last_seen[name]] = id
        last_seen[name] = id
    
    groups = []
    
    for id in ids:
        groups.append([id])
        
        group1 = [id]
        for i in range(max_next):
            n1 = next1[group1[-1]]

            if n1 is None:
                break
            
            group1.append(n1)
            groups.append(group1.copy())
                
        group2 = [id]
        for i in range(max_self):
            n2 = next2[group2[-1]]
            
            if n2 is None:
                break
                
            group2.append(n2)
            groups.append(group2.copy())
    
    return deduplicate(groups)

def index_building_complexity(messages):
    """
    Evaluate the building complexity of index.

    Args:
    messages (list): A list of dictionaries where each dictionary is a message.

    Returns:
    (pandas.DataFrame): A pandas DataFrame containing statistics related to building complexity of index.
    """

    base = get_combinations(messages, 0, 0)
    other = get_combinations(messages, 10, 10)
    
    ids_values = base + other
    search_values = ["\n\n".join([format_chat_message(messages[id], short=False) for id in ids]) for ids in base] + \
        ["\n".join([format_chat_message(messages[id], short=True) for id in ids]) for ids in other]
        
    encoding = tiktoken.get_encoding("cl100k_base")
    
    lens = []
    
    for i in tqdm(range(math.ceil(len(search_values) / 1000))):
        values = search_values[1000 * i:1000 * (i + 1)]
        lens += [len(encoding.encode(value)) for value in values] 
    
    msgs_lens = [len(m) for m in ids_values]
    
    ln_zip = list(zip(lens, msgs_lens))
    
    msgs_limits = [x + 1 for x in list(range(11))]
    kk_tokens_used = [sum([x[0] for x in ln_zip if x[1] <= limit]) / 1e6 for limit in msgs_limits]
    price_usd = [x * 0.1 for x in kk_tokens_used]
    cache_build_time_min = [x * 3 for x in kk_tokens_used]
    
    pd.DataFrame(list(zip(msgs_limits, kk_tokens_used, price_usd, cache_build_time_min)), 
                 columns=["max messages sticked", "tokens (kk)", "price $", "cache build time min"])

def get_chat(name, forwards=False):
    """
    Get all messages of a chat by loading the chat from a JSON file.

    Args:
    name (str): Name of the chat (.json file name from which chat is loaded).
    forwards (bool): If True, messages are considered from 'forwarded_from' key. If False(default), messages are considered from 'from' key.

    Returns:
    (list): A list of dictionaries where each dictionary represents a message of the chat.
    """

    chat = json.load(open(f'./chats/{name}.json', 'r'))
    messages = [m for m in chat['messages'] if m['type'] == 'message']

    if forwards:
        for msg in messages:
            msg.pop('from')
            msg.pop('from_id')
            if 'forwarded_from' in msg:
                msg['from'] = msg.pop('forwarded_from')
    
    for msg in messages:
        if msg.get('from') == '123':
            msg['from'] = '456'

    return messages

def format_chat_message(msg, short=False):
    """
    Format the chat message into a particular format.

    Args:
    msg (dict): A dictionary representing a chat message.
    short (bool): If True, return a short version of formatted message. Else, return a long version. Default is False.

    Returns:
    (str): The chat message formatted into a particular format.
    """

    if isinstance(msg['text'], list):
        text = ""

        for item in msg['text']:
            text += item if isinstance(item, str) else item['text']
    else:
        text = msg['text']
    
    return f"{msg['from']}: " + text.replace('\n', '\t') if short else f"{msg['from']}, [{msg['date']}]:\n{text}"

def get_key_stats(messages):
    """
    Get statistics related to keys in messages.

    Args:
    messages (list): A list of dictionaries where each dictionary is a message.

    Returns:
    (list): A list of tuples where each tuple contains a key, its count and an example value of the key from messages.
    """

    msgs = flatten_list([list(m.keys()) for m in messages])
    keys, cnts = np.unique(np.array(msgs), return_counts=True)

    examples = [ [m for m in messages if (k in m)][0][k] for k in keys]
    
    return sorted(list(zip(keys, cnts, examples)), key=lambda x: x[1], reverse=True)

def uniqs(items):
    """
    Get the unique statistics of items.

    Args:
    items (list): A list of items to get statistics.

    Returns:
    (pandas.DataFrame): A pandas DataFrame containing the unique statistics of items.
    """

    array = [x for x in items if x is not None]
    keys, cnts = np.unique(np.array(array), return_counts=True)
    percents = np.round((cnts / cnts.sum()) * 100, 2)
    percents_all = np.round((cnts / len(array)) * 100, 2)

    stats = sorted(list(zip(keys, cnts, percents, percents_all)), key=lambda x: x[1], reverse=True)
    return pd.DataFrame(stats[0:20], columns=["item", "count", "%", "% of all"])

def token_limit_efficiency(messages, limit = 8191):
    """
    Calculates the efficiency of different token limits for a set of chat messages.
    
    Args:
    - messages (list): List of chat messages to analyze.
    - limit (int): Token limit for the analysis. Default is 8191.
    
    Returns:
    - DataFrame: A Pandas DataFrame showing token limit efficiency stats.
    
    Outputs:
    - Prints the count and percentage of oversized messages.
    """
    
    encoding = tiktoken.get_encoding("cl100k_base")
    lens_orig = [len(encoding.encode(format_chat_message(m, short = True))) for m in messages] 

    quantiles = [0.001, 0.005, 0.01, 0.02, 0.05]
    lens = [l for l in lens_orig if l <= limit]
    lens.sort()
    total_size = sum(lens)
    efficiencies = []

    for q in quantiles:
        index = int(len(lens) * (1 - q))
        size_limit = lens[index]
        size_saved = sum([x for x in lens if x > size_limit])
    
        efficiencies.append((size_limit, f"{100 * q}%", f"{100 * (size_saved / total_size):.2f}%"))

    oversized_count = len(lens_orig) - len(lens)
    over_perc = 100 * oversized_count / len(lens_orig)
    print(f"Oversized count: {oversized_count} ({over_perc:.2f}%)")
    return pd.DataFrame(efficiencies, columns=["Setting message token limit to", "rejects % of largest messages", "saving % of overall tokens"])

def plot_worktimes(zchat, zchat_work):
    """
    Plots a scatter plot showing the percentage of messages sent during work hours.
    
    Parameters:
    - zchat (list): List of all chat messages.
    - zchat_work (list): List of chat messages sent during work hours.
    
    Outputs:
    - Scatter plot showing message distribution.
    """

    froms = [m.get('from') for m in zchat if m.get('from') is not None]
    froms_work = [m.get('from') for m in zchat_work if m.get('from') is not None]

    keys, cnts = np.unique(np.array(froms), return_counts=True)
    keys_work, cnts_work = np.unique(np.array(froms_work), return_counts=True)

    s1 = pd.Series(cnts, index=keys)
    s2 = pd.Series(cnts_work, index=keys_work)

    merged_df = pd.merge(s1.reset_index(), s2.reset_index(), how='inner', on='index')

    final_keys = merged_df['index'].values
    final_cnts = merged_df['0_x'].values
    final_cnts_work = merged_df['0_y'].values
    percents = 100*final_cnts_work/final_cnts

    stats = sorted(list(zip(final_keys, percents, final_cnts)), key=lambda x: x[1], reverse=True)

    stats = [m for m in stats if m[2] > 400]

    names, x_values, y_values = zip(*stats)

    plt.figure(figsize=(12, 8))
    plt.scatter(x_values, y_values, s=100)

    plt.rcParams['font.family'] = 'DejaVu Sans'

    for i, name in enumerate(names):
        plt.annotate(name, 
                    (x_values[i], y_values[i]), 
                    textcoords="offset points", 
                    xytext=(0,10), 
                    ha='center',
                    bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="azure"))

    plt.xlabel('% сообщений в рабочее время')
    plt.ylabel('Сообщений всего')

    plt.show()

def print_db_stats():
    """
    Get and print the statistics related to database such as database size, count of items and size of each item.

    Returns:
    None
    """
    size = os.path.getsize("./cache.db/data.mdb")
    
    with cache_db.begin() as txn:
        with txn.cursor() as cursor:
            count = len(list(cursor))
    
    print(f"Count of lines in the database: {humanize.intcomma(count)}")
    print(f"Size of the database: {humanize.naturalsize(size)}")
    print(f"Size per item: {humanize.naturalsize(size / count)} per item")

global encoding
encoding = tiktoken.get_encoding("cl100k_base")

global cache_db
cache_db = lmdb.open('cache.db', map_size=int(1e12), max_dbs=1000)

global zchat
zchat = get_chat('chat1', forwards=True)

global zchat_text
zchat_text = get_text(zchat)

global zchat_nospam
zchat_nospam = [m for m in zchat_text if not "ордли" in m['text'] and not "ordle" in m['text'] and not 'via_bot' in m]

# [num + i for num in ids for i in range(-5, 6)]

def split_messages(messages):
    chunks = []
    current_chunk = []
    current_size = 0
    
    for message in messages:
        message_size = len(encoding.encode(message))
        if current_size + message_size > 8190:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_size = 0
            
        current_chunk.append(message)
        current_size += message_size
    
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    
    return chunks


def get_ids(messages):
    mapping = {}

    for item in messages:
        if not 'from_id' in item:
            continue

        mapping[int(item['from_id'].replace('user', ''))] = item['from']

    return dict(sorted(mapping.items()))
