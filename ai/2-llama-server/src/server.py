from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import threading, uvicorn, hashlib, json, time, os, psutil
from fastapi import FastAPI, Depends, HTTPException
from llama_cpp import Llama, llama_perf_context
from pydantic import BaseModel, ConfigDict
from auth_token import read_token_v1
from memory_store import Store
from typing import List


events_log = open("/logs/events.json.log", "a")
run_id = int(time.time())


def get_memory_state():
    try:
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            "process_rss_mb": round(process_memory.rss / 1024 / 1024, 2),
            "process_vms_mb": round(process_memory.vms / 1024 / 1024, 2),
            "process_percent": round(process.memory_percent(), 2),
            "system_total_mb": round(system_memory.total / 1024 / 1024, 2),
            "system_available_mb": round(system_memory.available / 1024 / 1024, 2),
            "system_used_mb": round(system_memory.used / 1024 / 1024, 2),
            "system_free_mb": round(system_memory.free / 1024 / 1024, 2),
            "system_percent": round(system_memory.percent, 2)
        }
    except Exception:
        return {}


def log_event(event_type: str, **kwargs):
    event = {"unixtime": time.time(), "run_id": run_id, "type": event_type, "ram": get_memory_state(), **kwargs}
    events_log.write(json.dumps(event, ensure_ascii=False) + "\n")
    events_log.flush()


def cleanup_thread():
    while True:        
        try:
            store.clean_expired_tasks()
        except Exception as e:
            print(f"Cleanup error: {e}")

        time.sleep(3600)


class Message(BaseModel):
    role: str
    content: str

    model_config = ConfigDict(extra="forbid")

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str


def inference_thread():
    while True:        
        task = store.take_task()
            
        if not task:
            task_event.wait()
            task_event.clear()
            continue

        try:
            if task["model"] not in models:
                model_config = models_config[task["model"]]
                log_event("model_load_start", model=task["model"], config=model_config, n_gpu_layers = 0, chat_format = "chatml")
                
                models[task["model"]] = Llama(model_path = model_config["model_path"], n_ctx = model_config["n_ctx"], use_mmap = model_config["use_mmap"],
                    use_mlock = model_config["use_mlock"], n_threads = model_config["n_threads"], n_gpu_layers = 0, chat_format = "chatml")
                log_event("model_load_complete", model=task["model"])

            model = models[task["model"]]

            log_event("inference_start", task_id=task["task_id"], model=task["model"], max_tokens=task["max_tokens"], temperature=task["temperature"])
            messages = json.loads(task["messages_json"])
            response = model.create_chat_completion(messages=messages, max_tokens=task["max_tokens"], temperature=task["temperature"])
            perf = llama_perf_context(model.ctx)
            
            log_event("inference_complete", task_id=task["task_id"], model=task["model"], t_load_ms=perf.t_load_ms, t_p_eval_ms=perf.t_p_eval_ms, t_eval_ms=perf.t_eval_ms, n_p_eval=perf.n_p_eval, n_eval=perf.n_eval)
            
            choices = [Choice(**choice) for choice in response["choices"]]
            choices_json = json.dumps([choice.model_dump() for choice in choices], ensure_ascii=False)
            store.finish_task(task["task_id"], choices_json, t_load_ms=perf.t_load_ms, t_p_eval_ms=perf.t_p_eval_ms, t_eval_ms=perf.t_eval_ms, n_p_eval=perf.n_p_eval, n_eval=perf.n_eval)
        except Exception as e:
            print(f"Inference error: {e}")
            log_event("inference_error", model=task["model"], task_id=task["task_id"])
            store.error_task(task_id=task["task_id"])


task_event = threading.Event()
store = Store()

threading.Thread(target=cleanup_thread, daemon=True).start()
threading.Thread(target=inference_thread, daemon=True).start()

security = HTTPBearer(description="Bearer token for authentication")

app = FastAPI(title="LLM inference API (test)", version="1.0.0", docs_url="/",
    description='''This is test, do not use it for production or handling sensitive data.

Unless required by applicable law or agreed to in writing, this software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.'''
)
models, model_aliases = {}, {}

with open("models.json", "r") as file:
    models_config = json.load(file)

for canonical_name, model in models_config.items():
    for alias in model["aliases"]:
        model_aliases[alias] = canonical_name


@app.get("/v1/models")
def get_models():
    return models_config


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_data = read_token_v1(credentials.credentials)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_data


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 4096

    model_config = ConfigDict(extra="forbid")


@app.post("/v1/chat/completions-async")
def chat_completions(request: ChatCompletionRequest, user_data: dict = Depends(get_current_user)):
    request.model = model_aliases.get(request.model, request.model)

    if request.model not in models_config:
        return {"error": {"message": "Invalid model id", "available_models": models_config}}
    
    if request.max_tokens > user_data["max_tokens"] or request.max_tokens > models_config[request.model]["n_ctx"]:
        return {"error": {"message": "Too many tokens requested", "requested": request.max_tokens, "user_limit": user_data["max_tokens"], "model_limit": models_config[request.model]["n_ctx"]}}
    
    user_messages = store.get_task_count(user_id=user_data["user_id"])
    
    if user_messages >= user_data["max_daily_messages"]:
        return {"error": {"message": "Too many requests per day", "user_messages": user_messages, "limit": user_data["max_daily_messages"]}}

    messages_json = json.dumps([dict(msg) for msg in request.messages], ensure_ascii=False)
    
    request_hash = hashlib.sha256(request.model_dump_json().encode()).hexdigest()

    add, task = store.enqueue_task(user_data["user_id"], request_hash, request.temperature, request.max_tokens, request.model, user_data["priority"], messages_json)

    if task["choices_json"]:
        return {"choices": json.loads(task["choices_json"]), "stats": {"t_load_ms": task["t_load_ms"], "t_p_eval_ms": task["t_p_eval_ms"], "t_eval_ms": task["t_eval_ms"], "n_p_eval": task["n_p_eval"], "n_eval": task["n_eval"]}}

    task_event.set()        
    return {"wait": {"task_id": f"{run_id}_{task['task_id']}", "messages_left": user_data["max_daily_messages"] - user_messages - add}}


log_event("server_start")
uvicorn.run(app, uds="/var/run/llama-cpp.sock")
