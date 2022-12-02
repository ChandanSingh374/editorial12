from django.contrib import admin
from django.urls import path, include
from batches import views

urlpatterns = [
    path('<int:batch_id>/scoreboard',  views.BatchScoreBoard.as_view(), name='batch_scoreboard')
]
