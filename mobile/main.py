from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivy.config import Config
from kivy.core.text import LabelBase
import json
import os

# 注册中文字体
LabelBase.register(name='SimHei',
                  fn_regular='C:/Windows/Fonts/simhei.ttf')

# 设置窗口大小
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '600')
Window.size = (400, 600)

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # 标题
        title = Label(
            text='AI剧本杀',
            font_name='SimHei',
            font_size='24sp',
            size_hint_y=None,
            height=50
        )
        
        # 用户名输入框
        self.username = TextInput(
            multiline=False,
            hint_text='用户名',
            font_name='SimHei',
            size_hint_y=None,
            height=40,
            padding=10,
            text='test'
        )
        
        # 密码输入框
        self.password = TextInput(
            multiline=False,
            hint_text='密码',
            font_name='SimHei',
            password=True,
            size_hint_y=None,
            height=40,
            padding=10,
            text='123456'
        )
        
        # 登录按钮
        login_btn = Button(
            text='登录',
            font_name='SimHei',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        login_btn.bind(on_press=self.login)
        
        # 状态标签
        self.status_label = Label(
            text='',
            font_name='SimHei',
            size_hint_y=None,
            height=30,
            color=(1, 0, 0, 1)  # 红色
        )
        
        # 添加所有组件到布局
        layout.add_widget(title)
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(login_btn)
        layout.add_widget(self.status_label)
        
        # 添加布局到屏幕
        self.add_widget(layout)
    
    def login(self, instance):
        # 清除之前的状态信息
        self.status_label.text = '正在登录...'
        
        data = {
            'username': self.username.text,
            'password': self.password.text
        }
        
        # 检查输入是否为空
        if not data['username'] or not data['password']:
            self.status_label.text = '用户名和密码不能为空'
            return
            
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            # 修改为正确的API地址
            UrlRequest(
                'http://127.0.0.1:8000/token',
                req_body=f"username={data['username']}&password={data['password']}&grant_type=password",
                req_headers=headers,
                on_success=self.on_login_success,
                on_failure=self.on_login_error,
                on_error=self.on_login_error,
                timeout=10  # 添加超时设置
            )
        except Exception as e:
            self.status_label.text = f'连接错误: {str(e)}'
    
    def on_login_success(self, request, result):
        try:
            print(f"登录响应: {result}")  # 添加调试信息
            if isinstance(result, dict) and 'access_token' in result:
                App.get_running_app().token = result['access_token']
                self.status_label.text = '登录成功！'
                self.manager.current = 'game'
            else:
                self.status_label.text = f'登录失败：无效的响应格式 {result}'
        except Exception as e:
            self.status_label.text = f'处理响应时出错: {str(e)}'
    
    def on_login_error(self, request, error):
        print(f"登录错误: {error}")  # 添加调试信息
        if hasattr(error, 'args') and len(error.args) > 0:
            error_msg = error.args[0]
        else:
            error_msg = str(error)
        self.status_label.text = f'登录失败: {error_msg}'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # 标题
        title = Label(
            text='游戏大厅',
            font_name='SimHei',
            font_size='24sp',
            size_hint_y=None,
            height=50
        )
        
        # 游戏列表容器
        self.games_layout = BoxLayout(
            orientation='vertical',
            spacing=10,
            size_hint_y=0.7
        )
        
        # 刷新按钮
        refresh_btn = Button(
            text='刷新游戏列表',
            font_name='SimHei',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        refresh_btn.bind(on_press=self.refresh_games)
        
        # 创建游戏按钮
        create_btn = Button(
            text='创建新游戏',
            font_name='SimHei',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        create_btn.bind(on_press=self.create_game)
        
        # 添加所有组件到布局
        layout.add_widget(title)
        layout.add_widget(refresh_btn)
        layout.add_widget(self.games_layout)
        layout.add_widget(create_btn)
        
        # 添加布局到屏幕
        self.add_widget(layout)
    
    def refresh_games(self, instance):
        headers = {
            'Authorization': f'Bearer {App.get_running_app().token}'
        }
        UrlRequest(
            'http://localhost:8000/games',
            req_headers=headers,
            on_success=self.on_games_loaded
        )
    
    def on_games_loaded(self, request, result):
        self.games_layout.clear_widgets()
        for game in result:
            btn = Button(
                text=f"游戏 {game['id']}",
                font_name='SimHei',
                size_hint_y=None,
                height=40,
                background_color=(0.8, 0.8, 0.8, 1)
            )
            btn.bind(on_press=lambda x, g=game: self.join_game(g))
            self.games_layout.add_widget(btn)
    
    def create_game(self, instance):
        headers = {
            'Authorization': f'Bearer {App.get_running_app().token}',
            'Content-Type': 'application/json'
        }
        data = {
            'ai_count': 3,
            'is_all_ai': False
        }
        UrlRequest(
            'http://localhost:8000/game/start',
            req_body=json.dumps(data),
            req_headers=headers,
            on_success=self.on_game_created
        )
    
    def on_game_created(self, request, result):
        self.refresh_games(None)

class GameApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.token = None
    
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    GameApp().run() 