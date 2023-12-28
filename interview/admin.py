from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from interview import dingtalk
from interview.models import Candidate
import interview.candidate_fieldset as CF
# Register your models here.
import csv
from datetime import datetime
import logging

from jobs.models import Resume

logger = logging.getLogger(__name__)

exportable_fields = ('username', 'city', 'phone', 'bachelor_school', 'master_school',
                     'degree', 'first_result', 'first_interviewer_user', 'second_result', 'second_interviewer_user',
                     'hr_result', 'hr_score', 'hr_interviewer_user')


def export_model_as_csv(modeladmin, request, quertset):
    response = HttpResponse(content_type='text/csv')
    field_list = exportable_fields
    response['Content-Disposition'] = 'attachment; filename=recruitment-candidates-list-%s.csv' % (
        datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    # 写入表头
    writer = csv.writer(response)
    writer.writerow([quertset.model._meta.get_field(f).verbose_name.title() for f in field_list])

    for obj in quertset:
        # 单行的记录，写入到csv文件
        csv_line_values = []
        for field in field_list:
            field_object = quertset.model._meta.get_field(field)
            field_value = field_object.value_from_object(obj)
            csv_line_values.append(field_value)
        writer.writerow(csv_line_values)

    logger.info("%s exported %s candidate records" % (request.user, len(quertset)))
    return response


export_model_as_csv.short_description = u'导出为csv文件'
export_model_as_csv.allowed_permissions = ('export',)


def notify_interviewer(modeladmin, request, queryset):
    candidates = ""
    interviewers = ""
    for obj in queryset:
        candidates = obj.username + ";" + candidates
        interviewers = obj.first_interviewer_user.username + ";" + interviewers
    dingtalk.send("候选人 %s 进入面试环节，亲爱的面试官，请准备好面试: %s" % (candidates, interviewers))
    messages.add_message(request, messages.INFO, '已经成功发送面试通知')


notify_interviewer.short_description = u'通知一面面试官'
notify_interviewer.allowed_permissions = ('notify',)


class CandidateAdmin(admin.ModelAdmin):
    exclude = ('creator', 'create_date', 'modified_date')
    list_display = ('username', 'city', 'bachelor_school', 'get_resume', 'first_score', 'first_result', 'first_interviewer_user',
                    'second_result', 'second_interviewer_user', 'hr_score', 'hr_result', 'last_editor')

    actions = [export_model_as_csv, notify_interviewer, ]

    # 当前用户是否有导出权限
    def has_export_permission(self, request):
        opts = self.opts
        return request.user.has_perm('%s.%s' % (opts.app_label, "export"))

    # 当前用户是否有通知权限
    def has_notify_permission(self, request):
        opts = self.opts
        return request.user.has_perm('%s.%s' % (opts.app_label, "notify"))

    # 筛选条件
    list_filter = ('city', 'first_result', 'second_result', 'hr_result', 'first_interviewer_user', 'second_interviewer_user',
                   'hr_interviewer_user')
    # 查询字段
    search_fields = ('username', 'phone', 'email', 'bachelor_school')

    ordering = ('hr_result', 'second_result', 'first_result')

    default_list_editable = ('first_interviewer_user', 'second_interviewer_user', )

    def get_resume(self, obj):
        if not obj.phone:
            return ""
        resumes = Resume.objects.filter(phone=obj.phone)
        if resumes and len(resumes) > 0:
            return mark_safe(u'<a href="/resume/%s" target="_blank">%s</a' % (resumes[0].id, "查看简历"))
        return ""

    get_resume.short_description = '查看简历'
    # 因为用了html标签
    get_resume.allow_tags = True

    def get_list_editable(self, request):
        group_names = self.get_group_names(request.user)
        if request.user.is_superuser or 'hr' in group_names:
            return self.default_list_editable
        return ()

    # hr或者超级用户可以在列表页直接修改的字段
    def get_changelist_instance(self, request):
        self.list_editable = self.get_list_editable(request)
        return super(CandidateAdmin, self).get_changelist_instance(request)

    # readonly_fields = ('first_interviewer_user', 'second_interviewer_user')
    # 获取组名
    def get_group_names(self, user):
        group_names = []
        for g in user.groups.all():
            group_names.append(g.name)
        return group_names

    # 不同角色查询的条目
    def get_queryset(self, request):
        qs = super(CandidateAdmin, self).get_queryset(request)

        group_names = self.get_group_names(request.user)
        if request.user.is_superuser or 'hr' in group_names:
            return qs

        return Candidate.objects.filter(Q(first_interviewer_user=request.user) | Q(second_interviewer_user=request.user))

    # 面试官本身不能修改一面面试官、二面面试官信息
    def get_readonly_fields(self, request, obj=None):
        group_name = self.get_group_names(request.user)

        if 'interview' in group_name:
            logger.info("interviewer is in user's group for %s" % request.user.username)
            return ('first_interviewer_user', 'second_interviewer_user', )
        return ()

    # 不同角色展示不同详细名目
    def get_fieldsets(self, request, obj=None):
        group_name = self.get_group_names(request.user)

        if 'interview' in group_name and obj.first_interviewer_user == request.user:
            return CF.default_fieldsets_first
        if 'interview' in group_name and obj.second_interviewer_user == request.user:
            return CF.default_fieldsets_second
        return CF.default_fieldsets


admin.site.register(Candidate, CandidateAdmin)
