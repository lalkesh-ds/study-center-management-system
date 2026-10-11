import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> RefreshToken:
        token_obj = RefreshToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
            user_agent=user_agent,
            ip_address=ip_address
        )
        self.db.add(token_obj)
        self.db.commit()
        self.db.refresh(token_obj)
        return token_obj

    def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.execute(stmt).scalars().first()

    def revoke(self, token_obj: RefreshToken) -> RefreshToken:
        token_obj.is_revoked = True
        token_obj.revoked_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(token_obj)
        return token_obj

    def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
        tokens = list(self.db.execute(stmt).scalars().all())
        now = datetime.now(timezone.utc)
        for t in tokens:
            t.is_revoked = True
            t.revoked_at = now
        self.db.commit()
        return len(tokens)
