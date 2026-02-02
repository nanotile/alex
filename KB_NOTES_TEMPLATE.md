**LiteLLMModel** is a wrapper class that various AI frameworks implement to provide access to [LiteLLM](https://github.com/BerriAI/litellm)'s unified interface for 100+ LLM providers (OpenAI, Anthropic, Bedrock, Vertex AI, etc.) through a single API.

The class appears in multiple frameworks:

**OpenAI Agents SDK:**
```python
from agents.extensions.models.litellm_model import LitellmModel

agent = Agent(
    name="Assistant",
    model=LitellmModel(model="anthropic/claude-sonnet-4-20250514", api_key="...")
)
```

**Strands Agents:**
```python
from strands.models.litellm import LiteLLMModel

model = LiteLLMModel(
    model_id="bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    params={"max_tokens": 1000, "temperature": 0.7}
)
```

**smolagents (HuggingFace):**
```python
from smolagents import LiteLLMModel

model = LiteLLMModel(model_id="anthropic/claude-3-5-sonnet-latest", temperature=0.2)
```

**DeepEval:**
```python
from deepeval.models import LiteLLMModel

model = LiteLLMModel(model="openai/gpt-4o", api_key="...")
```

The key benefit is **provider abstraction** — you specify the model as `provider/model-name` and LiteLLM handles the API differences, letting you swap providers without rewriting code. It also gives you features like cost tracking, rate limiting, and fallback routing for free.

Is there a specific framework or use case you're working with?yls
ls

**LiteLLMModel** is a wrapper class that various AI frameworks implement to provide access to [LiteLLM](https://github.com/BerriAI/litellm)'s unified interface for 100+ LLM providers (OpenAI, Anthropic, Bedrock, Vertex AI, etc.) through a single API.

The class appears in multiple frameworks:

**OpenAI Agents SDK:**
```python
from agents.extensions.models.litellm_model import LitellmModel

agent = Agent(
    name="Assistant",
    model=LitellmModel(model="anthropic/claude-sonnet-4-20250514", api_key="...")
)
```

**Strands Agents:**
```python
from strands.models.litellm import LiteLLMModel

model = LiteLLMModel(
    model_id="bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    params={"max_tokens": 1000, "temperature": 0.7}
)
```

**smolagents (HuggingFace):**
```python
from smolagents import LiteLLMModel

model = LiteLLMModel(model_id="anthropic/claude-3-5-sonnet-latest", temperature=0.2)
```

**DeepEval:**
```python

from deepeval.models import LiteLLMModel

model = LiteLLMModel(model="openai/gpt-4o", api_key="...")
```

The key benefit is **provider abstraction** — you specify the model as `provider/model-name` and LiteLLM handles the API differences, letting you swap providers without rewriting code. It also gives you features like cost tracking, rate limiting, and fallback routing for free.

Is there a specific framework or use case you're working with?