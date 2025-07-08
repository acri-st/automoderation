# AutoModeration


## Table of Contents

- [Introduction](#Introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development](#development)
- [Contributing](#contributing)

## Introduction

### What is the AutoModeration microservice?

The AutoModeration microservice is a component designed to automatically analyze and moderate content. It provides content filtering capabilities to ensure compliance with organizational policies and standards.

**Key Features:**
- **Automated Content Analysis**: Uses AI (detoxify) to detect inappropriate or non-compliant content
- **Real-time Processing**: Provides feedback on content submissions
- **Configurable Rules**: Supports customizable moderation policies and thresholds
- **Scalable Architecture**: Built as a microservice for easy integration and horizontal scaling

**Use Cases:**
- User-generated content moderation
- Document and file screening
- Compliance monitoring
- Quality assurance automation


## Prerequisites

Before you begin, ensure you have the following installed:
- **Git** 
- **Docker** Docker is mainly used for the test suite, but can also be used to deploy the project via docker compose

## Installation

1. Clone the repository:
```bash
git clone https://github.com/acri-st/automoderation.git automoderation
cd automoderation
```

## Development

## Development Mode

### Standard local development

Setup environment
```bash
make setup
```

Start the development server:
```bash
make start
```

To clean the project and remove node_modules and other generated files, use:
```bash
make clean
```

## Contributing

Check out the **CONTRIBUTING.md** for more details on how to contribute.