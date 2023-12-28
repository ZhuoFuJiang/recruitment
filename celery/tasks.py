from celery import Celery

# 第一个参数是当前脚本的名称，第二个参数是broker的服务器地址
app = Celery('tasks', backend='redis://127.0.0.1', broker='redis://127.0.0.1')


@app.task
def add(x, y):
    return x + y
