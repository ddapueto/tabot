Deploy Tabot to the specified environment. Usage: /deploy [staging|production]

Steps:
1. Run /lint and /test to verify everything passes
2. Build Docker images: `docker compose build`
3. If staging: deploy to staging server
4. If production: require explicit confirmation, then deploy
5. Run health check after deploy
6. Report deployment status
