from django.urls import path
from . import views

urlpatterns = [
    # Vista que devuelve el puzzle en JSON
    path("get-puzzle/", views.get_puzzle, name="get_puzzle"),

    # Vista que renderiza la página donde probarás HTMX
    path("", views.watch_puzzle, name="watch_puzzle"),
]
