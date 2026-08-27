import re

with open('docker-compose.yml', 'r') as f:
    content = f.read()

# Replace backend DATABASE_URL
content = re.sub(
    r'- DATABASE_URL=postgresql://neondb_owner:npg_8KFDcHNlx3GA@ep-mute-haze-aoip5ik1-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb\?sslmode=require',
    r'- DATABASE_URL=postgresql://postgres:postgrespassword@postgres:5432/industrial_brain',
    content
)

# Add postgres service back if not present
if "postgres:" not in content:
    postgres_service = """
  postgres:
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
"""
    # Insert it before redis
    content = content.replace("  redis:", postgres_service + "\n  redis:")

# Fix depends_on for backend and celery
depends_str_1 = """    depends_on:
      redis:
        condition: service_started"""

depends_str_2 = """    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started"""

content = content.replace(depends_str_1, depends_str_2)

with open('docker-compose.yml', 'w') as f:
    f.write(content)

print("docker-compose reverted")
