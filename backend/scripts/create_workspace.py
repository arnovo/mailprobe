#!/usr/bin/env python3
"""Create workspace and add user as admin. Run after migrations.
Usage: python -m scripts.create_workspace --email user@example.com [--workspace-name "My Workspace"]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password
from app.models import User, Workspace, WorkspaceUser
from app.models.workspace import WorkspaceRole

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True, help="User email (must exist or will be created with password)")
    ap.add_argument("--password", default="changeme", help="Password if creating user")
    ap.add_argument("--workspace-name", default="Default", help="Workspace name")
    ap.add_argument("--workspace-slug", default="default", help="Workspace slug")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        r = db.execute(select(User).where(User.email == args.email))
        user = r.scalars().one_or_none()
        if not user:
            user = User(
                email=args.email,
                hashed_password=hash_password(args.password),
                full_name=args.email.split("@")[0],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created user: {user.email} (id={user.id})")
        else:
            print(f"Existing user: {user.email} (id={user.id})")

        r = db.execute(select(Workspace).where(Workspace.slug == args.workspace_slug))
        ws = r.scalars().one_or_none()
        if not ws:
            ws = Workspace(name=args.workspace_name, slug=args.workspace_slug, plan="free")
            db.add(ws)
            db.commit()
            db.refresh(ws)
            print(f"Created workspace: {ws.name} (id={ws.id}, slug={ws.slug})")
        else:
            print(f"Existing workspace: {ws.name} (id={ws.id})")

        r = db.execute(
            select(WorkspaceUser).where(
                WorkspaceUser.workspace_id == ws.id,
                WorkspaceUser.user_id == user.id,
            )
        )
        wu = r.scalars().one_or_none()
        if not wu:
            wu = WorkspaceUser(workspace_id=ws.id, user_id=user.id, role=WorkspaceRole.ADMIN)
            db.add(wu)
            db.commit()
            print(f"Added user to workspace as admin. X-Workspace-Id: {ws.id}")
        else:
            print(f"User already in workspace. X-Workspace-Id: {ws.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
