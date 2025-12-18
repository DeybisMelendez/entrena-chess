from django.urls import path
from . import views

urlpatterns = [
    # Home / Dashboard
    path("", views.home, name="home"),

    # Obtener y mostrar el puzzle actual (GET)
    path("puzzle/", views.get_puzzle, name="get_puzzle"),

    # Enviar resultado del puzzle (POST)
    path("puzzle/submit/", views.submit_puzzle, name="submit_puzzle"),

]
