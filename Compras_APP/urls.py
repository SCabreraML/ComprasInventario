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

    path(
        "solicitudes/<int:pk>/cotizaciones/",
        views.lista_cotizaciones_view,
        name="lista_cotizaciones"
    ),

    path(
        "solicitudes/<int:pk>/cotizaciones/nueva/",
        views.registrar_cotizacion_view,
        name="registrar_cotizacion"
    ),

    path(
        "ordenes/",
        views.lista_ordenes,
        name="lista_ordenes"
    ),

    path(
        "ordenes/generar/<int:pk>/",
        views.generar_orden_view,
        name="generar_orden"
    ),

    path(
        "ordenes/<int:pk>/",
        views.ver_orden_view,
        name="ver_orden"
    ),

    # HU-22: Exportar orden a PDF
    # COMENTARIO DE LOCALIZACIÓN: HU-22 - Ruta para descargar el PDF de la orden de compra
    path(
        "ordenes/<int:pk>/pdf/",
        views.exportar_orden_pdf,
        name="exportar_orden_pdf"
    ),
]