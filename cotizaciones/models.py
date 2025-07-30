from django.db import models

class Cotizacion(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.CharField(max_length=100)
    cliente_ruc = models.CharField(max_length=20, blank=True, null=True)
    cliente_direccion = models.CharField(max_length=255, blank=True, null=True)
    cliente_telefono = models.CharField(max_length=20, blank=True, null=True)
    cliente_provincia = models.CharField(max_length=100, blank=True, null=True)
    cliente_distrito = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.numero} - {self.cliente}"


class Producto(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=100)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.nombre} ({self.cantidad} x S/ {self.precio})"
