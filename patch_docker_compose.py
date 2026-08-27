import re

with open('docker-compose.yml', 'r') as f:
    content = f.read()

# Replace backend DATABASE_URL
content = re.sub(
    r'- DATABASE_URL=postgresql://postgres:postgrespassword@postgres:5432/industrial_brain',
    r'- DATABASE_URL=postgresql://neondb_owner:npg_8KFDcHNlx3GA@ep-mute-haze-aoip5ik1-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require',
    content
)

# Remove postgres dependency from backend
backend_depends = """    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started"""
new_backend_depends = """    depends_on:
      redis:
        condition: service_started"""
content = content.replace(backend_depends, new_backend_depends)

with open('docker-compose.yml', 'w') as f:
    f.write(content)

print("docker-compose patched")
