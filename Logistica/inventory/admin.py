from django.contrib import admin

from .models import Devolucion, InspeccionPercha, Lote, MovimientoInventario, OrderCompra, Producto, UbicacionBodega


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "stock_bodega", "stock_percha", "activo")
    search_fields = ("codigo", "nombre", "categoria")


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("producto", "numero_lote", "cantidad", "fecha_vencimiento", "estado")
    list_filter = ("estado",)


@admin.register(OrderCompra)
class OrderCompraAdmin(admin.ModelAdmin):
    list_display = ("numero", "proveedor", "estado", "fecha_esperada")
    search_fields = ("numero", "proveedor")


@admin.register(UbicacionBodega)
class UbicacionBodegaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "capacidad", "ocupada")


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("tipo", "producto", "cantidad", "usuario", "created_at")
    list_filter = ("tipo",)


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ("producto", "cantidad", "estado", "usuario", "fecha_devolucion")


@admin.register(InspeccionPercha)
class InspeccionPerchaAdmin(admin.ModelAdmin):
    list_display = ("producto", "sin_novedades", "responsable", "fecha_inspeccion")
