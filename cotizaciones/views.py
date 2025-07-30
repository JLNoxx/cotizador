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

        productos_data = request.POST
        for key in productos_data:
            if key.startswith('productos[') and '][nombre]' in key:
                index = key.split('[')[1].split(']')[0]
                nombre = productos_data.get(f'productos[{index}][nombre]')
                cantidad = float(productos_data.get(f'productos[{index}][cantidad]', 0))
                precio = float(productos_data.get(f'productos[{index}][precio]', 0))
                dscto_str = productos_data.get(f'productos[{index}][dscto]', '').strip()
                descuento = float(dscto_str) if dscto_str else 0
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

    # Leer y convertir el logo a base64
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    with open(logo_path, 'rb') as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        logo_src = f"data:image/png;base64,{logo_base64}"

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
        'logo_src': logo_src,  # 👈 se envía el logo como string base64
    }

    template = get_template('plantilla_pdf.html')
    html = template.render(context)

    static_root = os.path.join(settings.BASE_DIR, 'static').replace('\\', '/')
    css_path = os.path.join(static_root, 'css', 'styles.css').replace('\\', '/')

    html = html.replace('{% load static %}', '')
    html = html.replace("{% static 'css/styles.css' %}", f'file:///{css_path}')
    # OJO: Ya no reemplazamos el logo aquí

    pdf_file = HTML(string=html, base_url=static_root).write_pdf(stylesheets=[CSS(css_path)])

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="cotizacion_{cotizacion.numero}.pdf"'
    return response
