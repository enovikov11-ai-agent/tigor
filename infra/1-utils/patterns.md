# CI Patterns

## Terminal progress output

For CLI scripts that process many items, overwrite the current line for OK status and preserve failures:

```python
IS_TTY = sys.stdout.isatty()

def _ok(label):
    if IS_TTY:
        sys.stdout.write(f"\r\033[K  {label}")
        sys.stdout.flush()
    else:
        print(f"  {label}")

def _fail(label, reason):
    if IS_TTY:
        sys.stdout.write("\r\033[K")
    print(f"SKIP {label}: {reason}")
```

`\r\033[K` — carriage return + erase to end of line. OK lines overwrite each other; failures get a newline so they persist in the scroll-back buffer. Check `IS_TTY` so redirected output stays readable.
