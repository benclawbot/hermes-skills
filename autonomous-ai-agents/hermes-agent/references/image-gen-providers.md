# Image Gen Providers

Hermes supports pluggable image generation backends via the `ImageGenProvider` interface.
Built-in providers live in `<repo>/plugins/image_gen/<name>/` (auto-loaded as `kind: backend`).
User-installed providers live in `~/.hermes/plugins/image_gen/<name>/` (opt-in via `plugins.enabled`).

## Interface

```python
# ~/.hermes/plugins/image_gen/<name>/__init__.py
from agent.image_gen_provider import (
    ImageGenProvider, success_response, error_response,
    DEFAULT_ASPECT_RATIO, resolve_aspect_ratio,
)

class MyProvider(ImageGenProvider):
    @property
    def name(self) -> str: return "myprovider"
    @property
    def display_name(self) -> str: return "My Provider"

    def is_available(self) -> bool:
        return bool(os.getenv("MYPROVIDER_API_KEY"))  # or always True for free providers

    def list_models(self) -> list[dict]:
        return [{"id": "my-model", "display": "My Model", "speed": "~10s", "strengths": "..."}]

    def generate(self, prompt: str, aspect_ratio: str = DEFAULT_ASPECT_RATIO, **kwargs) -> dict:
        # Return success_response(...) or error_response(...)
```

Required files:
- `~/.hermes/plugins/image_gen/<name>/__init__.py` — provider implementation
- `~/.hermes/plugins/image_gen/<name>/plugin.yaml` — manifest

## plugin.yaml format

```yaml
name: <name>
version: 1.0.0
kind: backend
description: One-line description
entry: __init__.py
image_gen:
  provider: <name>
  display_name: <display>
  models:
    - id: <model-id>
      display: <display>
      speed: ~Ns
      strengths: ...
```

## Registering

Your `__init__.py` must call `ctx.register_image_gen_provider(YourClass())` in a `register(ctx)` function:

```python
def register(ctx) -> None:
    ctx.register_image_gen_provider(MyProvider())
```

## Configuration

1. Set the active provider in `config.yaml`:
   ```
   hermes config set image_gen.provider <name>
   ```

2. Enable the `image_gen` toolset:
   ```
   hermes tools enable image_gen
   ```

3. For API keys: write to `~/.hermes/.env` via shell redirection (write_file is blocked for `.env`):
   ```
   printf 'PROVIDER_API_KEY=your_key\n' >> ~/.hermes/.env
   ```

4. Restart the gateway to pick up a new plugin:
   ```
   systemctl --user restart hermes-gateway
   ```

## Pollinations.ai (free, no key)

Pollinations.ai requires no API key — always available. Example provider at `~/.hermes/plugins/image_gen/pollinations/`.

API: `https://image.pollinations.ai/prompt/<encoded_prompt>?width=&height=&seed=&model=`

Returns a redirect to a PNG/JPG. Save `response.content` to cache.

Tested working (May 2026). Config:
```bash
hermes config set image_gen.provider pollinations
hermes tools enable image_gen
systemctl --user restart hermes-gateway
```

## Verification

```python
import sys; sys.path.insert(0, '/path/to/hermes-agent')
sys.path.insert(0, '/path/to/hermes-agent/agent')
from agent.image_gen_provider import success_response, error_response, DEFAULT_ASPECT_RATIO

import importlib.util
spec = importlib.util.spec_from_file_location("provider",
    "/home/thomas/.hermes/plugins/image_gen/pollinations/__init__.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
# find the provider class and call .generate("a cat", aspect_ratio="square")
```