from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import requests

class ScriptKillApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 添加标题
        self.title_label = Label(text='剧本杀 AI 助手', size_hint_y=None, height=50)
        self.layout.add_widget(self.title_label)
        
        # 添加登录表单
        self.username_input = TextInput(hint_text='用户名', multiline=False)
        self.password_input = TextInput(hint_text='密码', password=True, multiline=False)
        self.layout.add_widget(self.username_input)
        self.layout.add_widget(self.password_input)
        
        # 添加按钮
        self.login_button = Button(text='登录', size_hint_y=None, height=50)
        self.login_button.bind(on_press=self.login)
        self.layout.add_widget(self.login_button)
        
        self.register_button = Button(text='注册', size_hint_y=None, height=50)
        self.register_button.bind(on_press=self.register)
        self.layout.add_widget(self.register_button)
        
        return self.layout
    
    def login(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        
        try:
            response = requests.post('http://localhost:8000/token', 
                                  data={'username': username, 'password': password})
            if response.status_code == 200:
                token = response.json()['access_token']
                # 保存 token
                with open('token.txt', 'w') as f:
                    f.write(token)
                self.title_label.text = '登录成功！'
            else:
                self.title_label.text = '登录失败，请重试'
        except Exception as e:
            self.title_label.text = f'错误: {str(e)}'
    
    def register(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        
        try:
            response = requests.post('http://localhost:8000/register', 
                                  json={'username': username, 'password': password})
            if response.status_code == 200:
                self.title_label.text = '注册成功！'
            else:
                self.title_label.text = '注册失败，请重试'
        except Exception as e:
            self.title_label.text = f'错误: {str(e)}'

if __name__ == '__main__':
    ScriptKillApp().run() 