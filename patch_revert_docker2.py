with open('docker-compose.yml', 'r') as f:
    content = f.read()

postgres_service = """  postgres:
    image: postgres:15-alpine
    container_name: industrial_brain_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgrespassword
      POSTGRES_DB: industrial_brain
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:"""

content = content.replace("  redis:", postgres_service)

with open('docker-compose.yml', 'w') as f:
    f.write(content)
