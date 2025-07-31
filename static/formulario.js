const container = document.getElementById('productos-container');
const btnAgregar = document.getElementById('agregar-producto');

btnAgregar.addEventListener('click', () => {
    const fila = document.querySelector('.producto-row');
    const nuevaFila = fila.cloneNode(true);
    nuevaFila.querySelectorAll('input, textarea').forEach(input => input.value = '');
    container.appendChild(nuevaFila);
});

container.addEventListener('click', function(e) {
    if (e.target.classList.contains('eliminar-producto')) {
        const filas = document.querySelectorAll('.producto-row');
        if (filas.length > 1) {
            e.target.closest('tr').remove();
        } else {
            alert("Debe haber al menos un producto.");
        }
    }
});

// Auto-crecimiento para textarea
document.querySelectorAll('.auto-grow').forEach(textarea => {
    textarea.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});
