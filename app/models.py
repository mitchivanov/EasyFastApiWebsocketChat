from sqlalchemy import Column, Integer, String, DateTime, Index, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rooms = relationship("Room", back_populates="owner")
    memberships = relationship("RoomMember", back_populates="user", cascade="all, delete-orphan")
    
    
class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="rooms")
    members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")


class RoomMember(Base):
    __tablename__ = "room_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    room = relationship("Room", back_populates="members")
    user = relationship("User", back_populates="memberships")
    
    __table_args__ = (
        UniqueConstraint('room_id', 'user_id', name='unique_room_member'),
        Index('idx_room_member', 'room_id', 'user_id'),
    )


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_room_id', 'room_id'),
    )

