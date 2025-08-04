## GenAI Proof of Concept: refactor existing Python codebase into microservices
The purpose of this proof of concept is to find out if an LLM can take an existing complex Python codebase and refactor it into microservices. The project we will be using for this PoC is the JDemetra+ Python version of the project: https://github.com/thuduc/jdplus-main-java2python

### LLM & AI Tool
* LLM used: Claude Opus 4 (best coding LLM) - https://www.anthropic.com/claude/opus
* AI tool used: Claude Code (best coding CLI due to its integration with Clause 4 LLMs) - https://www.anthropic.com/claude-code

### Conversion Process: 
* Step 1 - use Claude Code (together with Opus 4 LLM) to analyze an existing project's codebase, then ask it to put together a comprehensive refactoring plan to refactor into microservices.
* Step 2 - developer verifies the refactoring plan and modifies the plan as needed. Developer could use Claude Code and iterate through this process until the plan is ready.
* Step 3 - use this refactoring plan (see [MICROSERVICES_REFACTORING_PLAN.md](MICROSERVICES_REFACTORING_PLAN.md)) in Claude Code (together with Claude Opus 4 LLM) to implement all phases in the plan.

### Conversion Results
* The refactoring effort took Claude Code about 2 hours to complete
* The original codebase was refactored into 8 microservices, each with its own Dockerfile. These microservices reside under microservices/ folder.
* Claude Code also provided the following optional infrastructure tasks that could be implemented later, depending on the targeted compute (in our example, Kubernetes is the proposed compute):
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
