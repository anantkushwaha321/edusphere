from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ActivityLog
from accounts.decorators import admin_required


@admin_required
def activity_log_list_view(request):
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('q', '').strip()

    logs_qs = ActivityLog.objects.select_related('user').all()

    if category_filter:
        logs_qs = logs_qs.filter(category=category_filter)
    if search_query:
        logs_qs = logs_qs.filter(
            Q(action__icontains=search_query) |
            Q(details__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    paginator = Paginator(logs_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'activity_logs/log_list.html', {
        'page_obj': page_obj,
        'category_filter': category_filter,
        'categories': ActivityLog.Category.choices,
        'search_query': search_query,
        'total_count': logs_qs.count(),
    })
