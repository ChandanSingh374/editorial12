from django.contrib import admin
from django.urls import path, include
from cohorts import views

urlpatterns = [
    path('<int:cohort_id>/scoreboard',  views.CohortScoreBoard.as_view(), name='cohort_scoreboard')
]
