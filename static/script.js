function mostrarSeleccion() {
    var valorSeleccionado = document.getElementById("tabla-select").value;
    alert("Seleccionaste: " + valorSeleccionado);
}

function capitalizarPrimeraLetra(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

document.getElementById("form-busqueda").addEventListener("submit", function() {
    var inputBusqueda = document.getElementById("input-busqueda");
    document.getElementById("input-type").value = inputBusqueda.getAttribute("type");
});

// Despliega las columnas de la tabla seleccionada
$(document).ready(function() {
    $(".busqueda-tabla").change(function() {
        var tablaSeleccionada = $(this).val();
        var columnaSelect = $(this).closest(".busqueda-container").find('.busqueda-columna'); //$('#busqueda-columna');
        
        if (tablaSeleccionada) {
            $.ajax({ 
                url: "/get_columns",
                type: "POST",
                contentType: 'application/json',
                data: JSON.stringify({tabla: tablaSeleccionada}),
                success: function(response) {
                    columnaSelect.empty().append('<option value="">Seleccione una columna</option>');
                    response.forEach(function(columna) {
                        columnaSelect.append('<option value="' + capitalizarPrimeraLetra(columna.replaceAll("_", " ")) + '">' + capitalizarPrimeraLetra(columna.replaceAll("_", " ")) + '</option>');
                    });
                    if (tablaSeleccionada == 'equipos') {
                        columnaSelect.append('<option value="historial">Historial de mantenimiento</option>')
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error al obtener las columnas: ", error);
                }
            });
        } else {
            $('#busqueda-columna').html('<option value="">Seleccione una columna</option>');
        }
    });
});

// Modificar el tipo de input segun el tipo de columna
$(document).ready(function() {
    $(".busqueda-columna").change(function() {
        var columnaSeleccionada = $(this).val();
        if (columnaSeleccionada) {
            $.ajax({
                url: "/get_type",
                type: "POST",
                contentType: 'application/json',
                data: JSON.stringify({tabla: $('.busqueda-tabla').val(), columna: columnaSeleccionada.replaceAll(" ", "_").toLowerCase()}),
                success: function(response) {
                    var inputBusqueda = $('#input-busqueda');
                    if(response == 'int') {
                        inputBusqueda.attr('type', 'number');
                        inputBusqueda.attr('placeholder', 'Ingrese numero');
                    } else if(response == 'varchar') {
                        inputBusqueda.attr('type', 'text');
                        inputBusqueda.attr('placeholder', 'Ingresar dato');
                    } else if (response == 'date') {
                        inputBusqueda.attr('type', 'date');
                    } else if(response == 'datetime') {
                        inputBusqueda.attr('type', 'datetime-local');
                    } else {
                        inputBusqueda.attr('type', 'text');
                        inputBusqueda.attr('placeholder', 'Ingrese un valor');
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error al obtener el tipo de la columna: ", error);
                }
            })
        } else {
            $('#input-busqueda').attr('type', 'text');
            $('#input-busqueda').attr('placeholder', 'Ingrese un valor');
        }
    });
});

//despliega los inputs de cada columna para insertar datos
$(document).ready(function() {
    $(".busqueda-tabla").change(function() {
        var tablaSeleccionada = $(this).val();
        var inputContainer = $(this).closest(".busqueda-container").find('.input-container');
        
        if (tablaSeleccionada) {
            $.ajax({ 
                url: "/get_columns",
                type: "POST",
                contentType: 'application/json',
                data: JSON.stringify({tabla: tablaSeleccionada}),
                success: function(response) {
                    inputContainer.empty();
                    response.forEach(function(columna) {
                        inputContainer.append('<label for="' + columna + '">' + capitalizarPrimeraLetra(columna.replaceAll("_", " ")) + '</label>');
                        inputContainer.append('<input type="text" id="' + columna + '" name="' + columna + '">');
                    });
                },
                error: function(xhr, status, error) {
                    console.error("Error al obtener las columnas: ", error);
                }
            });
        } else {
            inputContainer.empty();
        }
    });
});

//Despliega los inputs de cada columna para actualizar datos menos la llave primaria
$(document).ready(function() {
    $(".busqueda-tabla").change(function() {
        var tablaSeleccionada = $(this).val();
        var inputContainer = $(this).closest("#actualizar-elemento").find('.input-container');
        if (tablaSeleccionada) {
            $.ajax({ 
                url: "/get_columns",
                type: "POST",
                contentType: 'application/json',
                data: JSON.stringify({tabla: tablaSeleccionada}),
                success: function(response) {
                    inputContainer.empty();
                    response.forEach(function(columna) {
                        if(columna.toLowerCase() != 'ruc' && columna.toLowerCase() != 'dni' && columna.toLowerCase() != 'id') {
                            inputContainer.append('<label for="' + columna + '">' + capitalizarPrimeraLetra(columna.replaceAll("_", " ")) + '</label>');
                            inputContainer.append('<input type="text" id="' + columna + '" name="' + columna + '">');
                        }
                    });
                },
                error: function(xhr, status, error) {
                    console.error("Error al obtener las columnas: ", error);
                }
            });
        } else {
            inputContainer.empty();
        }
    });
});

//busqueda
// $('#form-busqueda').submit(function(event) {
//     event.preventDefault();

//     var formData = {
//         tabla: $('#busqueda-tabla').val(),
//         columna: $('#busqueda-columna').val(),
//         valor: $('#input-busqueda').val()
//     };

//     if (formData.tabla && formData.columna && formData.valor) {
//         $.ajax({
//             url: "/search",
//             type: "POST",
//             contentType: "application/json",
//             data: JSON.stringify(formData),
//             success: function(response) {
//                 $('#resultados').empty();
//                 response.data.forEach(function(row) {
//                     var tr = '<tr>';
//                     response.columns.forEach(function(column) {
//                         tr += '<td>${row[column]}</td>';
//                     });
//                     tr += '</tr>';
//                     $('#resultados').append(tr);
//                 });
//             },
//             error: function() {
//                 alert("Error al buscar los datos");
//             }
//         });
//     } else {
//         alert("Faltan datos para realizar la búsqueda");
//     }
// });

