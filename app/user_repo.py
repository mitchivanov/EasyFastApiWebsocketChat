import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Room, RoomMember
from typing import Optional, List, Dict
from app.database import AsyncSessionLocal


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def create_user(first_name: str, last_name: str, username: str, password: str, session: AsyncSession) -> Optional[User]:
    user_exists = await session.execute(select(User).where(User.username == username))
    if user_exists.scalar_one_or_none():
        return None
    
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        password_hash=hash_password(password)
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user
        
async def authenticate_user(username: str, password: str, session: AsyncSession) -> Optional[User]:
    task = select(User).where(User.username == username)
    result = await session.execute(task)
    user = result.scalar_one_or_none()
    if user is None:
        return None
    
    if str(user.password_hash) == hash_password(password):
        return user
    
    return None


async def get_user_by_username(username: str, session: AsyncSession) -> Optional[User]:
    task = select(User).where(User.username == username)
    result = await session.execute(task)
    user = result.scalar_one_or_none()
    return user


async def get_user_by_id(user_id: int, session: AsyncSession) -> Optional[User]:
    task = select(User).where(User.id == user_id)
    result = await session.execute(task)
    user = result.scalar_one_or_none()
    return user
    
async def create_room(name: str, owner_id: int, session: AsyncSession) -> Optional[Room]:
    task = select(Room).where(Room.name == name)
    result = await session.execute(task)
    room = result.scalar_one_or_none()
    if room:
        return None
    
    new_room = Room(
        name=name,
        owner_id=owner_id
    )
    session.add(new_room)
    await session.commit()
    await session.refresh(new_room)
    return new_room


async def get_room_by_id(room_id: int, session: AsyncSession) -> Optional[Room]:
    task = select(Room).where(Room.id == room_id)
    result = await session.execute(task)
    return result.scalar_one_or_none()


async def invite_user_to_room(room_id: int, username: str, inviter_id: int, session: AsyncSession) -> Optional[Dict]:
    room = await get_room_by_id(room_id, session)
    if not room:
        return {"success": False, "error": "Комната не найдена"}
    
    if room.owner_id != inviter_id:
        return {"success": False, "error": "Только владелец может приглашать"}
    
    user = await get_user_by_username(username, session)
    if not user:
        return {"success": False, "error": "Пользователь не найден"}
    
    if user.id == room.owner_id:
        return {"success": False, "error": "Владелец уже имеет доступ"}
    
    existing = await session.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user.id
        )
    )
    if existing.scalar_one_or_none():
        return {"success": False, "error": "Пользователь уже приглашен"}
    
    new_member = RoomMember(room_id=room_id, user_id=user.id)
    session.add(new_member)
    await session.commit()
    return {"success": True, "message": f"Пользователь {username} приглашен"}


async def remove_user_from_room(room_id: int, user_id: int, remover_id: int, session: AsyncSession) -> Optional[Dict]:
    room = await get_room_by_id(room_id, session)
    if not room:
        return {"success": False, "error": "Комната не найдена"}
    
    if room.owner_id != remover_id:
        return {"success": False, "error": "Только владелец может удалять участников"}
    
    if user_id == room.owner_id:
        return {"success": False, "error": "Нельзя удалить владельца"}
    
    result = await session.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        return {"success": False, "error": "Пользователь не является участником"}
    
    await session.delete(member)
    await session.commit()
    return {"success": True, "message": "Участник удален"}


async def get_room_members(room_id: int, session: AsyncSession) -> List[Dict]:
    room = await get_room_by_id(room_id, session)
    if not room:
        return []
    
    members_list = [
        {
            "id": room.owner.id,
            "username": room.owner.username,
            "first_name": room.owner.first_name,
            "last_name": room.owner.last_name,
            "is_owner": True
        }
    ]
    
    result = await session.execute(
        select(RoomMember).where(RoomMember.room_id == room_id)
    )
    memberships = result.scalars().all()
    
    for membership in memberships:
        user = await get_user_by_id(membership.user_id, session)
        if user:
            members_list.append({
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_owner": False
            })
    
    return members_list


async def check_user_access_to_room(room_id: int, user_id: int, session: AsyncSession) -> bool:
    room = await get_room_by_id(room_id, session)
    if not room:
        return False
    
    if room.owner_id == user_id:
        return True
    
    result = await session.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none() is not None


async def get_user_rooms(user_id: int) -> Dict[str, List[Dict]]:
    async with AsyncSessionLocal() as session:
        owned_stmt = select(Room).where(Room.owner_id == user_id).order_by(Room.created_at.desc())
        owned_result = await session.execute(owned_stmt)
        owned_rooms = owned_result.scalars().all()
        
        invited_stmt = (
            select(Room)
            .join(RoomMember, Room.id == RoomMember.room_id)
            .where(RoomMember.user_id == user_id)
            .order_by(Room.created_at.desc())
        )
        invited_result = await session.execute(invited_stmt)
        invited_rooms = invited_result.scalars().all()
        
        return {
            "owned": [
                {
                    "id": room.id,
                    "name": room.name,
                    "created_at": room.created_at.strftime("%Y-%m-%d %H:%M"),
                    "is_owner": True
                }
                for room in owned_rooms
            ],
            "invited": [
                {
                    "id": room.id,
                    "name": room.name,
                    "created_at": room.created_at.strftime("%Y-%m-%d %H:%M"),
                    "is_owner": False
                }
                for room in invited_rooms
            ]
        }