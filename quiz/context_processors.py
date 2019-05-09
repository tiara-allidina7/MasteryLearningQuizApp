from config import dashboard_config


def course_name(request):
    return {'COURSE_NAME': dashboard_config.course_name}
