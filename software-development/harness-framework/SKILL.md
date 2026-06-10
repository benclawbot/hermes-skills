---
name: harness-framework
description: "Framework for creating, validating, and running test/evaluation harnesses for Hermes agent"
version: 1.0.0
author: Hermes Agent Team
license: MIT
dependencies: [pytest, pyyaml, jinja2]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Testing, Evaluation, Harness, Framework, Quality Assurance, Automation]
    requires_toolsets: [terminal, file, web]
---

# Hermes Harness Framework

Provides a standardized way to create, validate, and run test/evaluation harnesses for Hermes agent behaviors, workflows, and integrations.

## What's Inside

This skill provides:
- Templates for different types of harnesses (conversation, tool usage, performance, safety, integration)
- CLI commands for harness management
- Validation tools for harness configurations
- Execution engines for running harnesses
- Result reporting and analysis utilities

## Quick Start

### Create a new harness

```bash
hermes harness create my-conversation-harness --type conversation
```

### Validate a harness

```bash
hermes harness validate my-conversation-harness/
```

### Run a harness

```bash
hermes harness run my-conversation-harness/
```

## Harness Types

### 1. Conversation Harness
Tests multi-turn conversation flows, context retention, and response quality.

### 2. Tool Usage Harness
Validates correct tool selection, parameter passing, and result handling.

### 3. Performance Harness
Measures response times, token usage, and resource consumption.

### 4. Safety Harness
Tests for harmful outputs, policy violations, and boundary conditions.

### 5. Integration Harness
Tests MCP server connections, external API integrations, and plugin functionality.

## Harness Manifest Format

Each harness requires a `harness.yaml` manifest:

```yaml
name: my-harness
version: 1.0.0
description: "Description of what this harness tests"
harness_type: conversation|tool-usage|performance|safety|integration
hermes_requires: ">=0.13.0"
author: "Your Name"
license: "MIT"

inputs:
  - name: test_prompts
    description: "Prompts or test cases to run"
    required: true
    type: array
    item_type: string

outputs:
  - name: results
    description: "Test results"
    required: true
    type: object

dependencies:
  - pytest
  - requests

env_require:
  - name: OPENAI_API_KEY
    description: "OpenAI API key for model access"
    required: true

hermes:
  model: "claude-sonnet-4"
  temperature: 0.7
  max_iterations: 30

test:
  timeout: 300
  retry_count: 1
  continue_on_failure: false
```

## Common Workflows

### Workflow 1: Creating a Conversation Harness

1. Create the harness scaffold
2. Define test cases in `test_cases.yaml`
3. Implement any custom logic in `harness.py` (optional)
4. Validate the harness
5. Run the harness
6. Analyze results

### Workflow 2: Creating a Tool Usage Harness

1. Create harness for tool usage testing
2. Define expected tool sequences
3. Set up mock tools or real tool configurations
4. Run and validate tool selection accuracy

### Workflow 3: Performance Benchmarking

1. Create performance harness
2. Define benchmark scenarios
3. Run under different load conditions
4. Collect and analyze metrics

## Advanced Usage

### Custom Harness Logic

Create a `harness.py` file in your harness directory for custom logic:

```python
from hermes_harness import BaseHarness

class MyCustomHarness(BaseHarness):
    def setup(self):
        pass
    
    def execute_test(self, test_case):
        return {"passed": True, "metrics": {"response_time": 1.5}}
    
    def teardown(self):
        pass
```

### Sharing Harnesses

Harnesses can be shared as directories or packaged:

```bash
hermes harness pack my-harness/ --output my-harness-1.0.0.zip
hermes harness install my-harness-1.0.0.zip
```

## Result Formats

Harnesses produce results in standardized formats:
- JSON for machine processing
- Markdown for human reading
- JUnit XML for CI integration
- HTML reports for detailed analysis

## Best Practices

1. Keep test cases independent and repeatable
2. Use realistic test data that matches production scenarios
3. Include both positive and negative test cases
4. Measure both correctness and performance
5. Automate harness execution in CI pipelines
6. Document harness purpose and usage clearly

## Troubleshooting

### Harness Validation Fails
Check:
- Manifest format is correct YAML
- All required fields are present
- Referenced files exist
- Dependencies are available

### Harness Execution Fails
Check:
- Hermes agent is properly configured
- Required API keys are set
- Network connectivity for external services
- Sufficient permissions for file operations

### Results Analysis
Look for:
- Patterns in failures (specific tools, prompts, etc.)
- Performance trends over time
- Resource usage anomalies
- Consistency issues across runs

## Resources

- Template harnesses: `~/.hermes/skills/harness-framework/templates/`
- Example harnesses: `~/.hermes/skills/harness-framework/examples/`
- API reference: See `references/` directory
- Community harnesses: https://github.com/hermes-agent/harnesses

## Conclusion

The Hermes Harness Framework provides a standardized, extensible way to test and validate Hermes agent behaviors. By creating reusable harnesses, teams can ensure consistent quality, catch regressions early, and automate validation of agent improvements.
