# Proof-of-concept: Refactor existing Python codebase into microservices using Claude Code
JDemetra+ (toolkit for seasonal adjustment and time series analysis) Python source repo is located at https://github.com/thuduc/jdplus-main-java2python

This POC is to evaluate Claude Code (an agentic coding tool from Anthropic: https://www.anthropic.com/claude-code) for its ability to refactor an existing Python codebase into a set of modular microservices.

#### Conversion Process: 
* Step 1 - use a reasoning LLM that's able to analyze an existing code repository, then put together a comprehensive refactoring plan to refactor the entire project's codebase into microservices. We used Anthropic's Claude Opus 4 LLM for our reasoning LLM. We chose Opus 4 over OpenAI's ChatGPT o3 (advanded reasoning) and Google Gemini 2.5 Pro (reasoning) due to its advanced ability to analyze code.
* Step 2 - developer verifies the refactoring plan and modifies the plan (or engage with Claude Code to modify the plan) if needed.
* Step 3 - use this refactoring plan (see MICROSERVICES_REFACTORING_PLAN.md) with Claude Code (together with Claude Opus 4 LLM, known as the most advanded model for agentic coding tasks) to implement all tasks in all phases defined in the plan.

The Python microservices refactoring effort took Claude Code about 2 hours to complete. Claude Code created 1 common Python library and 8 microservices. The library and 8 microservices reside under microservices/ folder.

Claude Code provided the following optional infrastructure tasks that could be implemented later, depending on the targeted compute (in our example, Kubernetes is the proposed compute):
  - API Gateway - Request routing, authentication, rate limiting
  - Service Registry - Service discovery and health checking
  - Inter-service Communication - Set up message queues (RabbitMQ/Kafka)
  - Kubernetes Manifests - For production deployment
  - CI/CD Pipelines - Automated testing and deployment
  - Integration Tests - Cross-service testing
  - Monitoring & Observability - Prometheus, Grafana, Jaeger setup

## All prompts issued to Claude Code
The complete list of prompts issued to Clause Code is listed below:

> we're planning to refactor the existing codebase into modular microservices. Each microservice will be dockerized and run in its own container. Each microservice will exist in a separate git repo. You're an expert in microservices architecture, come up with a design and a plan on how to refactor the current codebase to support this effort. Save this plan under MICROSERVICES_REFACTORING_PLAN.md

> Go ahead and implement @MICROSERVICES_REFACTORING_PLAN.md . Put all microservices git repos under microservices directory. Make sure each microsservice has sufficient unit test coverage

> Implement the remaining 5 services. Do not implement any of the proposed infrastructure tasks
