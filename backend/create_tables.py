from database import engine, Base
import models.domain

Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
