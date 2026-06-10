# Hermes Harness Framework - Templates

This directory contains template harnesses for each harness type.

## Available Templates

### conversation-harness.yaml
Template for conversation testing harnesses.

### tool-usage-harness.yaml
Template for tool usage validation harnesses.

### performance-harness.yaml
Template for performance benchmarking harnesses.

### safety-harness.yaml
Template for safety/policy testing harnesses.

### integration-harness.yaml
Template for integration testing harnesses.

## Usage

```bash
# Create a new harness from a template
hermes harness create my-harness --template conversation

# Or copy a template manually
cp templates/conversation-harness.yaml my-harness/harness.yaml
```

## Template Fields

Each template includes:
- `name`: Harness name
- `version`: Version string
- `description`: What the harness tests
- `harness_type`: Type of harness
- `inputs`: Required inputs
- `outputs`: Expected outputs
- `hermes`: Hermes-specific configuration
- `test`: Test execution configuration

## Customizing Templates

Edit the template values to match your specific testing requirements:
- Change `name` and `description`
- Modify `inputs` to match your test data
- Adjust `hermes.model` and other settings
- Update `test.timeout` as needed