使用 FastAPI + HTMX 实现组件化

思考，持续 3m 24s

下面给出一个**示例项目**，展示在 **FastAPI + HTMX + 原生 HTML/CSS/JS** 的前提下，如何实现类似 “Component” 的可复用 UI 模块。  
我们会用到的关键技术要点包括：

1. **FastAPI**：作为后端框架，提供 API 和 HTML 模板渲染。
2. **Jinja2**（FastAPI 内置对 Jinja2 的支持）：实现模板继承与复用（可以类比“组件”）。
3. **HTMX**：通过在前端 HTML 中添加特殊属性（如 `hx-get`、`hx-target`），实现局部刷新与动态加载“组件”模板。
4. **纯原生 HTML/CSS/JS**：在前端，不依赖前端框架（如 React、Vue 等），仅使用基础的 HTML/CSS/JS。

---

## 一、项目结构

我们先给出一个示例的项目结构，方便你在 IDE 或者命令行里快速搭建：

```bash
fastapi-htmx-component/
├── app/
│   ├── main.py
│   ├── templates/
│   │   ├── layout.html
│   │   ├── index.html
│   │   ├── page2.html
│   │   └── partials/
│   │       └── _user_card.html
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── script.js
├── requirements.txt
└── README.md
```

接下来会按照这个结构，一步一步讲解各文件的内容和作用。

> **注意**：文件/文件夹命名、放置位置等都可以根据你自己的习惯做调整，这里只是提供一种常见的可行示例。

---

## 二、准备工作

1. **创建并激活虚拟环境**（可选但推荐）

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或者 Windows
# venv\Scripts\activate
```

2. **安装依赖**

- `fastapi`
- `uvicorn` (部署/开发时的服务器)
- `jinja2` (FastAPI 默认依赖)
- `htmx` (前端直接用 `<script>` 引入即可，不一定要 pip 安装)

创建 `requirements.txt` 并写入：

```txt
fastapi==0.95.2
uvicorn==0.21.1
```

_（这里演示指定了某些版本，你也可以用最新版本或不指定版本）_

然后执行：

```bash
pip install -r requirements.txt
```

3. **目录说明**

- `app/main.py`：主入口，启动 FastAPI。
- `app/templates/`：存放所有 Jinja2 模板文件（主页面、子页面、partials 等）。
- `app/static/`：存放静态文件（CSS、JS、图片等）。
- `app/templates/partials/`：我们要创建的可复用“组件”模板文件夹。这里示例一个 `_user_card.html`。
- `requirements.txt`：项目依赖。
- `README.md`：项目说明。

---

## 三、编写后端 (FastAPI)

### 1\. `main.py`

在 `app/main.py` 中编写核心代码，如下：

```python
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
```

> 这里用 `get_user_card` 这个接口示例，展示**怎么让前端通过 HTMX 动态请求单个用户卡片**。这样我们可以在其它页面里用 `<div hx-get="/user_card/2">` 之类的方式去加载组件。

---

## 四、编写模板

### 1\. `layout.html`：公共布局

示例用 Jinja2 的 **模板继承** 技术。做一个最基本的布局模板 `app/templates/layout.html`：

```html
<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="UTF-8" />
		<title>{% block title %}FastAPI + HTMX Component{% endblock %}</title>

		<!-- 引入 HTMX -->
		<script src="https://unpkg.com/htmx.org@1.8.4"></script>

		<!-- 引入公共 CSS -->
		<link
			rel="stylesheet"
			href="{{ url_for('static', path='css/style.css') }}"
		/>
	</head>
	<body>
		<header>
			<h1>My Web Application</h1>
			<nav>
				<a href="{{ url_for('get_index') }}">Home</a> |
				<a href="{{ url_for('get_page2') }}">Page2</a>
			</nav>
		</header>

		<!-- 页面主体内容 -->
		<main>{% block content %}{% endblock %}</main>

		<!-- 公共 JS -->
		<script src="{{ url_for('static', path='js/script.js') }}"></script>
	</body>
</html>
```

### 2\. `index.html`：首页

`app/templates/index.html`，继承自 `layout.html`，同时演示如何复用 `_user_card.html` 模板。如果不想做动态刷新，直接在后端把数据传进来，然后 Jinja2 进行 for-loop 即可。

```html
{% extends "layout.html" %} {% block title %}Home{% endblock %} {% block content
%}
<h2>Welcome to the Home Page</h2>

<!-- 直接渲染多个用户卡片，users 来自后端 context -->
<div class="user-cards">
	{% for user in users %}
	<!-- 通过 include 语法，把 _user_card.html 嵌入进来 -->
	{% include "partials/_user_card.html" %} {% endfor %}
</div>

{% endblock %}
```

这里的 `users` 来自 `get_index` 路由里返回的 `{"request": request, "users": USERS}`。  
`{% include "partials/_user_card.html" %}` 表示直接嵌入这个组件模板。

### 3\. `page2.html`：第二个页面

`app/templates/page2.html`，同理，也继承自 `layout.html` 并复用 user card。这次再示例一下 **HTMX 动态加载** 的写法（可对比上面的静态 include）：

```html
{% extends "layout.html" %} {% block title %}Page2{% endblock %} {% block
content %}
<h2>This is Page2</h2>

<!-- 如果只是想重复使用，也可以跟 index.html 一样 static include -->
<!-- 下面展示另外一种思路：让用户点击按钮时，才动态加载某个特定用户的卡片 -->

<button
	hx-get="/user_card/1"
	hx-target="#dynamic-user-card"
	hx-swap="innerHTML"
>
	Load Alice's Card
</button>

<button
	hx-get="/user_card/2"
	hx-target="#dynamic-user-card"
	hx-swap="innerHTML"
>
	Load Bob's Card
</button>

<button
	hx-get="/user_card/3"
	hx-target="#dynamic-user-card"
	hx-swap="innerHTML"
>
	Load Carol's Card
</button>

<div id="dynamic-user-card" class="user-cards">
	<!-- HTMX 会在点击按钮后，把 /user_card/{id} 的返回 HTML 注入到这里 -->
</div>

{% endblock %}
```

> 通过 HTMX 的 `hx-get`、`hx-target`、`hx-swap` 属性，可以很直观地在页面局部插入一个我们定义好的模板片段。

### 4\. `partials/_user_card.html`：可复用“组件”模板

`app/templates/partials/_user_card.html`，这是一个**纯粹**的模板片段，不包含 `<html>`、`<body>` 等基础结构。我们假设这是你想复用的“组件”，比如用户卡片：

```html
<div class="user-card">
	<h3>{{ user.name }}</h3>
	<p>Age: {{ user.age }}</p>
	<p>Bio: {{ user.bio }}</p>
</div>
```

---

## 五、前端静态资源

### 1\. CSS：`app/static/css/style.css`

简单写个示例样式：

```css
body {
	font-family: sans-serif;
	margin: 0;
	padding: 0;
}

header {
	background-color: #efefef;
	padding: 1em;
}

header nav a {
	margin: 0 10px;
	text-decoration: none;
	color: #333;
}

.user-cards {
	display: flex;
	gap: 1rem;
	flex-wrap: wrap;
	margin: 1em;
}

.user-card {
	border: 1px solid #ccc;
	padding: 1em;
	border-radius: 8px;
	width: 150px;
}
```

### 2\. JS：`app/static/js/script.js`

如果需要一些通用的前端脚本，可以放在这里。比如简单写个示例：

```js
console.log("Script loaded!");
```

---

## 六、运行与测试

1. **启动服务**

在项目根目录下执行：

```bash
uvicorn app.main:app --reload
```

这会使用 `--reload` 模式，让你修改代码后服务自动重启。 2. **访问页面**

打开浏览器访问：

- http://127.0.0.1:8000/  
  可以看到主页上渲染了多个用户卡片，这些卡片的 HTML 来自 `partials/_user_card.html`。
- http://127.0.0.1:8000/page2  
  可以在这里点击“Load Alice’s Card”/“Load Bob’s Card” 等按钮，局部加载并插入 `_user_card.html` 模板。

这样就实现了一个非常基础但完整的示例，说明**如何在 FastAPI + HTMX + 原生 HTML/CSS/JS** 环境里构建可复用的组件式模板（即“partials”）。

---

## 七、再补充一些思路

1. **Jinja2 include**

- 当你想要在编译时就把组件“插入”到多个页面，或者在 for-loop 中重复渲染组件时，Jinja2 的 `include` / `extends` 十分方便。
- 适用于页面在初始加载时就已经知道要渲染多少个组件，以及如何渲染。

2. **HTMX 动态加载**

- 当你想要**懒加载**或**动态加载**组件（例如用户点击按钮、下拉刷新、分页等），可以借助 HTMX 的局部刷新特性，后端提供一个单独渲染那个组件的 API 路由，就可以让前端拿到局部模板并插入指定区域。
- 适用于需要在页面上动态增删的组件场景。

3. **数据传递**

- 无论是静态 include 还是动态加载，实质都是：**后端获取数据 -> 渲染同一个模板片段 -> 返回 HTML -> 前端插入页面**。
- 所以组件中的数据可以用后端传递，也可以结合你的业务逻辑，用普通的数据库查询、API 请求等方式获取。

4. **命名约定**

- 多数人会使用带下划线 `_xxxx.html` 来表示“部分模板”或“组件模板”（partial）。
- 也有些人会直接放在 `partials/` 文件夹或者 `components/` 文件夹里。

通过这套机制，就可以在不使用 React、Vue、Angular 等前端框架的前提下，让你的组件逻辑（HTML、CSS、JS）都保持**相对独立并可复用**，同时具备**服务器端渲染**以及**HTMX 的前端动态交互**。

---

### 结语

以上示例展示了如何在不使用 React 等前端框架的情况下，基于 **FastAPI + HTMX + 纯 HTML/CSS/JS**，实现一套**可复用的“组件化”开发**思路。对于小型或中等规模的项目，这是非常轻量且可行的方案。

祝你编码愉快，若有更多问题，欢迎再来提问。
