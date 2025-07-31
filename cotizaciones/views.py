from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML, CSS
from .models import Cotizacion, Producto
from django.utils import timezone
from decimal import Decimal
import os
from django.conf import settings
import base64

def generar_pdf(request):
    if request.method == 'POST':
        ultima = Cotizacion.objects.order_by('-id').first()
        if ultima:
            ultimo_num = int(ultima.numero.split('-')[1])
            numero = f"PTA-{ultimo_num + 1:05d}-1"
        else:
            numero = "PTA-00001-1"

        cotizacion = Cotizacion.objects.create(
            numero=numero,
            fecha=timezone.now(),
            cliente=request.POST.get('cliente'),
            cliente_ruc=request.POST.get('dni'),
            cliente_direccion=request.POST.get('direccion'),
            cliente_telefono=request.POST.get('telefono'),
            cliente_provincia=request.POST.get('provincia'),
            cliente_distrito=request.POST.get('distrito'),
            observaciones=request.POST.get('observaciones') or '',
        )

        nombres = request.POST.getlist('producto')
        cantidades = request.POST.getlist('cantidad')
        precios = request.POST.getlist('precio')
        dsctos = request.POST.getlist('dscto')

        for nombre, cantidad, precio, dscto in zip(nombres, cantidades, precios, dsctos):
            cantidad = float(cantidad)
            precio = float(precio)
            descuento = float(dscto) if dscto else 0
            subtotal = (cantidad * precio) * (1 - descuento / 100)

            Producto.objects.create(
                cotizacion=cotizacion,
                nombre=nombre,
                cantidad=cantidad,
                precio=precio,
                descuento=descuento,
                subtotal=subtotal
            )

        return redirect('generar_pdf_id', id=cotizacion.id)

    return render(request, 'formulario.html')


def generar_pdf_id(request, id):
    cotizacion = get_object_or_404(Cotizacion, id=id)
    productos = cotizacion.productos.all()

    subtotal = sum(p.subtotal for p in productos)
    igv = subtotal * Decimal('0.18')
    total = subtotal + igv

    # Logo a base64
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    with open(logo_path, 'rb') as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        logo_src = f"data:image/png;base64,{logo_base64}"

    # Contenido del CSS como texto
    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'styles.css')
    with open(css_path, 'r', encoding='utf-8') as css_file:
        css_inline = css_file.read()

    context = {
        'cotizacion': {'numero': cotizacion.numero},
        'fecha': cotizacion.fecha.strftime("%d/%m/%Y"),
        'cliente': {
            'nombre': cotizacion.cliente,
            'ruc': cotizacion.cliente_ruc,
            'direccion': cotizacion.cliente_direccion,
            'telefono': cotizacion.cliente_telefono,
            'provincia': cotizacion.cliente_provincia,
            'distrito': cotizacion.cliente_distrito,
            'pais': 'PER',
        },
        'observaciones': cotizacion.observaciones or '',
        'productos': [
            {
                'nombre': p.nombre,
                'cantidad': f"{p.cantidad:.2f}",
                'precio': f"{p.precio:.2f}",
                'descuento': f"{p.descuento:.2f}",
                'subtotal': f"{p.subtotal:.2f}",
                'total': f"{(p.subtotal * Decimal('1.18')):.2f}",
            }
            for p in productos
        ],
        'subtotal': f"{subtotal:.2f}",
        'igv': f"{igv:.2f}",
        'total': f"{total:.2f}",
        'logo_src': logo_src,
        'css_inline': css_inline,  # Empotramos CSS
    }

    template = get_template('plantilla_pdf.html')
    html = template.render(context)

    # Quita link externo (por si aún existe en HTML renderizado)
    html = html.replace('<link rel="stylesheet" href="file:///{{ css_absoluto }}">', '')
    html = html.replace('<link rel="stylesheet" href="file://{{ css_absoluto }}">', '')
    html = html.replace('<link rel="stylesheet" href="{{ css_absoluto }}">', '')

    # Generar PDF
    pdf = HTML(string=html).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="cotizacion_{cotizacion.numero}.pdf"'
    return response
