from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Devolucion, InspeccionPercha, Lote, MovimientoInventario, OrderCompra, Producto, UbicacionBodega


class InventoryService:
    @staticmethod
    def registrar_recepcion(order_compra, producto, cantidad, usuario, lote_numero=None, ubicacion=None):
        if cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")

        with transaction.atomic():
            producto.stock_bodega += cantidad
            producto.save(update_fields=["stock_bodega", "updated_at"])

            lote = None
            if lote_numero:
                lote, _ = Lote.objects.get_or_create(
                    producto=producto,
                    numero_lote=lote_numero,
                    defaults={"cantidad": 0, "ubicacion": ubicacion},
                )
                lote.cantidad += cantidad
                lote.save(update_fields=["cantidad", "updated_at"])

            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.TIPO_ENTRADA,
                producto=producto,
                lote=lote,
                cantidad=cantidad,
                motivo="Recepción de mercadería",
                referencia=order_compra.numero if order_compra else "",
                usuario=usuario,
            )

            InventoryService.notificar_area("Compras", f"Recepción registrada para {producto.codigo}")
            InventoryService.notificar_area("Ventas", f"Recepción registrada para {producto.codigo}")

            return producto, lote

    @staticmethod
    def registrar_devolucion(producto, cantidad, motivo, usuario, evidencia="", lote=None):
        if cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")

        if producto.stock_bodega < cantidad:
            raise ValidationError("No existe stock suficiente para procesar la devolución")

        with transaction.atomic():
            producto.stock_bodega -= cantidad
            producto.save(update_fields=["stock_bodega", "updated_at"])

            devolucion = Devolucion.objects.create(
                producto=producto,
                lote=lote,
                cantidad=cantidad,
                motivo=motivo,
                evidencia=evidencia,
                usuario=usuario,
                estado="PROCESADA",
            )

            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.TIPO_SALIDA,
                producto=producto,
                lote=lote,
                cantidad=cantidad,
                motivo="Devolución por no conformidad",
                usuario=usuario,
            )

            InventoryService.notificar_area("Compras", f"Devolución registrada para {producto.codigo}")
            InventoryService.notificar_area("Ventas", f"Devolución registrada para {producto.codigo}")

            return devolucion

    @staticmethod
    def registrar_movimiento(producto, cantidad, tipo, usuario, motivo="", lote=None, referencia=""):
        if cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")

        with transaction.atomic():
            if tipo == MovimientoInventario.TIPO_SALIDA:
                if producto.stock_bodega < cantidad:
                    raise ValidationError("No se puede generar un movimiento con stock negativo")
                producto.stock_bodega -= cantidad
            elif tipo == MovimientoInventario.TIPO_ENTRADA:
                producto.stock_bodega += cantidad
            else:
                raise ValidationError("Tipo de movimiento no soportado")

            producto.save(update_fields=["stock_bodega", "updated_at"])

            movimiento = MovimientoInventario.objects.create(
                tipo=tipo,
                producto=producto,
                lote=lote,
                cantidad=cantidad,
                motivo=motivo,
                referencia=referencia,
                usuario=usuario,
            )
            return movimiento

    @staticmethod
    def aplicar_fifo(producto, cantidad, usuario):
        lotes = Lote.objects.filter(producto=producto, estado="DISPONIBLE").order_by("fecha_vencimiento", "created_at")
        if not lotes.exists():
            raise ValidationError("No existen lotes disponibles para aplicar FIFO")

        restante = cantidad
        for lote in lotes:
            if restante <= 0:
                break
            usar = min(restante, lote.cantidad)
            lote.cantidad -= usar
            restante -= usar
            lote.save(update_fields=["cantidad", "updated_at"])

        if restante > 0:
            raise ValidationError("No hay suficiente cantidad en lotes para completar la operación")

        if producto.stock_bodega < cantidad:
            raise ValidationError("No hay suficiente stock en bodega para trasladar a percha")

        producto.stock_bodega -= cantidad
        producto.stock_percha += cantidad
        producto.save(update_fields=["stock_bodega", "stock_percha", "updated_at"])

        MovimientoInventario.objects.create(
            tipo=MovimientoInventario.TIPO_SALIDA,
            producto=producto,
            cantidad=cantidad,
            motivo="Reposición de percha con FIFO",
            usuario=usuario,
        )

        InventoryService.notificar_area("Ventas", f"Reposición de percha aplicada para {producto.codigo}")

    @staticmethod
    def monitorear_proximos_a_vencer(dias=30):
        fecha_maxima = timezone.now().date() + timezone.timedelta(days=dias)
        return Lote.objects.filter(estado="DISPONIBLE", fecha_vencimiento__lte=fecha_maxima).order_by("fecha_vencimiento")

    @staticmethod
    def retirar_vencidos(producto, cantidad, motivo, responsable, evidencia=""):
        if cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")

        if producto.stock_bodega < cantidad:
            raise ValidationError("No hay suficiente stock en bodega para retirar")

        producto.stock_bodega -= cantidad
        producto.save(update_fields=["stock_bodega", "updated_at"])

        movimiento = MovimientoInventario.objects.create(
            tipo=MovimientoInventario.TIPO_SALIDA,
            producto=producto,
            cantidad=cantidad,
            motivo=f"Retiro por vencimiento: {motivo}",
            usuario=responsable,
            observaciones=evidencia,
        )

        InventoryService.notificar_area("Ventas", f"Retiro de producto vencido {producto.codigo}")
        InventoryService.notificar_area("Contabilidad", f"Retiro de producto vencido {producto.codigo}")
        return movimiento

    @staticmethod
    def registrar_inspeccion(producto, responsable, observaciones="", sin_novedades=True):
        inspec = InspeccionPercha.objects.create(
            producto=producto,
            responsable=responsable,
            observaciones=observaciones,
            sin_novedades=sin_novedades,
            fecha_inspeccion=timezone.now(),
        )
        InventoryService.notificar_area("Logística", f"Inspección registrada para {producto.codigo}")
        return inspec

    @staticmethod
    def notificar_area(area, mensaje):
        print(f"[NOTIFICACIÓN {area}] {mensaje}")

    @staticmethod
    def generar_reporte_existencias():
        return Producto.objects.filter(activo=True).values("codigo", "nombre", "stock_bodega", "stock_percha", "stock_minimo")
