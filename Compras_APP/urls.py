from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/usuarios/",views.usuarios, name="usuarios"),
    path("dashboard/solicitudes/", views.lista_solicitudes, name="lista_solicitudes"),
    path("dashboard/solicitudes/nueva/", views.crear_solicitud, name="crear_solicitud"),
    path("dashboard/solicitudes/editar/<int:pk>/", views.editar_solicitud, name="editar_solicitud"),
]