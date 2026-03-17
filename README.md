# proxify-llm
A proxy server for llm providers, designed to implement logging , authentications , routings based on conditions. Also It provides a unified interface for interacting with different language models, allowing developers to easily switch between them without changing their application code.

Phase 1: Basic Proxy Server
- Implement a basic proxy server.
- Logging of all incoming requests and outgoing responses in files.

Phase 2: Implementation of Basic Dashboard
- Develop a web-based dashboard for monitoring real-time logs of requests and responses.

Phase 4: Implementation Tunneling and Self-Signed SSL
- Implement tunneling capabilities(claudeflare, ngrok) to securely forward requests to llm providers.
- Implement self-signed SSL certificates for secure communication.