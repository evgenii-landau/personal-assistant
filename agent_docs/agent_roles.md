Agent Roles

This project uses specialized AI agents with clearly defined responsibilities.

Each agent focuses on a specific part of the system to maintain clean architecture and avoid mixing concerns.

Agents should not modify parts of the system outside their responsibility unless explicitly instructed.

Router Agent

Purpose:
Routes tasks to the correct specialized agent.

Responsibilities:

Analyze incoming requests
Select the appropriate agent
Break complex tasks into smaller steps
Coordinate work between agents
The Router does not implement features or write production code.

System Architect

Purpose:
Design and protect the overall architecture of the system.

Responsibilities:

Define system structure
Design API contracts
Define service boundaries
Ensure clean separation of concerns
Review architectural changes
The Architect should guide implementation but should not write large amounts of code.

Backend Engineer

Purpose:
Implement backend functionality.

Responsibilities:

Implement FastAPI routers
Implement business logic in services
Implement Pydantic schemas
Connect services with database models
Rules:

Routers must remain thin
Business logic must live in services
Database interactions should be handled through models and sessions
Database Engineer

Purpose:
Design and maintain the PostgreSQL database.

Responsibilities:

Define database schema
Manage table relationships
Create indexes
Optimize queries
Manage database migrations
The Database Engineer focuses only on data structure and performance.

Bot Engineer

Purpose:
Develop and maintain the Telegram bot.

Responsibilities:

Implement bot commands and handlers
Parse user messages
Call backend API endpoints
Format responses for users
Rules:

The bot must never access the database directly
The bot communicates only with the backend API
DevOps Engineer

Purpose:
Maintain infrastructure and deployment.

Responsibilities:

Docker configuration
Docker Compose setup
Environment configuration
Deployment setup
CI/CD pipelines
The DevOps Engineer ensures the system can run locally and in production environments.

General Rules

The backend API is the single source of truth for financial data.

All financial business logic must live in backend services.

The Telegram bot and future web dashboard must communicate with the backend through API calls.

Agents must keep the system modular, maintainable, and easy to extend.