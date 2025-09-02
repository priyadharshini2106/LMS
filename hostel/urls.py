from django.urls import path
from .views import (
    # Dashboard
    HostelDashboardView,

    # Hostels
    HostelListView, HostelCreateView, HostelUpdateView, HostelDeleteView,

    # Rooms
    RoomListView, RoomCreateView, RoomUpdateView, RoomDeleteView,

    # Allocations
    AllocationListView, AllocationCreateView, AllocationDetailView,
    AllocationUpdateView, AllocationDeleteView,

    # Payments
    PaymentListView, PaymentCreateView, PaymentDetailView,
    PaymentUpdateView, PaymentDeleteView,

    # Visitors
    VisitorListView, VisitorCreateView, VisitorUpdateView,
    VisitorDetailView, VisitorDeleteView,

    # Outpass
    OutpassListView, OutpassCreateView, OutpassUpdateView, UndoOutpassUpdateView,

    # Complaints
    ComplaintListView, ComplaintCreateView,

    # API / Utility
    student_search,
)

app_name = "hostel"

urlpatterns = [
    # Dashboard
    path("", HostelDashboardView.as_view(), name="dashboard"),

    # Hostels
    path("list/", HostelListView.as_view(), name="hostel_list"),
    path("create/", HostelCreateView.as_view(), name="hostel_create"),
    path("<int:pk>/update/", HostelUpdateView.as_view(), name="hostel_update"),
    path("<int:pk>/delete/", HostelDeleteView.as_view(), name="hostel_delete"),

    # Rooms
    path("rooms/", RoomListView.as_view(), name="room_list"),
    path("rooms/create/", RoomCreateView.as_view(), name="room_create"),
    path("rooms/<int:pk>/edit/", RoomUpdateView.as_view(), name="room_edit"),
    path("rooms/<int:pk>/delete/", RoomDeleteView.as_view(), name="room_delete"),

    # Allocations
    path("allocations/", AllocationListView.as_view(), name="allocation_list"),
    path("allocations/create/", AllocationCreateView.as_view(), name="allocation_create"),
    path("allocations/<int:pk>/", AllocationDetailView.as_view(), name="allocation_detail"),
    path("allocations/<int:pk>/edit/", AllocationUpdateView.as_view(), name="allocation_update"),
    path("allocations/<int:pk>/delete/", AllocationDeleteView.as_view(), name="allocation_delete"),

    # Payments
    path("payments/", PaymentListView.as_view(), name="payment_list"),
    path("payments/add/", PaymentCreateView.as_view(), name="payment_create"),
    path("payments/<int:pk>/", PaymentDetailView.as_view(), name="payment_detail"),
    path("payments/<int:pk>/edit/", PaymentUpdateView.as_view(), name="payment_update"),
    path("payments/<int:pk>/delete/", PaymentDeleteView.as_view(), name="payment_delete"),

    # Visitors
    path("visitors/", VisitorListView.as_view(), name="visitor_list"),
    path("visitors/create/", VisitorCreateView.as_view(), name="visitor_create"),
    path("visitors/<int:pk>/", VisitorDetailView.as_view(), name="visitor_detail"),
    path("visitors/<int:pk>/edit/", VisitorUpdateView.as_view(), name="visitor_update"),
    path("visitors/<int:pk>/delete/", VisitorDeleteView.as_view(), name="visitor_delete"),

    # Outpass
    path('outpasses/', OutpassListView.as_view(), name='outpass_list'),
    path('outpasses/create/', OutpassCreateView.as_view(), name='outpass_create'),
    path('outpasses/<int:pk>/edit/', OutpassUpdateView.as_view(), name='outpass_update'),
    path('outpasses/<int:pk>/undo/', UndoOutpassUpdateView.as_view(), name='outpass_undo'),

    # Complaints
    path("complaints/", ComplaintListView.as_view(), name="complaint_list"),
    path("complaints/create/", ComplaintCreateView.as_view(), name="complaint_create"),

    # Student Search API
    path("student-search/", student_search, name="student_search"),
]
