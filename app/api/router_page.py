from fastapi import APIRouter, Request, Form, Cookie, Response, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.database import get_session
from app.user_repo import (
    create_user, authenticate_user, get_user_by_id, create_room,
    invite_user_to_room, remove_user_from_room, get_room_members,
    check_user_access_to_room, get_user_rooms
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

templates = Jinja2Templates(directory='app/templates')
router = APIRouter()


async def get_current_user(user_id: Optional[str] = Cookie(None), session: AsyncSession = Depends(get_session)):
    if not user_id:
        return None
    try:
        return await get_user_by_id(int(user_id), session)
    except:
        return None


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, user_id: Optional[str] = Cookie(None), session: AsyncSession = Depends(get_session)):
    user = await get_current_user(user_id, session)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    rooms = await get_user_rooms(user.id)
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,
        "rooms": rooms
    })


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    response: Response,
    first_name: str = Form(...),
    last_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    if password != password_confirm:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Пароли не совпадают"
        })
    
    user = await create_user(first_name, last_name, username, password, session)
    if not user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username уже занят"
        })
    
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(username, password, session)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверный username или пароль"
        })
    
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="user_id")
    return response


@router.post("/create_room")
async def create_room_endpoint(
    room_name: str = Form(...),
    user_id: Optional[str] = Cookie(None),
    session: AsyncSession = Depends(get_session)
):
    user = await get_current_user(user_id, session)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    await create_room(room_name, user.id, session)
    return RedirectResponse(url="/", status_code=302)


@router.post("/join_room", response_class=HTMLResponse)
async def join_room(
    request: Request,
    room_id: int = Form(...),
    user_id: Optional[str] = Cookie(None),
    session: AsyncSession = Depends(get_session)
):
    user = await get_current_user(user_id, session)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    has_access = await check_user_access_to_room(room_id, user.id, session)
    if not has_access:
        rooms = await get_user_rooms(user.id)
        return templates.TemplateResponse("home.html", {
            "request": request,
            "user": user,
            "rooms": rooms,
            "error": "У вас нет доступа к этой комнате"
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "room_id": room_id,
        "username": user.username,
        "user_id": user.id
    })


@router.post("/invite_user")
async def invite_user(
    room_id: int = Form(...),
    username: str = Form(...),
    user_id: Optional[str] = Cookie(None),
    session: AsyncSession = Depends(get_session)
):
    user = await get_current_user(user_id, session)
    if not user:
        return JSONResponse({"success": False, "error": "Не авторизован"}, status_code=401)
    
    result = await invite_user_to_room(room_id, username, user.id, session)
    return JSONResponse(result)


@router.post("/remove_member")
async def remove_member(
    room_id: int = Form(...),
    member_id: int = Form(...),
    user_id: Optional[str] = Cookie(None),
    session: AsyncSession = Depends(get_session)
):
    user = await get_current_user(user_id, session)
    if not user:
        return JSONResponse({"success": False, "error": "Не авторизован"}, status_code=401)
    
    result = await remove_user_from_room(room_id, member_id, user.id, session)
    return JSONResponse(result)


@router.get("/room/{room_id}/members")
async def get_members(
    room_id: int,
    user_id: Optional[str] = Cookie(None),
    session: AsyncSession = Depends(get_session)
):
    user = await get_current_user(user_id, session)
    if not user:
        return JSONResponse({"success": False, "error": "Не авторизован"}, status_code=401)
    
    has_access = await check_user_access_to_room(room_id, user.id, session)
    if not has_access:
        return JSONResponse({"success": False, "error": "Нет доступа"}, status_code=403)
    
    members = await get_room_members(room_id, session)
    return JSONResponse({"success": True, "members": members})
