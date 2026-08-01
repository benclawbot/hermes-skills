# GitHub Pages & `gh api` JSON-Body Patterns

`gh` has **no first-class subcommand for Pages**. `gh api` is the only CLI path, and it has a sharp edge: `-f` form-encodes everything, so any endpoint that expects a nested JSON object needs raw JSON via `--input -`. This reference covers the complete Pages enablement workflow plus the JSON-body patterns you'll need for other endpoints that hit the same trap.

## Enabling Pages via API

The Pages API requires a POST body shaped like `{"source": {"branch": "...", "path": "..."}}`. Two fields, nested. Form-encoding the `-f` value sends a string, GitHub returns 422, and the error messages are misleadingly generic.

### Working pattern (the only one that works)

```bash
OWNER=benclawbot
REPO=cahier-de-dictees

printf '%s' '{"source":{"branch":"main","path":"/"}}' \
  | gh api --method POST \
      -H "Accept: application/vnd.github+json" \
      -H "Content-Type: application/json" \
      /repos/$OWNER/$REPO/pages \
      --input -
```

Successful response:
```json
{
  "url": "https://api.github.com/repos/benclawbot/cahier-de-dictees/pages",
  "html_url": "https://benclawbot.github.io/cahier-de-dictees/",
  "status": null,
  "cname": null,
  "build_type": "legacy",
  "source": {"branch": "main", "path": "/"},
  "public": true,
  "https_enforced": true
}
```

### Patterns that **don't** work — and why

```bash
# WRONG — wrong top-level shape (Pages expects {"source": {...}}, not flat keys)
gh api --method POST /repos/$OWNER/$REPO/pages \
  -f source.branch=main -f source.path=/

# WRONG — `-f` form-encodes the JSON as a string value
gh api --method POST /repos/$OWNER/$REPO/pages \
  -f source='{"branch":"main","path":"/"}'
# → 422 Invalid input: data matches no possible input.

# WRONG — `-f` with the right key but still a stringified object
gh api --method POST /repos/$OWNER/$REPO/pages \
  -f source='{"branch":"main","path":"/"}'
# → 422 Invalid property /source: "{\"branch\":\"main\"}" is not of type object.
```

### What if the repo has no public visibility default?

If the org / personal settings disable public Pages by default, you may need to make the repo public first (or enable Pages for private repos in settings). `gh repo edit --visibility public` flips it; `gh api PATCH /repos/$OWNER/$REPO` with `{"visibility": "public"}` is the API equivalent.

### Custom 404, CNAME, HTTPS enforcement

```bash
# Custom 404 page (must exist in the served directory)
printf '%s' '{"source":{"branch":"main","path":"/"},"custom_404":true}' \
  | gh api --method PUT \
      -H "Accept: application/vnd.github+json" \
      -H "Content-Type: application/json" \
      /repos/$OWNER/$REPO/pages --input -

# Add custom domain — note this is `PUT /pages` (update), not POST (create)
printf '%s' '{"cname":"docs.example.com","https_enforced":true}' \
  | gh api --method PUT /repos/$OWNER/$REPO/pages --input -

# Delete Pages site entirely (cancels the deployment)
gh api --method DELETE /repos/$OWNER/$REPO/pages
```

## Wait for the first build

After enabling Pages, the first build runs asynchronously. Poll until status flips to `built`:

```bash
for i in $(seq 1 30); do
  status=$(gh api /repos/$OWNER/$REPO/pages/builds/latest -q '.status' 2>/dev/null)
  echo "try $i: $status"
  [ "$status" = "built" ] && break
  [ "$status" = "errored" ] && { echo "Build failed — check the run logs"; break; }
  sleep 4
done
```

`status` values: `building`, `built`, `errored`. Polling every 4s is fine — the build usually finishes in 20–40s for a static page.

## Verify the live site

Don't trust the build status alone. Hit the URL and confirm the page and every asset it references return 200:

```bash
SITE=https://benclawbot.github.io/$REPO/

# Index page
curl -s -o /dev/null -w "html: %{http_code} %{size_download}b\n" "$SITE"

# Every asset referenced in the HTML
for f in brand-feather header-pencils stat-dictations stat-students \
         stat-success stat-evolution sun-cloud \
         action-class action-dictation action-entry action-report; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$SITE/assets/$f.png")
  echo "$f.png: $code"
done

# Spot-check the rendered title and asset refs
curl -s "$SITE" | grep -oE '<title>[^<]+</title>|src="assets/[^"]+"' | sort -u
```

A live site is verified when: HTML returns 200 with non-zero size, every external asset returns 200, and the rendered `<title>` matches the intended page name.

## When `gh api` hits the JSON-body trap elsewhere

The same `--input -` pattern works for any GitHub REST endpoint that expects a nested body:

```bash
# Update branch protection (nested required_status_checks + restrictions)
printf '%s' '{
  "required_status_checks": {"strict": true, "contexts": ["ci"]},
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 1}
}' | gh api --method PUT /repos/$OWNER/$REPO/branches/main/protection --input -

# Add a label with description (description is a nested object conceptually, but flat)
gh api /repos/$OWNER/$REPO/labels -f name=bug -f color='f29513' -f description='Bug report'
# ↑ Flat scalars are fine with -f

# Create an issue with multiple labels and assignees (arrays — still -f, comma-separated)
gh api /repos/$OWNER/$REPO/issues \
  -f title='...' -f body='...' \
  -f labels='bug,priority:high' \
  -f assignees='alice,bob'
```

**Heuristic for `-f` vs `--input -`:**
| Body shape | Use |
|---|---|
| `{"scalar": "value"}` | `-f scalar=value` |
| `{"array": ["a","b"]}` with known values | `-f array='a,b'` (works for many endpoints) |
| `{"nested": {"foo": 1}}` | **must use `--input -`** |
| `{"list": [{"a":1}, {"b":2}]}` | **must use `--input -`** |
| Anything unclear | **default to `--input -`** — it always works |

## Verifying the trap without burning API calls

If a 422 comes back, the response body distinguishes shape mismatch from value mismatch:

```bash
gh api --method POST /repos/$OWNER/$REPO/pages \
  -f source.branch=main -f source.path=/ 2>&1
```

- `"Invalid input: data matches no possible input."` → wrong top-level shape (you sent flat keys, API wants nested)
- `"Invalid property /foo: \"...\" is not of type object."` → you sent the right key but as a stringified object
- `"Validation Failed"` → field exists, value is wrong (typo in branch name, etc.)

Always print the response body on 4xx — the message alone never tells you enough.