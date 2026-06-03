from django.urls import path

from apps.projects import views

app_name = 'projects'

urlpatterns = [
    path('new/', views.project_create, name='create'),
    path('<int:pk>/', views.project_detail, name='detail'),
    path('<int:pk>/status/', views.project_status_api, name='status'),
    path('<int:pk>/status/update/', views.project_status_update, name='status_update'),
    path('<int:pk>/delete/', views.project_delete, name='delete'),
    path('<int:pk>/voice-notes/upload/', views.voice_note_upload, name='voice_upload'),
    path(
        '<int:pk>/voice-notes/<int:note_id>/regenerate/',
        views.voice_note_regenerate,
        name='voice_regenerate',
    ),
    path(
        '<int:pk>/voice-notes/<int:note_id>/edit-summary/',
        views.voice_note_edit_summary,
        name='voice_edit_summary',
    ),
    path(
        '<int:pk>/voice-notes/<int:note_id>/delete/',
        views.voice_note_delete,
        name='voice_delete',
    ),
    path(
        '<int:pk>/voice-notes/<int:note_id>/retry/',
        views.voice_note_retry,
        name='voice_retry',
    ),
    path('<int:pk>/finances/income/', views.finances_income_update, name='finances_income_update'),
    path('<int:pk>/finances/income/clear/', views.finances_income_clear, name='finances_income_clear'),
    path('<int:pk>/finances/expense/add/', views.finances_expense_add, name='finances_expense_add'),
    path(
        '<int:pk>/finances/expense/<int:index>/',
        views.finances_expense_update,
        name='finances_expense_update',
    ),
    path(
        '<int:pk>/finances/expense/<int:index>/delete/',
        views.finances_expense_delete,
        name='finances_expense_delete',
    ),
]
