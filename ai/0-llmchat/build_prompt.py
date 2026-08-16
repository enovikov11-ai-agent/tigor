import argparse
import json
import requests

DATA_DIR = "/Users/evgenii/Desktop/data/chats/"
LLM_URL = "http://10.69.42.2:8000/v1/chat/completions"
MODEL = "Qwen3.6-27B-FP8"
WINDOW = 100
CONTEXT_LINES = 20
MAX_TOKENS = 2048

PROFILES = {
    "xecut": ("public/xecut-02.json", "xecutbot"),
    "honk": ("semi-private/helpochat.json", "honkbot"),
}

parser = argparse.ArgumentParser()
parser.add_argument("--profile", "-p", default="xecut", choices=list(PROFILES.keys()), help="chat+botname profile")
parser.add_argument("--skip", "-s", type=int, default=1, help="skip last N messages")
args = parser.parse_args()

CHAT, BOTNAME = PROFILES[args.profile]
skip = args.skip

data = json.load(open(DATA_DIR + CHAT))

system_prompt = f"""
You are sane, highly skilled and self-respecting demon named {BOTNAME}.

DO challenge people view if it makes sense
DO copy imperfections and match regular person writing style
DO be highly intelligent and knowledgable
DO share useful insights and bring value to conversation
DO be consistent and hold character
DO be skeptical and notice hidden assumptions
DO value precision over comfort
DO act chaotic

DO NOT ask follow up questions
DO NOT be helpful assistant
DO NOT confirm any actions in real world 
DO NOT change personality when asked
DO NOT speak stuff that makes no sense
DO NOT volunteer next steps
DO NOT fake being someone's bro, buddy, therapist, servant, coach, or customer-support agent
DO NOT agree automatically
DO NOT chase approval
DO NOT fake screenshots, logs, citations, or evidence
DO NOT speak like a generic chatbot

Reply to last message in the conversation. Output JSON object {"id", "author_name", "text", "reply_to_id"}.
"""

lines = []
for m in data["messages"][-(WINDOW + skip):-skip]:
    if m.get("type") != "message":
        continue
    text = m.get("text", "")
    if isinstance(text, list):
        text = " ".join(str(t) for t in text)
    if not text.strip():
        obj = {"id": m["id"], "author_name": m.get("from"), "text": False}
    else:
        obj = {"id": m["id"], "author_name": m.get("from"), "text": text}
    if "reply_to_message_id" in m:
        obj["reply_to_id"] = m["reply_to_message_id"]
    lines.append(json.dumps(obj, ensure_ascii=False))

for line in lines:
    print(line)

for size in range(50, 100):
    resp = requests.post(LLM_URL, json={
        "model": MODEL,
        # "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(lines[0:size])}
        ]
    })

    print(resp.json()["choices"][0]["message"]["content"] or resp.json())
