from .base import BaseRepository
from app.db.tables import User


class UserRepository(BaseRepository):
    base_table = User

    async def store(self, model: User) -> User:
        ret = await self._create(model, mute_conflict_exception=True)
        if ret is None:
            ret = await self._get_one(external_id=model.external_id, app_bundle=model.app_bundle)
        return ret

    async def get_by_external(self, external_id: str, app_bundle: str) -> User:
        return await self._get_one(external_id=external_id, app_bundle=app_bundle)

    async def get_by_id(self, model_id: int) -> User:
        return await self._get_one(id=model_id)

