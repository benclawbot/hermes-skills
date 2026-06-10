# OpenRouter: Auxiliary Provider for Vision

Use OpenRouter as a **secondary/auxiliary provider** without making it the main model. Common case: main model is MiniMax/Claude, but you want a free OpenRouter model to handle Telegram image analysis (vision tasks).

## Config: auxiliary.vision with OpenRouter

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: google/gemma-4-31b-it:free   # the free vision model
    base_url: ''
    api_key: ''        # reads from OPENROUTER_API_KEY in ~/.hermes/.env
    timeout: 120
    extra_body: {}
    download_timeout: 30
    default: ''        # must be empty — model goes in 'model' field, not 'default'
```

**Key pitfall:** `hermes config set auxiliary.vision.default <model>` puts the model in the wrong field (`default` instead of `model`). The `default` key in the auxiliary section is not the right target. After using `hermes config set`, always verify the YAML directly with `grep -A10 "^auxiliary:" ~/.hermes/config.yaml` and patch if needed.

**Restart required** after changing auxiliary config: `hermes gateway restart` or start a new CLI session.

## Setting the API Key

```bash
printf 'OPENROUTER_API_KEY=sk-or-v1-<your-key>\n' >> ~/.hermes/.env
```

The `.env` file is protected — `write_file` will be denied. Always use shell redirection.

## Query OpenRouter API for Free Vision Models

The API endpoint is `https://openrouter.ai/api/v1/models`. Vision models have `image` in `architecture.input_modalities` (not `modalities` — that's a different field and often empty).

```python
import urllib.request, json

req = urllib.request.Request(
    'https://openrouter.ai/api/v1/models',
    headers={'Authorization': 'Bearer <YOUR_KEY>'}
)
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read())

vision = []
for m in data.get('data', []):
    arch = m.get('architecture') or {}
    input_mods = arch.get('input_modalities') or []
    price = m.get('pricing') or {}
    prompt_price = float(price.get('prompt', '0') or 0)

    if 'image' in input_mods:
        vision.append({
            'id': m['id'],
            'name': m.get('name'),
            'input_mods': input_mods,
            'context_length': m.get('context_length'),
            'prompt_price': prompt_price,
        })

vision.sort(key=lambda x: x['prompt_price'])
for x in vision:
    price_str = "FREE" if x['prompt_price'] == 0.0 else f"${x['prompt_price']:.2e}"
    print(f"{x['id']} | {price_str} | context: {x['context_length']}")
```

## Free Vision Models Available (as of May 2025)

| Model ID | Price | Context | Notes |
|----------|-------|---------|-------|
| `google/lyria-3-pro-preview` | free | 1M | best free vision, large context |
| `google/lyria-3-clip-preview` | free | 1M | |
| `google/gemma-4-31b-it:free` | free | 262K | recommended for Telegram image analysis |
| `google/gemma-4-26b-a4b-it:free` | free | 262K | |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | free | 256K | also handles audio |
| `openrouter/free` | free | 200K | auto-routes to best free model |
| `nvidia/nemotron-nano-12b-v2-vl:free` | free | 128K | smaller VL |
| `baidu/qianfan-ocr-fast:free` | free | 65K | OCR-specific |

For Telegram image analysis, `google/gemma-4-31b-it:free` is the best balance of capability, context, and zero cost.

## Keep OpenRouter from Becoming the Main Provider

If you set `model.provider: openrouter` by mistake and want it only for auxiliary tasks:

```bash
hermes config set model.provider minimax
hermes config set model.default anthropic/claude-3.5-sonnet
```

OpenRouter should only appear under `auxiliary.vision.provider`, not under the top-level `model.provider`.