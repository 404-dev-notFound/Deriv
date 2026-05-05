# Docker Setup for Email Analysis Pipeline

This guide covers building and running the email analysis pipeline in Docker.

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t email-pipeline:latest .
```

### 2. Run with Docker Compose (Recommended)

```bash
# Copy .env file with your API keys
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY or ANTHROPIC_API_KEY

# Run the pipeline
docker-compose up
```

### 3. Run with Docker Directly

```bash
docker run --rm \
  -e LLM_PROVIDER=openrouter \
  -e OPENROUTER_API_KEY=sk-or-v1-... \
  -v $(pwd)/data:/app/data:ro \
  -v $(pwd)/ARTIFACTS:/app/ARTIFACTS:rw \
  -v $(pwd)/llm_calls.jsonl:/app/llm_calls.jsonl:rw \
  email-pipeline:latest
```

## Environment Variables

- `LLM_PROVIDER`: `openrouter` or `anthropic`
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key (if using Anthropic)
- `LLM_MODEL`: Model to use (default: `claude-3.5-sonnet`)
- `MAX_TOKENS`: Maximum tokens per request (default: 4096)
- `TEMPERATURE`: Temperature for LLM (default: 0.7)

## Volumes

The container mounts:

- `/app/data` - Input thread.txt (read-only)
- `/app/ARTIFACTS` - Generated outputs (read-write)
- `/app/llm_calls.jsonl` - LLM call log (read-write)

## Validation

After the pipeline runs, validate outputs:

```bash
docker run --rm \
  -v $(pwd)/ARTIFACTS:/app/ARTIFACTS:ro \
  -v $(pwd)/llm_calls.jsonl:/app/llm_calls.jsonl:ro \
  email-pipeline:latest \
  python validate.py
```

## Troubleshooting

### API Key Not Working

Ensure your .env file has correct key format and no extra spaces:
```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key
```

### Build Fails

Clear Docker cache and rebuild:
```bash
docker build --no-cache -t email-pipeline:latest .
```

### Permission Denied on Volumes

Ensure Docker has permission to access data and ARTIFACTS directories:
```bash
chmod -R 755 data ARTIFACTS
```

## Image Size Optimization

Current multi-stage Dockerfile:
- Builder stage: Compiles dependencies
- Final stage: Strips build tools (saves ~300MB)
- Result: ~500MB final image

## Production Deployment

For production:

```bash
docker build -t email-pipeline:v1.0 .
docker tag email-pipeline:v1.0 registry.example.com/email-pipeline:v1.0
docker push registry.example.com/email-pipeline:v1.0

# Deploy with Kubernetes
kubectl apply -f k8s-deployment.yaml
```
