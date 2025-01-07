from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# 创建 FastAPI 实例
app = FastAPI()

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 模板目录位置
templates = Jinja2Templates(directory="app/templates")

# 模拟一些用户数据
USERS = [
    {"id": 1, "name": "Alice", "age": 25, "bio": "I love hiking."},
    {"id": 2, "name": "Bob",   "age": 30, "bio": "Coffee enthusiast."},
    {"id": 3, "name": "Carol", "age": 28, "bio": "Movie fan."}
]

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """
    首页，示例演示在这里直接包含 user card 组件，
    也可以从后端把 USERS 数据传给模板，来渲染多个组件。
    """
    return templates.TemplateResponse("index.html",
                                     {"request": request,
                                      "users": USERS})

@app.get("/page2", response_class=HTMLResponse)
async def get_page2(request: Request):
    """
    第二个页面，也想使用同样的 'user card' 组件
    """
    return templates.TemplateResponse("page2.html",
                                     {"request": request,
                                      "users": USERS})

@app.get("/user_card/{user_id}", response_class=HTMLResponse)
async def get_user_card(request: Request, user_id: int):
    """
    用于给 HTMX 动态请求特定 user_id 的卡片组件
    """
    # 查找对应用户
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        return HTMLResponse(content="User not found", status_code=404)

    # 返回我们封装的模板片段
    return templates.TemplateResponse(
        "partials/_user_card.html",
        {"request": request, "user": user}
    )

@app.get("/error", response_class=HTMLResponse)
async def error_page():
    return HTMLResponse(
        content="<h1>Error occurred</h1>",
        status_code=500
    )