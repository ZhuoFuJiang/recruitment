from django.urls import path, include, re_path
from django.conf import settings
from jobs import views

urlpatterns = (
    # 职位列表
    re_path(r'^joblist/', views.joblist, name='joblist'),
    re_path(r'^job/(?P<job_id>\d+)', views.detail, name='detail'),
    # 首页自动跳转到职位列表
    re_path(r"^$", views.joblist, name='name'),
    # 提交简历
    path("resume/add/", views.ResumeCreateView.as_view(), name='resume-add'),
    path(r'resume/<int:pk>', views.ResumeDetailView.as_view(), name='resume-detail'),
    # 管理员创建hr账号的页面
    path('create_hr_user/', views.create_hr_user, name='create_hr_user'),
)


if settings.DEBUG:
    # 有xss漏洞的视图页面
    urlpatterns += (re_path(r"^detail_resume/(?P<resume_id>\d+)/", views.detail_resume, name='detail_resume'), )
