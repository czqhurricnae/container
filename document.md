## 无法在数据库 models中,从 `db`初始化所在的模块中导入 `db`
![](http://7xtyap.com1.z0.glb.clouddn.com/Python_2_7_11_Shell_Sun_Jul_10_09_18_21_2016.png)
修改后的结构

1.因为在同样的一个文件`my_app\__init__.py`中,需要使用
```python
from flask_script import Shell, Manager
manager = Manager(app)
def _make_context():
        return dict(app=app, db=db, Tool=Tool)
manager.add_command('shell', Shell(make_context=_make_context))
```
来生成`shell`命令和上下文,而`Tool`类是从`models`中导入而来(`app`,`db`都是在
`my_app\__init__.py`中初始化来的)
```python
from models import Tool
```
然而在`my_app\models.py`中需要`db`类,就将其从`my_app\__init__.py`导入
```python
from my_app import db
```
这样就导致了循环导入,所以会导致错误

解决的办法如下:
![](http://7xtyap.com1.z0.glb.clouddn.com/Python_2_7_11_Shell_Sun_Jul_10_10_00_14_2016.png)

## 使用 `flask-script`为 `shell`添加命令和上下文,但是没有出现所需效果
如下图是需要的效果:
![](http://7xtyap.com1.z0.glb.clouddn.com/_Sun_Jul_10_10_16_09_2016.png)

解决办法如下:
![](http://7xtyap.com1.z0.glb.clouddn.com/Python_2_7_11_Shell_Sun_Jul_10_10_23_31_2016.png)

## 对数据库中含有中文的行 (表)进行查询时,在 console中使用 print输出出现`UnicodeEncodeError`错误
### 错误的现象
![](http://7xtyap.com1.z0.glb.clouddn.com/Python_2_7_11_Shell_Sun_Jul_10_13_45_29_2016.png)

### 错误的原因
![](http://7xtyap.com1.z0.glb.clouddn.com/Python_2_7_11_Shell_Sun_Jul_10_13_33_13_2016.png)
其实就是在 `ordinal not in range(128).md`这个文章中讲的,console要输出`unicode`的字符串,就必须先进行
`encode`而系统的编码是 `ascii`只能 `encode`1-127之间的 `unicode`,中文字符不在范围内,出现错误.最理想的状况是 `encode`没有出现错误,
而print输出也是乱码,因为 `因为控制台输出窗口按照ascii编码输出utf8编码的字符串.`,正如文章讲到.

### 将数据库模型中 `Unicode`或者 `UnicodeText`都定义成 `String`后,写入数据时出现错误
修改后:
```python
class Tool(db.Model):
    __tablename__ = 'tool'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64))
    size = db.Column(db.String(64))
    number = db.Column(db.Integer)
    description = db.Column(db.String(64))

    def __init__(self, name, size, number, description):
        self.name = name
        self.size = size
        self.number = number
        self.description = description
```

* 写入数据库时,直接使用 `str`的中文
```pyhton
>>> t = Tool('一字', '小', 1, '无')
>>> db.session.add(t)
>>> db.session.commit()
```

产生错误

```python
ProgrammingError: (sqlite3.ProgrammingError) You must not use 8-bit bytestrings unless you use a text_factory that can interpret 8-bit bytestrings (like text_factory = str). It is highly r
ecommended that you instead just switch your application to Unicode strings. [SQL: u'INSERT INTO tool (name, size, number, description) VALUES (?, ?, ?, ?)'] [parameters: ('\xe4\xb8\x80\xe
5\xad\x97', '\xe5\xb0\x8f', 1, '\xe6\x97\xa0')]
```

* 使用 `unicode`中文
产生错误

```python
>>> t = Tool(u'一字',u '小', 1,u '无')
  File "<console>", line 1
    t = Tool(u'涓€瀛?,u '灏?, 1,u '鏃?)
                             ^
SyntaxError: invalid syntax

```

### 数据库模型定义对于字符的只是用 `Unicode`或者 `UnicodeText`
* 写入数据库,使用`unicode`中文,结果正常写入

```python
>>> t = Tool(u'一字', u'小', 1, u'无')
>>> db.session.add(t)
>>> db.session.commit()
```

* 写入数据库,使用`str`中文,
```python
>>> t = Tool('锤子', '橡胶', 4, '无')
>>> db.session.add(t)
```

进行提交时出现错误:

```python
>>> t.session.commit()
```

```python
ProgrammingError: (sqlite3.ProgrammingError) You must not use 8-bit bytestrings unless you use a text_factory that can interpret 8-bit bytestrings (like text_factory = str). It is highly r
ecommended that you instead just switch your application to Unicode strings. [SQL: u'INSERT INTO tool (name, size, number, description) VALUES (?, ?, ?, ?)'] [parameters: ('\xe9\x94\xa4\xe
5\xad\x90', '\xe6\xa9\xa1\xe8\x83\xb6', 4, '\xe6\x97\xa0')]

```

* 查询时直接使用字符串,出现错误
```python
>>> s = Tool.query.filter_by(name = 一字).first()
  File "<console>", line 1
    s = Tool.query.filter_by(name = 涓€瀛?.first()
                                    ^
SyntaxError: invalid syntax
```

* 查询时使用 `str`的中文
```python
s = Tool.query.filter_by(name = '一字').first()
```
出现错误:

```python
ProgrammingError: (sqlite3.ProgrammingError) You must not use 8-bit bytestrings unless you use a text_factory that can interpret 8-bit bytestrings (like text_factory = str). It is highly r
ecommended that you instead just switch your application to Unicode strings. [SQL: u'SELECT tool.id AS tool_id, tool.name AS tool_name, tool.size AS tool_size, tool.number AS tool_number,
tool.description AS tool_description \nFROM tool \nWHERE tool.name = ?\n LIMIT ? OFFSET ?'] [parameters: ('\xe4\xb8\x80\xe5\xad\x97', 1, 0)]
```

* 查询时使用 `str`的数字,字母

```python
>>> s = Tool.query.filter_by(name = 'something').first()
C:\Users\czq\OneDrive\exercise\tool\tool_env\lib\site-packages\sqlalchemy\sql\sqltypes.py:185: SAWarning: Unicode type received non-unicode bind param value 'something'. (this warning may
be suppressed after 10 occurrences)
  (util.ellipses_string(value),))
>>> s = Tool.query.filter_by(name = '5/16').first()
C:\Users\czq\OneDrive\exercise\tool\tool_env\lib\site-packages\sqlalchemy\sql\sqltypes.py:185: SAWarning: Unicode type received non-unicode bind param value '5/16'. (this warning may be su
ppressed after 10 occurrences)
  (util.ellipses_string(value),))
```

### 录入和查询的问题解决了,如何解决在 console中自动完成使用 `utf-8`进行 `encode`的问题呢?
### 解决输出时乱码的方法
```python
import sys
reload(sys)
sys.setdefaultencoding('gb2312')
```

## 出现了循环导入的错误`ImportError: cannot import name db`
![](http://7xtyap.com1.z0.glb.clouddn.com/Python_2_7_11_Shell_Mon_Jul_11_22_10_08_2016.png)
![](http://7xtyap.com1.z0.glb.clouddn.com/Python_2_7_11_Shell_Mon_Jul_11_21_37_21_2016.png)
最后使用`create_app`工厂函数解决了这个bug,出现bug的原因是在`my_app/__init__.py`中没有使用工厂函数时,
使用了语句 `from . index import index_blueprint`来导入 `my_app/index/__init__.py`中的蓝图,接下来因语句 `from . import views`进入到 `views.py`中,
在 `views`中,因 `from ..models import Project, Tool`进入到 `models`,`models`中出现语句 `from . import db`,因为这样绕了一圈,
最开始的 `my_app/__init__.py`要到 `from . import db`中的 `.`即 `my_app/__init__.py`中导入`db`,好了第一次导入自身后,在自身的'复制品'中
还是有一样的`from . index import index_blueprint`又导致了下一次的导入,这样造成了`循环导入`.

解决循环导入的办法就是对可能造成循环导入的语句放在 `局部上下文`中,于是将 `from . index import index_blueprint`放在工厂函数`create_app`中.

## 关于`flask_whooshalchemyplus`在工厂函数`create_app`会出现错误?
`flask_whooshalchemyplus`没有正常的flask插件初始化的方法,如下的代码是错误的
```python
from flask import Flask
import flask_whooshalchemyplus
whoosh = flask_whooshalchemyplus()

def create_app():
    app = Flask(__name__)
    whoosh.init_app(app)
```

或者在`my_app/__init__.py`中 `flask_whooshalchemyplus.init_app(app)`的初始化放在 `flask_sqlalchemy`之前,会出现错误 `KeyError: 'sqlalchemy'`,就像如下

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import flask_whooshalchemyplus
db = SQLAlchemy()
def create_app():
    app = Flask(__name__)
    ...
    ...
    db.init_app(app)
    flask_whooshalchemyplus.init_app(app)
```

## ` flask_whooshalchemyplus`的`whoosh_index`索引文件生成函数的初始化
`whoosh_index`需要两个函数一个是flask实例,另一个是 `flask_sqlalchemy`的 `models`中定义的一个数据类,所以最好将其的初始化放在 `run.py`中,如下

```python
from flask_whooshalchemyplus import whoosh_index
from my_app import create_app,db
from my_app.models import Tool, Project
app = create_app()
whoosh_index(app, Project)
```

## 使用flask的 flash功能,没有配置 `app`的 `SECRET_KEY`出现错误
![](http://7xtyap.com1.z0.glb.clouddn.com/Python_2_7_11_Shell_Wed_Jul_13_20_34_30_2016.png)
使用
```python
app.secret_key = 'hard to guess'
```
进行配置.

## AttributeError: 'module' object has no attribute 'init_app'
因为包 `admin`名称与 `flask-admin`初始化时的实例名称 `admin`一样,编译
时将 `admin`当成一个包来处理 `admin.init_app(app)`
![](http://7xtyap.com1.z0.glb.clouddn.com/screenshot_py_(2_7_11)_Sat_Jul_16_16_33_51_2016.png)

## 使用 `python run.py db init`出现 `KeyError: 'migrate'的错误
原来是自己没有初始化完全好少了一句 `migrate = Migrate(app, db)`.

## 使用flask-admin自定义 `ModelView`时出现 `AttributeError: type object 'Project' has no attribute 't'
`
因为在 `column_searchable_list = 'title'`的 `'title'`少加了括号,实际上 `column_searchable_list`
的参数应该是元组,改成 `column_searchable_list = ('title',)`就好

~~~python
class ProjectModelView(ModelView):
    column_searchable_list = 'title'
~~~

## 自定义flask-admin的 field
![](http://7xtyap.com1.z0.glb.clouddn.com/Mon_Jul_18_22_33_56_2016.png)

```python
class ToolModelView(ModelView):
    form_widget_args = {
        'description':{
            'column':20
        }
    }
```

## flask-admin的初始化
![](http://7xtyap.com1.z0.glb.clouddn.com/_Tue_Jul_19_11_39_31_2016.png)
![](http://7xtyap.com1.z0.glb.clouddn.com/screenshot_py_(2_7_11)_Tue_Jul_19_11_45_46_2016.png)

在定义了endpoint后,在 `add_tool.html`就可以使用 `<div><a href = " {{url_for('test2.upload')}}">{{'test2.upload'}}</a>`</div>`,
点击超链接后跳转到 URL`http://127.0.0.1:5000/admin/test2/`,其中 `test2`是定义过的 `endpoint`,`upload`是定义了 `endpoint`的 `class UpLoad(BaseView)`类的视图函数名.

```python
class UpLoad(BaseView):
    @expose('/', methods = ['GET','POST'])
    def upload(self):
        return self.render('add_tools.html')

admin.add_view(UpLoad(name = u'添加工具1',category= u'添加工具',endpoint= 'test1'))
admin.add_view(UpLoad(name = u'添加工具2',category= u'添加工具',endpoint= 'test2'))
```
![](http://7xtyap.com1.z0.glb.clouddn.com/screenshot_py_(2_7_11)_Tue_Jul_19_11_52_59_2016.png)

# 使用 `os.walk`的注意事项
```
import os
for root, dircts, files in os.walk('C:\Users\czq\OneDrive\exercise\tool\my_app'):
    print root,dircts,files

```
这样是没有输出结果的,记得 `os.walk`的参数是使用真实绝对路径,如下
```
import os
for root, dircts, files in os.walk(r'C:\Users\czq\OneDrive\exercise\tool\my_app'):
    print root,dircts,files
```

## EnvironmentError: mysql_config not found
解决办法

```python
sudo apt-get install libmysqlclient-dev
```
