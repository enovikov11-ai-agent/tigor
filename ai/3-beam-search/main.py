import sys
import heapq
import math
from llama_cpp import Llama
import llama_cpp.llama_chat_format as llama_chat_format

MAX_PATHS = 1000
MIN_LOGPROB = -15

def softmax(logits):
    max_logit = max(logits)
    exps = [math.exp(x - max_logit) for x in logits]
    total = sum(exps)
    return [e / total for e in exps]

def solve(llm, messages):
    variable_indices = [i for i, m in enumerate(messages) if "check_content" in m]
    paths = [(0.0, [""])]
    results = []

    def build_prompt(variable_texts):
        built = []
        var_idx = 0
        stop_at = variable_indices[len(variable_texts) - 1] + 1
        for i, m in enumerate(messages[:stop_at]):
            if "check_content" in m:
                built.append({"role": m["role"], "content": variable_texts[var_idx]})
                var_idx += 1
            else:
                built.append(m)
        # Try to get formatter from the llm's chat_handler (for Jinja2 templates from GGUF)
        if llm.chat_handler is not None:
            formatter = getattr(llm.chat_handler, "formatter", None)
            if formatter:
                return formatter(messages=built).prompt
        # Fallback: try registered chat format handlers
        try:
            chat_handler = llama_chat_format.get_chat_completion_handler(llm.chat_format)
            formatter = getattr(chat_handler, "formatter", None)
            if formatter:
                return formatter(messages=built).prompt
        except Exception:
            pass
        # Fallback: build formatter from GGUF metadata directly
        chat_template = llm.metadata.get("tokenizer.chat_template")
        if chat_template:
            formatter = llama_chat_format.Jinja2ChatFormatter(
                template=chat_template,
                bos_token=llm.detokenize([llm.token_bos()]).decode(errors="replace") if llm.token_bos() is not None else "",
                eos_token=llm.detokenize([llm.token_eos()]).decode(errors="replace") if llm.token_eos() is not None else "",
            )
            return formatter(messages=built).prompt
        raise ValueError(f"Could not find formatter for chat_format: {llm.chat_format}")

    def try_add_path(new_path):
        new_logprob = new_path[0]
        if len(paths) + len(results) < MAX_PATHS:
            heapq.heappush(paths, new_path)
            return None
        elif new_logprob > paths[0][0]:
            heapq.heapreplace(paths, new_path)
            return ("replaced", new_path)
        else:
            return ("discarded", new_path)

    while paths:
        best_idx = max(range(len(paths)), key=lambda i: paths[i][0])
        paths[best_idx], paths[-1] = paths[-1], paths[best_idx]
        logprob, var_texts = paths.pop()
        heapq.heapify(paths)

        prompt = build_prompt(var_texts)
        tokens = llm.tokenize(prompt.encode(), add_bos=False)
        llm.reset()
        llm.eval(tokens)
        logits = llm.scores[len(tokens) - 1].tolist()
        probs = softmax(logits)

        check_fn = messages[variable_indices[len(var_texts) - 1]]["check_content"]

        for token_id, prob in enumerate(probs):
            if prob <= 0:
                continue
            token_logprob = math.log(prob)
            new_logprob = logprob + token_logprob
            if new_logprob < MIN_LOGPROB:
                continue

            token_str = llm.detokenize([token_id]).decode(errors="replace")
            if len(token_str) == 0:
                continue

            new_text = var_texts[-1] + token_str
            check_result = check_fn(new_text)

            if check_result is False:
                yield ("discarded", (new_logprob, var_texts[:-1] + [new_text]))
                continue

            if isinstance(check_result, str):
                new_var_texts = var_texts[:-1] + [check_result]
                if len(new_var_texts) == len(variable_indices):
                    results.append((new_logprob, new_var_texts))
                    yield ("finalized", (new_logprob, new_var_texts))
                    if len(paths) + len(results) > MAX_PATHS:
                        heapq.heappop(paths)
                else:
                    event = try_add_path((new_logprob, new_var_texts + [""]))
                    if event:
                        yield event
            else:
                event = try_add_path((new_logprob, var_texts[:-1] + [new_text]))
                if event:
                    yield event

    results.sort(reverse=True)
    return results

if __name__ == "__main__":
    import regex

    llm = Llama(
        model_path=sys.argv[1],
        n_ctx=8192,
        n_threads=64,
        n_gpu_layers=0,
        logits_all=True,
        verbose=True,
    )

    npm_package = regex.compile(r"^To solve this problem, run `npm install [a-z][a-z0-9_-]+`")

    def check_npm(fragment):
        match = npm_package.match(fragment, partial=True)
        if match is None:
            return False
        elif match.partial:
            return True
        else:
            return match.group(0)

    messages = [
        {"role": "user", "content": "What package should I install to solve my problem?"},
        {"role": "assistant", "check_content": check_npm},
    ]

    gen = solve(llm, messages)
    results = []
    try:
        for event, path in gen:
            if event == "finalized":
                results.append(path)
            if event != "discarded":
                print(f"{event}: logprob={path[0]:.2f} prob={math.exp(path[0]):.4f} texts={path[1]}")
    except KeyboardInterrupt:
        print("\nInterrupted, partial results:")

    results.sort(reverse=True)
    print(f"\n=== Top {min(10, len(results))} Results ===")
    for logprob, texts in results[:10]:
        print(f"prob={math.exp(logprob):.4f} texts={texts}")
