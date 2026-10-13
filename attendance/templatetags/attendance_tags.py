from django import template

register = template.Library()

@register.filter
def dict_get_status(record_dict, student_id):
    if not record_dict or student_id not in record_dict:
        return 'PRESENT'
    return record_dict[student_id].status

@register.filter
def dict_get_remarks(record_dict, student_id):
    if not record_dict or student_id not in record_dict:
        return ''
    return record_dict[student_id].remarks or ''
