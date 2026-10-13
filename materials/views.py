from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404

from .models import StudyMaterial
from .forms import StudyMaterialForm
from academics.models import Course, CourseEnrollment
from accounts.decorators import teacher_required
from activity_logs.models import log_activity, ActivityLog


@login_required
def material_list_view(request):
    user = request.user
    course_filter = request.GET.get('course', '')
    search_query = request.GET.get('q', '').strip()

    if user.is_student_role and hasattr(user, 'student_profile'):
        enrolled_courses = CourseEnrollment.objects.filter(
            student=user.student_profile, is_active=True
        ).values_list('course_id', flat=True)
        materials = StudyMaterial.objects.filter(course_id__in=enrolled_courses).select_related('course', 'uploaded_by__user')
        courses = Course.objects.filter(id__in=enrolled_courses)
    elif user.is_teacher_role and hasattr(user, 'teacher_profile') and not user.is_admin_role:
        materials = StudyMaterial.objects.filter(uploaded_by=user.teacher_profile).select_related('course')
        courses = Course.objects.filter(teacher=user.teacher_profile)
    else:
        materials = StudyMaterial.objects.all().select_related('course', 'uploaded_by__user')
        courses = Course.objects.all()

    if course_filter:
        materials = materials.filter(course_id=course_filter)
    if search_query:
        materials = materials.filter(
            Q(title__icontains=search_query) |
            Q(unit_module__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    return render(request, 'materials/material_list.html', {
        'materials': materials,
        'courses': courses,
        'selected_course': course_filter,
        'search_query': search_query,
    })


@teacher_required
def material_upload_view(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    form = StudyMaterialForm(request.POST or None, request.FILES or None, teacher=teacher)
    if request.method == 'POST' and form.is_valid():
        material = form.save(commit=False)
        if teacher:
            material.uploaded_by = teacher
        material.save()

        log_activity(
            request=request,
            action=f"Uploaded study material: '{material.title}' for {material.course.code}",
            category=ActivityLog.Category.MATERIAL
        )
        messages.success(request, f"Study material '{material.title}' has been uploaded successfully!")
        return redirect('material_list')

    return render(request, 'materials/material_form.html', {'form': form, 'title': 'Upload Study Material'})


@teacher_required
def material_delete_view(request, pk):
    material = get_object_or_404(StudyMaterial, pk=pk)
    teacher = getattr(request.user, 'teacher_profile', None)

    if teacher and material.uploaded_by != teacher and not request.user.is_admin_role:
        messages.error(request, "You can only delete materials that you uploaded.")
        return redirect('material_list')

    title = material.title
    material.delete()
    log_activity(
        request=request,
        action=f"Deleted study material: '{title}'",
        category=ActivityLog.Category.MATERIAL
    )
    messages.success(request, f"Study material '{title}' was removed.")
    return redirect('material_list')


@login_required
def material_download_view(request, pk):
    material = get_object_or_404(StudyMaterial, pk=pk)
    if not material.file:
        raise Http404("File not found")

    material.download_count += 1
    material.save(update_fields=['download_count'])

    return FileResponse(material.file.open('rb'), as_attachment=True, filename=material.file_name)
