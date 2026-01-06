from django.urls import path
from .views import (
    VendorApplyView,
    PendingVendorsView,
    VendorConfirmView,
    InternalVendorApproveView,
    VendorNotificationListView,
    UnreadNotificationCountView,
    MarkNotificationReadView,
    VendorMeView,
    PublicVendorDetailView,
    ScheduleTaskListCreateView,
    ScheduleTaskDetailView,
    TechnicianListCreateView,
    TechnicianDetailView,
)

urlpatterns = [
    path("me/", VendorMeView.as_view(), name="vendor-me"),
    path("apply/", VendorApplyView.as_view(), name="vendor-apply"),
    path("confirm/", VendorConfirmView.as_view(), name="vendor-confirm"),

    path("admin/vendors/pending/", PendingVendorsView.as_view(), name="pending-vendors"),
    path("internal/vendors/approve/", InternalVendorApproveView.as_view(), name="internal-vendor-approve",),

    path("notifications/", VendorNotificationListView.as_view()),
    path("notifications/unread-count/", UnreadNotificationCountView.as_view()),
    path("notifications/<int:pk>/read/", MarkNotificationReadView.as_view()),
    
    # Schedule Tasks
    path("schedule/tasks/", ScheduleTaskListCreateView.as_view(), name="schedule-task-list"),
    path("schedule/tasks/<uuid:pk>/", ScheduleTaskDetailView.as_view(), name="schedule-task-detail"),

    # Technician Management
    path("technicians/", TechnicianListCreateView.as_view(), name="technician-list"),
    path("technicians/<uuid:pk>/", TechnicianDetailView.as_view(), name="technician-detail"),

    # Public endpoint
    path("public/vendors/<int:user_id>/", PublicVendorDetailView.as_view(), name="public-vendor-detail"),
]
