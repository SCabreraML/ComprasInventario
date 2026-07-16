from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_view, name="inventory_root"),
    path("dashboard/", views.dashboard_view, name="inventory_dashboard"),
    path("recepcion/", views.registro_recepcion_view, name="inventory_registro_recepcion"),
    path("movimiento/", views.registro_movimiento_view, name="inventory_registro_movimiento"),
    path("devolucion/", views.registro_devolucion_view, name="inventory_registro_devolucion"),
    path("inspeccion/", views.inspeccion_percha_view, name="inventory_inspeccion_percha"),
    path("reponer/", views.reponer_percha_view, name="inventory_reponer_percha"),
    path("reporte/", views.reporte_existencias_view, name="inventory_reporte_existencias"),
    path("vencer/", views.proximos_vencer_view, name="inventory_proximos_vencer"),
    path("retirar-vencidos/", views.retirar_vencidos_view, name="inventory_retirar_vencidos"),
    path("historial/<int:producto_id>/", views.historial_movimientos_view, name="inventory_historial"),
    path("api/existencias/", views.api_consultar_existencias, name="api_consultar_existencias"),
]
