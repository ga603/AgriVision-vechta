from django.urls import path
from . import views

urlpatterns = [
    # We will define the actual view in the next step
    path('', views.dashboard, name='dashboard'),
    path('analyze/<int:field_id>/', views.analyze_field, name='analyze_field'), 
]