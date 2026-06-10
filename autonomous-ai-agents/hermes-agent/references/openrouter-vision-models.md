# OpenRouter: Free Vision Models for Telegram Image Analysis

Captured 2026-05-10 from API discovery session.

## How to Discover Free Vision Models

```python
import urllib.request, json

req = urllib.request.Request(
    'https://openrouter.ai/api/v1/models',
    headers={'Authorization': 'Bearer <OPENROUTER_API_KEY>'}
)
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read())

# Filter: free + image input + supports tools
free_vision_tools = []
for m in data.get('data', []):
    arch = m.get('architecture') or {}
    input_mods = arch.get('input_modalities') or []
    price = m.get('pricing') or {}
    
    if 'image' in input_mods and float(price.get('prompt', '0') or 0) == 0.0:
        supported = m.get('supported_parameters') or []
        supports_tools = 'tools' in supported
        free_vision_tools.append({
            'id': m['id'],
            'name': m.get('name'),
            'context_length': m.get('context_length'),
            'supports_tools': supports_tools,
        })

for x in sorted(free_vision_tools, key=lambda a: -a['context_length']):
    tool_status = '✓ tools' if x['supports_tools'] else '✗ no tools'
    print(f"{x['id']}  context:{x['context_length']}  {tool_status}")
```

## Free Vision Models (confirmed working with Hermes tool-calling)

| Model ID | Context | Tools | Notes |
|----------|---------|-------|-------|
| `openrouter/free` | 200K | ✓ | Free Models Router — works, used as fallback |
| `google/gemma-4-31b-it:free` | 262K | ✓ | FAILED — 400 Gemini API tool schema incompatibility |
| `google/gemma-4-26b-a4b-it:free` | 262K | ✓ | Same incompatibility as above |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256K | ✓ | Reasoning model — may produce empty responses |
| `nvidia/nemotron-nano-12b-v2-vl:free` | 128K | ✓ | Empty responses in testing |
| `google/lyria-3-pro-preview` | 1M | ✗ | No tool support — unsuitable for Hermes |
| `google/lyria-3-clip-preview` | 1M | ✗ | No tool support — unsuitable for Hermes |
| `baidu/qianfan-ocr-fast:free` | 65K | ✗ | No tool support — unsuitable for Hermes |

## Config Pattern: Auxiliary Vision Model for Telegram

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: openrouter/free   # Only confirmed-working free vision model with tool support
    default: ''
    timeout: 120
```

Set via:
```bash
hermes config set auxiliary.vision.provider openrouter
# Then edit config.yaml to set model: openrouter/free (hermes config set may not handle '/' correctly)
```

## Key Learnings

1. **OpenRouter model IDs for hermes chat:** Use the raw ID from the API (e.g., `google/gemma-4-31b-it:free`), NOT with `openrouter/` prefix in CLI
2. **Gemma 4 fails with Hermes tool calling:** Gemini API rejects Hermes's tool schema format. This is a provider-side incompatibility — not configurable.
3. **nemotron-nano-12b-v2-vl fails:** It's a reasoning model. Produces thinking but no visible text response in simple queries.
4. **`openrouter/free` is the safe choice:** It's a router that handles tool calling correctly and accepts image input.
5. **Test with simple queries first:** `hermes chat -q "Reply with just the word OK" -m <model> --provider openrouter` before relying on it for production.

## API Key Storage

OpenRouter key stored in `~/.hermes/.env`:
```
OPENROUTER_API_KEY=sk-or-v1-...
```

Main model remains `MiniMax-M2.7` via minimax provider. OpenRouter used only for auxiliary/vision.