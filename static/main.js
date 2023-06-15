$(document).ready(function(){
    $('.dropdown').hover(function() {
        $(this).find('.dropdown-menu').stop(true, true).delay(200).fadeIn(500);
    }, function() {
        $(this).find('.dropdown-menu').stop(true, true).delay(200).fadeOut(500);
    });

    $('#empresa').change(function() {
        updateObjectives();
        updateKRs();
        updateUsers();
    });

    $('#objetivo').change(function() {
        var objetivoId = $(this).val();
        $('#id_okr').val(objetivoId);
        updateKRs();
    });

    updateObjectives();
    updateKRs();
    updateUsers();

    $('.btn-approve').click(function(e) {
        if (!confirm('Tem certeza de que deseja aprovar esta macro ação? Ela será inserida no banco de dados.')) {
            e.preventDefault();
        }
    });

    $('.btn-reject').click(function(e) {
        if (!confirm('Tem certeza de que deseja recusar esta macro ação? Ela será excluída.')) {
            e.preventDefault();
        }
    });

    var toDoCount = 1;

    $('#add_to_do').click(function() {
        var newToDo = $('<input>');
        newToDo.attr('type', 'text');
        newToDo.attr('id', 'to_do_' + toDoCount);
        newToDo.attr('name', 'to_do_' + toDoCount);

        $('#to_do_container').append(newToDo);

        toDoCount++;
    });
    $('#emailModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget) // Botão que acionou o modal
        var usuarioId = button.data('usuario') // Extrai a informação do data-* attributes

        // Busca o conteúdo do email do servidor
        $.get('/get_email_content/' + usuarioId, function(data) {
            $('#emailContent').html('<h5>' + data.titulo + '</h5><p>' + data.corpo.replace(/\n/g, '<br>') + '</p>');
        });

        // Adiciona um listener ao botão de enviar email para enviar o email quando clicado
        $('#sendEmailButton').off('click').on('click', function() {
            $.post('/enviar_email/' + usuarioId, function() {
                $('#emailModal').modal('hide');
            });
        });
    });
});
function updateObjectives() {
    var objetivoOriginal = $('#objetivo').data('original');
    var empresaId = $('#empresa').val();

    $.getJSON('/get_okrs/' + empresaId, function(data) {
        var select = $('#objetivo');
        select.empty();
        data.forEach(function(okr) {
            var option = $('<option>');
            option.val(okr.id);
            option.text(okr.objetivo);
            if (okr.id == objetivoOriginal) {
                option.prop('selected', true);
            }
            select.append(option);
        });

        if (objetivoOriginal) {
            $('#id_okr').val(objetivoOriginal);
        } else {
            $('#id_okr').val($('#objetivo').val());
        }
    });

    $.getJSON('/get_empresa_info/' + empresaId, function(data) {
        $('#descricao_div').text(data.descricao_empresa);
        $('#cargos_div').text(data.usuarios.join(', '));
        $('#okrs_div').text(data.objetivos.join(', '));
        $('#krs_div').text(data.krs.join(', '));
        $('#macroacoes_div').text(data.macro_acoes.join(', '));
    });
}

function updateKRs() {
    var krOriginal = $('#kr').data('original');
    var objetivoId = $('#objetivo').val();

    $.getJSON('/get_krs/' + objetivoId, function(data) {
        var select = $('#kr');
        select.empty();
        data.forEach(function(kr) {
            var option = $('<option>');
            option.val(kr.id);
            option.text(kr.texto);
            if (kr.id == krOriginal) {
                option.prop('selected', true);
            }
            select.append(option);
        });
    });
}

function updateUsers() {
    var usuarioOriginal = $('#usuario').data('original');
    var empresaId = $('#empresa').val();

    $.getJSON('/get_usuarios/' + empresaId, function(data) {
        var select = $('#usuario');
        select.empty();
        data.forEach(function(usuario) {
            var option = $('<option>');
            option.val(usuario.id);
            option.text(usuario.nome);
            if (usuario.id == usuarioOriginal) {
                option.prop('selected', true);
            }
            select.append(option);
        });
    });
}
document.getElementById('add_passo').addEventListener('click', function() {
    var passosContainer = document.getElementById('passos_container');
    var passoCount = passosContainer.getElementsByClassName('passo').length;

    var newPasso = document.createElement('div');
    newPasso.className = 'passo';

    var passoLabel = document.createElement('label');
    passoLabel.htmlFor = 'passo_' + passoCount;
    passoLabel.textContent = 'Nome do Passo:';

    var passoInput = document.createElement('input');
    passoInput.type = 'text';
    passoInput.id = 'passo_' + passoCount;
    passoInput.name = 'passo_' + passoCount;

    var dateLabel = document.createElement('label');
    dateLabel.htmlFor = 'data_' + passoCount;
    dateLabel.textContent = 'Data:';

    var dateInput = document.createElement('input');
    dateInput.type = 'date';
    dateInput.id = 'data_' + passoCount;
    dateInput.name = 'data_' + passoCount;

    newPasso.appendChild(passoLabel);
    newPasso.appendChild(passoInput);
    newPasso.appendChild(dateLabel);
    newPasso.appendChild(dateInput);

    passosContainer.appendChild(newPasso);
});
