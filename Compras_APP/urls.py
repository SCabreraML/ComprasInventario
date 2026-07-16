from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/usuarios/", views.usuarios, name="usuarios"),

    # Sprint 2
    path(
        "solicitudes/",
        views.lista_solicitudes,
        name="lista_solicitudes"
    ),

    path(
        "solicitudes/nueva/",
        views.crear_solicitud,
        name="crear_solicitud"
    ),

    path(
        "solicitudes/<int:pk>/editar/",
        views.editar_solicitud,
        name="editar_solicitud"
    ),

    path(
        "solicitudes/<int:pk>/aprobar/",
        views.aprobar_solicitud_view,
        name="aprobar_solicitud"
    ),

    path(
        "solicitudes/<int:pk>/rechazar/",
        views.rechazar_solicitud_view,
        name="rechazar_solicitud"
    ),
]