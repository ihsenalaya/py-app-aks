import os
import time
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pydantic import ConfigDict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Boolean

# =========================
# Config DB via variables d'environnement
# =========================
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppass")
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =========================
# Modèle SQLAlchemy
# =========================
class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    done = Column(Boolean, default=False)

# =========================
# Schémas Pydantic
# =========================
class TodoIn(BaseModel):
    title: str
    done: bool = False

class TodoOut(TodoIn):
    id: int
    model_config = ConfigDict(from_attributes=True)

# =========================
# App FastAPI
# =========================
app = FastAPI(title="AKS + PostgreSQL Demo (simple)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Démarrage avec retry sur la DB pour éviter CrashLoop si Postgres n'est pas prêt
MAX_TRIES = 15
SLEEP_SECONDS = 2

@app.on_event("startup")
def on_startup():
    tries = 0
    while True:
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception:
            tries += 1
            if tries >= MAX_TRIES:
                raise
            time.sleep(SLEEP_SECONDS)

# Dépendance DB
from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# Routes (plusieurs chemins pour tester un Ingress)
# =========================
@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
      <body style='font-family:system-ui;padding:24px'>
        <h1>FastAPI + PostgreSQL</h1>
        <p>Routes de test :</p>
        <ul>
          <li><a href='/hello'>/hello</a></li>
          <li><a href='/healthz'>/healthz</a></li>
          <li><a href='/todos'>/todos</a></li>
          <li><a href='/docs'>/docs (Swagger)</a></li>
        </ul>
      </body>
    </html>
    """

@app.get("/hello")
def hello():
    return {"message": "hello from FastAPI"}

@app.get("/healthz")
def healthz():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail="db not ready")

@app.get("/todos", response_model=List[TodoOut])
def list_todos():
    with get_db() as db:
        items = db.query(Todo).order_by(Todo.id.asc()).all()
        return items

@app.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(todo: TodoIn):
    with get_db() as db:
        obj = Todo(title=todo.title, done=todo.done)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

@app.put("/todos/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, todo: TodoIn):
    with get_db() as db:
        obj = db.get(Todo, todo_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        obj.title = todo.title
        obj.done = todo.done
        db.commit()
        db.refresh(obj)
        return obj

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    with get_db() as db:
        obj = db.get(Todo, todo_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        db.delete(obj)
        db.commit()
        return