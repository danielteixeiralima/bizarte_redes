from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Empresa, Resposta, Usuario, OKR, KR, PostsInstagram, AnaliseInstagram
import requests
import json
import time
import os
from flask_migrate import Migrate
from flask import jsonify
import pandas as pd
import traceback
from flask import current_app
from sqlalchemy import inspect
from sqlalchemy import desc
import tkinter as tk
from tkinter import filedialog
import sqlite3
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import dateparser
from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from models import db, Empresa, Resposta, Usuario, OKR, KR, MacroAcao, Sprint, TarefaSemanal
import requests
import json
import time
from flask_migrate import Migrate
from flask import jsonify
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
from psycopg2 import errors as pg_errors
import traceback
from sqlalchemy.exc import DataError

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

url = os.getenv("DATABASE_URL")  # obtém a URL do banco de dados do ambiente
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)  # substitui o primeiro 'postgres://' por 'postgresql://'

class User(UserMixin):
    pass

app = Flask(__name__)
app.secret_key = 'Omega801'
app.config['SQLALCHEMY_DATABASE_URI'] = url or 'sqlite:///C:\\Users\\USER\\PycharmProjects\\bizarte\\test.db'
migrate = Migrate(app, db)
db.init_app(app)
app.jinja_env.globals.update(zip=zip)
app.jinja_env.globals.update(len=len)

# Carrega as credenciais do arquivo JSON
credentials = service_account.Credentials.from_service_account_file(
    'emialappbizarte-03be77ba1989.json',
    scopes=['https://www.googleapis.com/auth/gmail.send'])

# Constrói o serviço de e-mail
service = build('gmail', 'v1', credentials=credentials)

#################################### LOGIN #########################################


# Configuração do gerenciador de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def user_loader(email):
    user = Usuario.query.filter_by(email=email).first()
    if user is None:
        return

    user = User()
    user.id = email
    return user

@app.route('/')
@login_required
def home():
    return render_template('home.html')

def convert_string_to_datetime(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form['email']
    user = Usuario.query.filter_by(email=email).first()
    if user is None:
        return abort(401)

    if user.verify_password(request.form['password']):
        user_auth = User()
        user_auth.id = user.id  # use user id instead of email
        login_user(user_auth)
        return redirect(url_for('home'))

    return abort(401)


def verify_password(self, password):
    if self.password_hash is None:
        return False
    return check_password_hash(self.password_hash, password)


class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    user = Usuario.query.filter_by(email=email).first()
    if user is None:
        return

    user = User()
    user.id = email
    return user


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@login_manager.request_loader
def request_loader(request):
    user_id = request.form.get('user_id')
    if user_id is None:
        return
    return Usuario.query.get(int(user_id))

##################################################################################


#################################### RESULTADO #########################################



@app.route('/mostrar_resultados/<int:kr_id>')
@login_required
def mostrar_resultados(kr_id):
    kr = KR.query.get(kr_id)  # Busca o KR novamente do banco de dados

    # Busca as macro ações no banco de dados e as ordena por data_inclusao (descendente)
    macro_acoes = MacroAcao.query.filter_by(kr_id=kr_id, aprovada=False)\
                      .order_by(MacroAcao.data_inclusao.desc())\
                      .all()  # Remova `.all()` e adicione `.first()` para obter apenas a mais recente ou `.limit(n)` para as `n` mais recentes

    return render_template('mostrar_resultados.html', macro_acoes=macro_acoes, kr=kr)

#############################################################################

#################################### PROCESSO #########################################

@app.route('/iniciar_processo/<int:usuario_id>', methods=['POST'])
@login_required
def iniciar_processo(usuario_id):
    print(f"Usuario ID: {usuario_id}")  # Adicione esta linha
    # Obter o usuário pelo ID
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        return redirect(url_for('montar_tarefas_semana', usuario_id=usuario_id))  # Se o usuário não existir, redirecionar

    # Obter a empresa associada ao usuário
    empresa = db.session.get(Empresa, usuario.id_empresa)

    # Obter as macro ações associadas à empresa
    macro_acoes = MacroAcao.query.filter_by(empresa_id=empresa.id).all()

    # Obter os OKRs associados à empresa
    okrs = OKR.query.filter_by(id_empresa=empresa.id).all()

    # Obter os KRs associados à empresa
    krs = KR.query.filter_by(id_empresa=empresa.id).all()

    # Obter os sprints associados ao usuário
    sprints = Sprint.query.filter_by(usuario_id=usuario.id).all()

    # Formatar as listas como strings
    macro_acoes_str = ', '.join([acao.texto for acao in macro_acoes])
    okrs_str = ', '.join([okr.objetivo for okr in okrs])
    krs_str = ', '.join([kr.texto for kr in krs])
    sprints_str = ', '.join([f'{sprint.tarefa} ({sprint.data_criacao})' for sprint in sprints])

    # Construir a pergunta para o GPT-4
    pergunta = f"Inteligência Artificial GPT, considerando a lista de macro ações estratégicas geradas a partir dos OKRs {okrs_str} e dos KRs {krs_str}, Resumo sobre a empresa: {empresa.descricao_empresa} e a Lista de macro ações: {macro_acoes_str}, as tarefas da semana {sprints_str} para o colaborador {usuario.nome} {usuario.cargo}  crie to-do para cada tarefa. Provide them in JSON format with the following keys: tarefa, usuario, data_para_conclusão, passo1, data1, passo2, data2, passo3, data3, passo4, data4, passo5, data5, passo6, data6."
    print(pergunta)
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    resposta, messages = perguntar_gpt(pergunta, empresa.id, messages)
    # Imprimir a resposta do GPT
    print(f"Resposta do GPT: {resposta}")
    # Encontra o início e o final do objeto JSON na resposta
    inicio_json = resposta.find('[')
    final_json = resposta.rfind(']')

    # Se não encontramos um objeto JSON, lançamos um erro
    if inicio_json == -1 or final_json == -1:
        print(f"Erro ao decodificar JSON: não foi possível encontrar um objeto JSON na resposta")
        print(f"Resposta: {resposta}")
        return redirect(url_for('montar_tarefas_semana', usuario_id=usuario_id))


    json_str = resposta[inicio_json:final_json+1]

    # Carrega a resposta JSON
    try:
        tarefas_semana = json.loads(json_str)

    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {str(e)}")
        print(f"Resposta:{resposta}")

        return redirect(url_for('montar_tarefas_semana', usuario_id=usuario_id))  # Se a decodificação falhar, redirecionar

    # Armazena a resposta, as tarefas da semana e o id do usuário na sessão
    session['resposta'] = resposta
    session['tarefas_semana'] = tarefas_semana
    session['usuario_id'] = usuario_id

    # Redireciona para a página de revisão
    return redirect(url_for('revisar_tarefas'))

#############################################################################


#################################### TAREFAS #########################################

@app.route('/montar_tarefas_semana/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def montar_tarefas_semana(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    empresa = Empresa.query.get(usuario.id_empresa)
    okrs = OKR.query.filter_by(id_empresa=usuario.id_empresa).all()
    krs = KR.query.filter_by(id_empresa=usuario.id_empresa).all()  # Adicionado aqui
    macro_acoes = MacroAcao.query.filter_by(empresa_id=usuario.id_empresa).all()
    sprints = Sprint.query.filter_by(usuario_id=usuario.id).all()

    # Adicionado código de depuração
    print(f"Usuario: {usuario.nome}")
    print(f"Empresa: {empresa.nome_contato}")
    print(f"OKRs: {[okr.objetivo for okr in okrs]}")
    print(f"KRs: {[kr.texto for kr in krs]}")
    print(f"Macro Ações: {[acao.texto for acao in macro_acoes]}")
    print(f"Sprints: {[sprint.tarefa for sprint in sprints]}")

    if request.method == 'POST':
        # Aqui você pode iniciar o processo que mencionou
        pass

    return render_template('montar_tarefas_semana.html', empresa=empresa, usuario=usuario, okrs=okrs, krs=krs, macro_acoes=macro_acoes, sprints=sprints)



@app.route('/cadastrar/tarefa_semanal', methods=['GET', 'POST'])
@login_required
def cadastrar_tarefa_semanal():
    if request.method == 'POST':
        id_empresa = int(request.form.get('empresa', '0'))
        id_usuario = int(request.form.get('usuario', '0'))
        tarefa_semana = request.form['tarefa_semana']
        data_para_conclusao_str = request.form['data_para_conclusao']

        empresa = db.session.get(Empresa, id_empresa)
        usuario = db.session.get(Usuario, id_usuario)

        if empresa is None or usuario is None:
            return "Empresa ou Usuário não encontrado", 404

        # Converta a string da data para um objeto datetime
        data_para_conclusao = datetime.strptime(data_para_conclusao_str, '%Y-%m-%d')

        passos = []
        datas = []
        i = 0
        while True:
            passo_key = 'passo_' + str(i)
            data_key = 'data_' + str(i)
            if passo_key in request.form:
                passo = request.form[passo_key]
                data_str = request.form[data_key]

                # Converta a string da data para um objeto datetime
                if data_str:  # Verifique se data_str não é uma string vazia
                    data = datetime.strptime(data_str, '%Y-%m-%d')
                else:
                    data = None  # Ou algum valor padrão

                passos.append(passo)
                if data:  # Verifique se data não é None antes de chamar strftime
                    datas.append(data.strftime('%Y-%m-%d'))  # Converta o objeto datetime para uma string
                else:
                    datas.append(None)  # Ou algum valor padrão
                i += 1
            else:
                break

        to_do = json.dumps({"passos": passos, "datas": datas})

        tarefa_semanal = TarefaSemanal(
            empresa_id=empresa.id,
            usuario_id=usuario.id,
            tarefa_semana=tarefa_semana,
            to_do=to_do,
            data_para_conclusao=data_para_conclusao,
        )
        db.session.add(tarefa_semanal)
        db.session.commit()
        return redirect(url_for('listar_tarefas_semanais_usuario'))

    empresas = Empresa.query.all()
    usuarios = Usuario.query.all()
    return render_template('cadastrar_tarefas_semanais_usuario.html', empresas=empresas, usuarios=usuarios)


@app.route('/refazer_tarefa/<int:usuario_id>', methods=['POST'])
@login_required
def refazer_tarefa(usuario_id):
    # Obter o feedback do usuário
    feedback = request.form.get('feedback')

    # Obter a resposta anterior do GPT
    resposta_anterior = session.get('resposta')

    # Obter o usuário pelo ID
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        return redirect(url_for('montar_tarefa_semana'))  # Se o usuário não existir, redirecionar

    # Obter a empresa associada ao usuário
    empresa = db.session.get(Empresa, usuario.id_empresa)

    # Obter as macro ações associadas à empresa
    macro_acoes = MacroAcao.query.filter_by(empresa_id=empresa.id).all()

    # Obter os OKRs associados à empresa
    okrs = OKR.query.filter_by(id_empresa=empresa.id).all()

    # Obter os KRs associados à empresa
    krs = KR.query.filter_by(id_empresa=empresa.id).all()

    # Obter os sprints associados ao usuário
    sprints = Sprint.query.filter_by(usuario_id=usuario.id).all()

    # Formatar as listas como strings
    macro_acoes_str = ', '.join([acao.texto for acao in macro_acoes])
    okrs_str = ', '.join([okr.objetivo for okr in okrs])
    krs_str = ', '.join([kr.texto for kr in krs])
    sprints_str = ', '.join([f'{sprint.tarefa} ({sprint.data_criacao})' for sprint in sprints])

    # Construir a pergunta para o GPT-4
    pergunta = f"Inteligência Artificial GPT, considerando esse feedback {feedback} pra essa resposta {resposta_anterior}, considerando a lista de macro ações estratégicas geradas a partir dos OKRs {okrs_str} e dos KRs {krs_str}, Resumo sobre a empresa: {empresa.descricao_empresa} e a Lista de macro ações: {macro_acoes_str}, as tarefas da semana {sprints_str} para o colaborador {usuario.nome} {usuario.cargo}  crie to-do para cada tarefa. Provide them in JSON format with the following keys: tarefa, usuario, data_para_conclusão, passo1, data1, passo2, data2, passo3, data3, passo4, data4, passo5, data5, passo6, data6."
    print(pergunta)
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    resposta, messages = perguntar_gpt(pergunta, empresa.id, messages)
    # Imprimir a resposta do GPT
    print(f"Resposta do GPT: {resposta}")
    # Encontra o início e o final do objeto JSON na resposta
    inicio_json = resposta.find('[')
    final_json = resposta.rfind(']')

    # Se não encontramos um objeto JSON, lançamos um erro
    if inicio_json == -1 or final_json == -1:
        print(f"Erro ao decodificar JSON: não foi possível encontrar um objeto JSON na resposta")
        print(f"Resposta: {resposta}")
        return redirect(url_for('montar_tarefa_semana'))

    json_str = resposta[inicio_json:final_json+1]

    # Carrega a resposta JSON
    try:
        tarefas_semana = json.loads(json_str)

    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {str(e)}")
        print(f"Resposta:{resposta}")

        return redirect(url_for('montar_tarefa_semana'))  # Se a decodificação falhar, redirecionar

    # Armazena a resposta, as tarefas da semana e o id do usuário na sessão
    session['resposta'] = resposta
    session['tarefas_semana'] = tarefas_semana
    session['usuario_id'] = usuario_id

    # Redireciona para a página de revisão
    return redirect(url_for('revisar_tarefas'))




@app.route('/revisar_tarefas', methods=['GET'])
@login_required
def revisar_tarefas():
    # Obter o ID do usuário da sessão
    usuario_id = session.get('usuario_id')
    if usuario_id is None:
        print("Erro: usuario_id não encontrado na sessão")
        return redirect(url_for('montar_tarefa_semana'))

    # Obter o usuário pelo ID
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        print(f"Erro: Não foi possível encontrar o usuário com o ID {usuario_id}")
        return redirect(url_for('montar_tarefa_semana'))  # Se o usuário não existir, redirecionar

    # Obter as tarefas da semana da sessão
    tarefas_semana = session.get('tarefas_semana', [])
    if not tarefas_semana:
        print("Erro: tarefas_semana não encontradas na sessão")

    # Renderizar o template 'revisar_tarefas.html'
    return render_template('revisar_tarefas.html', usuario=usuario, tarefas_semana=tarefas_semana)




@app.route('/aprovar_tarefas', methods=['POST'])
@login_required
def aprovar_tarefas():
    usuario_id = session.get('usuario_id')
    tarefas_semana = session.get('tarefas_semana', [])

    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        return redirect(url_for('montar_tarefa_semana'))

    for tarefa in tarefas_semana:
        passos = []
        datas = []
        for i in range(1, 7):
            passo_key = 'passo' + str(i)
            data_key = 'data' + str(i)
            passo = tarefa.get(passo_key, '')
            data_str = tarefa.get(data_key, '')

            if data_str:
                data = datetime.strptime(data_str, '%Y-%m-%d')
            else:
                data = None

            passos.append(passo)
            if data:
                datas.append(data.strftime('%Y-%m-%d'))
            else:
                datas.append(None)

        to_do = json.dumps({"passos": passos, "datas": datas})

        data_para_conclusao_str = tarefa.get('data_para_conclusão')
        data_para_conclusao = None

        # Tenta vários formatos de data
        for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
            try:
                data_para_conclusao = datetime.strptime(data_para_conclusao_str, fmt)
                break  # Se a conversão for bem sucedida, saia do loop
            except ValueError:
                pass  # Se a conversão falhar, continue para o próximo formato

        tarefa_semanal = TarefaSemanal(
            empresa_id=usuario.id_empresa,
            usuario_id=usuario_id,
            tarefa_semana=tarefa.get('tarefa', ''),
            to_do=to_do,
            data_para_conclusao=data_para_conclusao,
        )
        db.session.add(tarefa_semanal)
    db.session.commit()

    session.pop('usuario_id', None)
    session.pop('tarefas_semana', None)

    return redirect(url_for('listar_tarefas_semanais_usuario'))





@app.route('/listar_tarefas_semanais_usuario', methods=['GET'])
@login_required
def listar_tarefas_semanais_usuario():
    tarefas_semanais = TarefaSemanal.query.all()
    tarefas_decodificadas = []
    for tarefa in tarefas_semanais:
        tarefa_dict = tarefa.__dict__
        tarefa_dict['to_do_decoded'] = tarefa.to_do_decoded
        tarefa_dict['usuario'] = tarefa.usuario.nome
        tarefas_decodificadas.append(tarefa_dict)
    return render_template('listar_tarefas_semanais_usuario.html', tarefas_semanais=tarefas_decodificadas)


@app.route('/atualizar_tarefa_semanal/<int:id>', methods=['GET', 'POST'])
@login_required
def atualizar_tarefa_semanal(id):
    tarefa = TarefaSemanal.query.get_or_404(id)

    if request.method == 'POST':
        tarefa.tarefa_semana = request.form['tarefa_semana']
        tarefa.data_para_conclusao = datetime.strptime(request.form['data_para_conclusao'], '%Y-%m-%d')
        to_do = {
            'passos': [request.form.get(f'passo{i}') for i in range(1, 7) if request.form.get(f'passo{i}')],
            'datas': [request.form.get(f'data{i}') for i in range(1, 7) if request.form.get(f'data{i}')],
            'status': [request.form.get(f'status{i}') for i in range(1, 7) if request.form.get(f'status{i}')]
        }
        tarefa.to_do = json.dumps(to_do)
        tarefa.data_atualizacao = datetime.utcnow()

        # Load and decode 'observacoes' if it exists, otherwise create a new dictionary
        observacoes = json.loads(tarefa.observacoes) if tarefa.observacoes else {}

        # Update 'status_tarefa' and 'observacao_tarefa' in 'observacoes'
        observacoes['status_tarefa'] = request.form['status_tarefa']
        observacoes['observacao_tarefa'] = request.form['observacao_tarefa']

        tarefa.observacoes = json.dumps(observacoes)

        db.session.commit()
        return redirect(url_for('listar_tarefas_semanais_usuario'))

    # If 'status' key does not exist in the 'to_do' dictionary, add it with the value 'criado' for each step
    if 'status' not in tarefa.to_do_decoded:
        print("Adding status to to_do_decoded")  # print a message to check if this code is being executed
        new_to_do = tarefa.to_do_decoded.copy()  # create a new dictionary and copy all data from to_do_decoded
        new_to_do['status'] = ['criado' for _ in
                               range(len(tarefa.to_do_decoded['passos']))]  # add status to the new dictionary
        print(new_to_do)  # print the new dictionary to check if status was added
        tarefa.to_do = json.dumps(new_to_do)  # save the new dictionary to the database
        db.session.commit()

    # Load and decode 'observacoes' if it exists, otherwise create a new dictionary
    observacoes = json.loads(tarefa.observacoes) if tarefa.observacoes else {}

    # If 'status_tarefa' and 'observacao_tarefa' are not in 'observacoes'
    if not ('status_tarefa' in observacoes and 'observacao_tarefa' in observacoes):
        observacoes['status_tarefa'] = 'pendente'
        observacoes['observacao_tarefa'] = ''
        tarefa.observacoes = json.dumps(observacoes)
        db.session.commit()

    return render_template('atualizar_tarefa_semanal.html', tarefa=tarefa)


@app.route('/deletar_todo/<int:id>/<int:todo_index>', methods=['POST'])
@login_required
def deletar_todo(id, todo_index):
    tarefa = TarefaSemanal.query.get_or_404(id)
    to_do_decoded = tarefa.to_do_decoded

    # Remove the to-do at the given index from each list in the to_do_decoded dictionary
    for key in to_do_decoded:
        del to_do_decoded[key][todo_index]

    # Save the updated to_do_decoded back to the database
    tarefa.to_do = json.dumps(to_do_decoded)
    db.session.commit()

    return redirect(url_for('atualizar_tarefa_semanal', id=id))





@app.route('/deletar_tarefa_semanal/<int:id>', methods=['POST'])
@login_required
def deletar_tarefa_semanal(id):
    tarefa = TarefaSemanal.query.get_or_404(id)
    db.session.delete(tarefa)
    db.session.commit()
    return redirect(url_for('listar_tarefas_semanais_usuario'))

#############################################################################

#################################### MACROAÇÃO #########################################


@app.route('/listar_macro_acao')
@login_required
def listar_macro_acao():
    krs = KR.query.all()  # Busca todos os KR do banco de dados
    return render_template('listar_macro_acao.html', krs=krs)

@app.route('/listar_macro_acoes_aprovadas', methods=['GET'])
@login_required
def listar_macro_acoes_aprovadas():
    macro_acoes = MacroAcao.query.all()
    return render_template('listar_macro_acoes_aprovadas.html', macro_acoes=macro_acoes)


@app.route('/gerar_macro_acao/<int:id>', methods=['GET', 'POST'])
@login_required
def gerar_macro_acao(id):
    time_now = datetime.utcnow()  # Salve o horário atual
    kr = KR.query.get(id)  # Busca o KR específico pelo id
    if kr is None:
        flash('KR não encontrado', 'error')
        return redirect(url_for('listar_macro_acao'))

    if request.method == 'POST':
        # Gera a pergunta para o GPT-4
        pergunta = f"Considerando o Key Result {kr.texto} definidos para o objetivo: {kr.okr.objetivo} para a empresa {kr.okr.empresa.descricao_empresa} para os próximos 90 dias, eu gostaria que você gerasse uma lista de macro ações estratégicas necessárias para alcançar esses KRs. Depois de gerar essa lista, por favor, organize as ações em ordem de prioridade, levando em consideração a eficiência e a eficácia na realização dos KRs. Provide them in JSON format with the following keys: prioridade, acao."
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        resposta, messages = perguntar_gpt(pergunta, id, messages)

        # Carrega a resposta JSON
        resposta_dict = json.loads(resposta)
        # Verifica se a resposta é uma lista ou um dicionário com a chave 'acoes'
        if isinstance(resposta_dict, list):
            print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
            macro_acoes = resposta_dict
        elif 'acoes' in resposta_dict:
            macro_acoes = resposta_dict['acoes']
        else:
            raise ValueError("Resposta inesperada: não é uma lista nem contém a chave 'acoes'")

        # Adiciona um ID a cada ação
        for i, acao in enumerate(macro_acoes, start=1):
            acao['id'] = i

        # Armazena a resposta, as macro ações e o id do KR na sessão
        session['resposta'] = resposta
        session['macro_acoes'] = macro_acoes
        session['kr_id'] = id

        # Redireciona para a página de revisão
        return redirect(url_for('revisar_macro_acoes'))

    return render_template('gerar_macro_acao.html', kr=kr)


@app.route('/revisar_macro_acoes', methods=['GET', 'POST'])
@login_required
def revisar_macro_acoes():
    if request.method == 'POST':
        macro_acoes = session.get('macro_acoes')
        kr_id = session.get('kr_id')
        kr = KR.query.get(kr_id)
        print(macro_acoes)
        for acao in macro_acoes:
            # Cria uma nova entrada em MacroAcao para cada ação na resposta
            macro_acao = MacroAcao(
                texto=acao['acao'],
                aprovada=False,  # Inicialmente, a ação não é aprovada
                kr_id=kr_id,
                objetivo=kr.okr.objetivo,
                objetivo_id=kr.okr.id,
                empresa=kr.okr.empresa.nome_contato,
                empresa_id=kr.okr.empresa.id
            )

            # Salva a nova entrada no banco de dados
            db.session.add(macro_acao)
        db.session.commit()

        # Redireciona para a página de resultados
        return redirect(url_for('mostrar_resultados', kr_id=kr_id))

    else:
        macro_acoes = session.get('macro_acoes')
        return render_template('revisar_macro_acoes.html', macro_acoes=macro_acoes)

@app.route('/refazer_macro_acao/<int:id>', methods=['POST'])
@login_required
def refazer_macro_acao(id):
    feedback = request.form.get('feedback')  # Obtenha o feedback do formulário
    resposta_anterior = session.get('resposta')  # Obtenha a resposta anterior da sessão
    kr = KR.query.get(id)  # Busca o KR específico pelo id

    # Gera a pergunta para o GPT-4
    pergunta = f"Considerando essa resposta {resposta_anterior}, e esse feedback {feedback}, Considerando o Key Result {kr.texto} definidos para o objetivo: {kr.okr.objetivo} para a empresa {kr.okr.empresa.descricao_empresa} para os próximos 90 dias, eu gostaria que você gerasse uma lista de macro ações estratégicas necessárias para alcançar esses KRs. Depois de gerar essa lista, por favor, organize as ações em ordem de prioridade, levando em consideração a eficiência e a eficácia na realização dos KRs. Provide them in JSON format with the following keys: prioridade, acao."
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    resposta, messages = perguntar_gpt(pergunta, id, messages)

    print(f'Resposta: {resposta}')  # Imprime a resposta

    # Carrega a resposta JSON
    resposta_dict = json.loads(resposta)
    print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK")
    # Verifica se a resposta é uma lista ou um dicionário com a chave 'acoes'
    if isinstance(resposta_dict, list):
        macro_acoes = resposta_dict
    elif 'acoes' in resposta_dict:
        macro_acoes = resposta_dict['acoes']
    else:
        raise ValueError("Resposta inesperada: não é uma lista nem contém a chave 'acoes'")

    # Adiciona um ID a cada ação
    for i, acao in enumerate(macro_acoes, start=1):
        acao['id'] = i

    # Armazena a nova resposta e as novas macro ações na sessão
    session['resposta'] = resposta
    session['macro_acoes'] = macro_acoes

    # Redireciona para a página de revisão
    return redirect(url_for('revisar_macro_acoes'))


@app.route('/atualizar_macro_acao/<int:id>', methods=['GET', 'POST'])
@login_required
def atualizar_macro_acao(id):
    macro_acao = MacroAcao.query.get(id)
    if request.method == 'POST':
        macro_acao.texto = request.form['texto']
        macro_acao.aprovada = True if request.form['aprovada'] == 'sim' else False
        db.session.commit()
        return redirect(url_for('listar_macro_acoes_aprovadas'))
    return render_template('atualizar_macro_acao.html', acao=macro_acao)


@app.route('/deletar_macro_acao/<int:id>', methods=['GET'])
@login_required
def deletar_macro_acao(id):
    macro_acao = MacroAcao.query.get(id)
    db.session.delete(macro_acao)
    db.session.commit()
    return redirect(url_for('listar_macro_acoes_aprovadas'))




@app.route('/get_macro_acoes_sprint/<int:empresa_id>')
@login_required
def get_macro_acoes_sprint(empresa_id):
    macro_acoes = MacroAcao.query.filter_by(id_empresa=empresa_id)
    return jsonify([macro_acao.texto for macro_acao in macro_acoes])


@app.route('/cadastrar/macro_acao', methods=['GET', 'POST'])
@login_required
def cadastrar_macro_acao():
    if request.method == 'POST':
        id_empresa = int(request.form.get('empresa', '0'))
        id_objetivo = int(request.form.get('objetivo', '0'))
        id_kr = int(request.form.get('kr', '0'))
        texto = request.form['texto']

        empresa = Empresa.query.get(id_empresa)
        objetivo = OKR.query.get(id_objetivo)
        kr = KR.query.get(id_kr)

        if empresa is None or objetivo is None or kr is None:
            return "Empresa, Objetivo ou KR não encontrado", 404

        macro_acao = MacroAcao(
            texto=texto,
            kr_id=kr.id,
            objetivo=objetivo.objetivo,
            objetivo_id=objetivo.id,
            empresa=empresa.nome_contato,
            empresa_id=empresa.id,
        )
        db.session.add(macro_acao)
        db.session.commit()
        return redirect(url_for('listar_macro_acoes_aprovadas'))  # Redirecionamento atualizado

    empresas = Empresa.query.all()
    objetivos = OKR.query.all()
    krs = KR.query.all()
    return render_template('cadastrar_macro_acao.html', empresas=empresas, objetivos=objetivos, krs=krs)


#############################################################################

#################################### MURAL #########################################

@app.route('/selecionar_empresa_mural', methods=['GET', 'POST'])
@login_required
def selecionar_empresa_mural():
    empresas = Empresa.query.all()
    if request.method == 'POST':
        empresa_id = request.form.get('empresa')
        return redirect(url_for('mural', empresa_id=empresa_id))
    return render_template('selecionar_empresa_mural.html', empresas=empresas)


@app.route('/mural/<int:empresa_id>', methods=['GET', 'POST'])
@login_required
def mural(empresa_id):
    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        flash('Empresa não encontrada.', 'error')
        return redirect(url_for('index'))

    objetivos = OKR.query.filter_by(id_empresa=empresa_id).all()
    krs = KR.query.filter_by(id_empresa=empresa_id).all()
    macro_acoes = MacroAcao.query.filter_by(empresa_id=empresa_id).all()
    tarefas = TarefaSemanal.query.filter_by(empresa_id=empresa_id).all()

    return render_template('mural.html', empresa=empresa, objetivos=objetivos, krs=krs, macro_acoes=macro_acoes, tarefas=tarefas)

#############################################################################

#################################### SPRINT #########################################



@app.route('/montagem_sprint_semana')
@login_required
def montagem_sprint_semana():
    empresas = Empresa.query.all()
    return render_template('montagem_sprint_semana.html', empresas=empresas)



@app.route('/get_descricao_sprint/<int:empresa_id>')
@login_required
def get_descricao_sprint(empresa_id):
    empresa = Empresa.query.get(empresa_id)
    return jsonify(descricao=empresa.descricao_empresa)

@app.route('/get_cargos_sprint/<int:empresa_id>')
@login_required
def get_cargos_sprint(empresa_id):
    usuarios = Usuario.query.filter_by(id_empresa=empresa_id)
    return jsonify([usuario.cargo for usuario in usuarios])


@app.route('/criar_sprint_semana', methods=['GET', 'POST'])
@login_required
def criar_sprint_semana():
    if request.method == 'POST':
        # Coletar informações da empresa
        empresa_id = request.form.get('empresa')
        empresa = db.session.get(Empresa, empresa_id)  # Obter a empresa pelo ID
        if empresa is None:
            return redirect(url_for('montagem_sprint_semana'))  # Se a empresa não existir, redirecionar

        # Obter as macro ações associadas à empresa
        macro_acoes = MacroAcao.query.filter_by(empresa_id=empresa.id).all()

        # Obter os OKRs e usuários associados à empresa
        okrs = OKR.query.filter_by(id_empresa=empresa.id).all()
        usuarios = Usuario.query.filter_by(id_empresa=empresa.id).all()

        # Formatar as listas como strings
        macro_acoes_str = ', '.join([acao.texto for acao in macro_acoes])
        okrs_str = ', '.join([okr.objetivo for okr in okrs])
        usuarios_str = ', '.join([f'{usuario.nome} ({usuario.cargo})' for usuario in usuarios])

        # Construir a pergunta para o GPT-4
        pergunta = f"Inteligência Artificial GPT, considerando a lista de macro ações estratégicas geradas a partir dos OKRs {okrs_str} da empresa para os próximos 90 dias, as habilidades específicas dos colaboradores da equipe {usuarios_str}, peço que você desenvolva um plano de sprint para a próxima semana. Para ajudar a moldar esse plano, aqui estão as informações que você precisa considerar: Lista de macro ações: {macro_acoes_str}, Habilidades dos colaboradores: {usuarios_str}, Resumo sobre a empresa: {empresa.descricao_empresa}. Com base nessas informações, por favor, crie um plano de sprint que defina as tareas específicas a serem realizadas na próxima semana, priorizando as ações mais críticas e detalhando como essas tarefas suportam os OKRs definidos. Além disso, coloque o responsável por cada tarefa específica de acordo com a tarefa e o cargo dos colaboradores. Provide them in JSON format with the following keys: prioridade, tarefa, responsável."
        print(pergunta)
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        resposta, messages = perguntar_gpt(pergunta, empresa_id, messages)

        # Encontra o início e o final do objeto JSON na resposta
        inicio_json = resposta.find('[')
        final_json = resposta.rfind(']')

        # Se não encontramos um objeto JSON, lançamos um erro
        if inicio_json == -1 or final_json == -1:
            print(f"Erro ao decodificar JSON: não foi possível encontrar um objeto JSON na resposta")
            print(f"Resposta: {resposta}")
            return redirect(url_for('montagem_sprint_semana'))  # Se a decodificação falhar, redirecionar

        json_str = resposta[inicio_json:final_json+1]

        # Carrega a resposta JSON
        try:
            sprints = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {str(e)}")
            print(f"Resposta:{resposta}")

            return redirect(url_for('montagem_sprint_semana'))  # Se a decodificação falhar, redirecionar

        # Armazena a resposta, os sprints e o id da empresa na sessão
        session['resposta'] = resposta
        session['sprints'] = sprints
        session['empresa_id'] = empresa_id

        # Redireciona para a página de revisão
        return redirect(url_for('revisar_sprint'))

    # Renderiza o template de criação de sprint
    return render_template('montagem_sprint_semana.html')


@app.route('/revisar_sprint', methods=['GET', 'POST'])
@login_required
def revisar_sprint():
    if request.method == 'POST':
        # Aqui, vamos adicionar os sprints ao banco de dados
        sprints = session.get('sprints', [])
        empresa_id = session.get('empresa_id')
        empresa = db.session.get(Empresa, empresa_id)
        for sprint in sprints:
            if isinstance(sprint, dict):
                nome_usuario_responsavel = sprint.get('responsável', '')
                usuario_responsavel = Usuario.query.filter_by(nome=nome_usuario_responsavel).first()
                sprint_db = Sprint(
                    empresa_id=empresa_id,
                    nome_empresa=empresa.nome_contato,
                    prioridade=sprint.get('prioridade', ''),
                    tarefa=sprint.get('tarefa', ''),
                    usuario=usuario_responsavel
                )
                db.session.add(sprint_db)
        db.session.commit()

        # Limpa os dados da sessão
        session.pop('resposta', None)
        session.pop('sprints', None)
        session.pop('empresa_id', None)

        # Redireciona para a página de resultados
        return redirect(url_for('resultado_sprint'))

    # Renderiza o template de revisão de sprint
    return render_template('revisar_sprint.html')


@app.route('/aprovar_sprints', methods=['POST'])
@login_required
def aprovar_sprints():
    # Aqui, você pode adicionar o código para aprovar os sprints
    # Por exemplo, você pode adicionar os sprints ao banco de dados
    sprints = session.get('sprints', [])
    empresa_id = session.get('empresa_id')
    empresa = db.session.get(Empresa, empresa_id)
    for sprint in sprints:
        if isinstance(sprint, dict):
            nome_usuario_responsavel = sprint.get('responsável', '')
            usuario_responsavel = Usuario.query.filter_by(nome=nome_usuario_responsavel).first()
            sprint_db = Sprint(
                empresa_id=empresa_id,
                nome_empresa=empresa.nome_contato,
                prioridade=sprint.get('prioridade', ''),
                tarefa=sprint.get('tarefa', ''),
                usuario=usuario_responsavel
            )
            db.session.add(sprint_db)
    db.session.commit()

    # Limpa os dados da sessão
    session.pop('resposta', None)
    session.pop('sprints', None)
    session.pop('empresa_id', None)

    # Redireciona para a página de resultados
    return redirect(url_for('resultado_sprint'))



@app.route('/refazer_sprint', methods=['POST'])
@login_required
def refazer_sprint():
    # Obter o feedback do usuário
    feedback = request.form.get('feedback')

    # Obter as informações da empresa
    empresa_id = session.get('empresa_id')
    empresa = db.session.get(Empresa, empresa_id)  # Obter a empresa pelo ID
    if empresa is None:
        return redirect(url_for('montagem_sprint_semana'))  # Se a empresa não existir, redirecionar

    # Obter as macro ações associadas à empresa
    macro_acoes = MacroAcao.query.filter_by(empresa_id=empresa.id).all()

    # Obter os OKRs e usuários associados à empresa
    okrs = OKR.query.filter_by(id_empresa=empresa.id).all()
    usuarios = Usuario.query.filter_by(id_empresa=empresa.id).all()

    # Formatar as listas como strings
    macro_acoes_str = ', '.join([acao.texto for acao in macro_acoes])
    okrs_str = ', '.join([okr.objetivo for okr in okrs])
    usuarios_str = ', '.join([f'{usuario.nome} ({usuario.cargo})' for usuario in usuarios])

    # Obter a resposta anterior
    resposta_anterior = session.get('resposta')

    # Construir a pergunta para o GPT-3
    pergunta = f"Considerando essa resposta {resposta_anterior}, e esse feedback {feedback}, considerando a lista de macro ações estratégicas geradas a partir dos OKRs {okrs_str} da empresa para os próximos 90 dias, as habilidades específicas dos colaboradores da equipe {usuarios_str}, peço que você desenvolva um plano de sprint para a próxima semana. Para ajudar a moldar esse plano, aqui estão as informações que você precisa considerar: Lista de macro ações: {macro_acoes_str}, Habilidades dos colaboradores: {usuarios_str}, Resumo sobre a empresa: {empresa.descricao_empresa}. Com base nessas informações, por favor, crie um plano de sprint que defina as tareas específicas a serem realizadas na próxima semana, priorizando as ações mais críticas e detalhando como essas tarefas suportam os OKRs definidos. Além disso, coloque o responsável por cada tarefa específica de acordo com a tarefa e o cargo dos colaboradores. Provide them in JSON format with the following keys: prioridade, tarefa, responsável."
    print(pergunta)
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    resposta, messages = perguntar_gpt(pergunta, empresa_id, messages)

    # Encontra o início e o final do objeto JSON na resposta
    inicio_json = resposta.find('[')
    final_json = resposta.rfind(']')

    # Se não encontramos um objeto JSON, lançamos um erro
    if inicio_json == -1 or final_json == -1:
        print(f"Erro ao decodificar JSON: não foi possível encontrar")
        return redirect(url_for('montagem_sprint_semana'))

    # Extrair o objeto JSON da resposta
    json_str = resposta[inicio_json:final_json+1]

    # Decodificar o objeto JSON
    sprints = json.loads(json_str)

    # Salvar os sprints na sessão
    session['sprints'] = sprints

    # Redirecionar para a página de revisão de sprints
    return redirect(url_for('revisar_sprint'))



@app.route('/montagem_lista_usuario_sprint', methods=['GET', 'POST'])
@login_required
def montagem_lista_usuario_sprint():
    if request.method == 'POST':
        empresa_id = request.form.get('empresa')
        usuarios = Usuario.query.filter_by(id_empresa=empresa_id).all()
        return render_template('lista_usuario_sprint.html', usuarios=usuarios)
    empresas = Empresa.query.all()
    return render_template('montagem_lista_usuario_sprint.html', empresas=empresas)

@app.route('/lista_usuario_sprint', methods=['GET', 'POST'])
@login_required
def lista_usuario_sprint():
    if request.method == 'POST':
        empresa_id = request.form.get('empresa')
        usuarios = Usuario.query.filter_by(empresa_id=empresa_id).all()
        return render_template('lista_usuario_sprint.html', usuarios=usuarios)
    empresas = Empresa.query.all()
    return render_template('selecionar_empresa.html', empresas=empresas)


@app.route('/cadastrar/sprint', methods=['GET', 'POST'])
@login_required
def cadastrar_sprint():
    if request.method == 'POST':
        id_empresa = int(request.form.get('empresa', '0'))
        id_usuario = int(request.form.get('usuario', '0'))
        tarefa = request.form['tarefa']
        prioridade = int(request.form.get('prioridade', '0'))

        empresa = Empresa.query.get(id_empresa)
        usuario = Usuario.query.get(id_usuario)

        if empresa is None or usuario is None:
            return "Empresa ou Usuário não encontrado", 404

        sprint = Sprint(
            nome_empresa=empresa.nome_contato,
            empresa_id=empresa.id,
            prioridade=prioridade,
            tarefa=tarefa,
            usuario_id=usuario.id,
            usuario_grupo='',  # Definido como string vazia
            data_criacao=datetime.utcnow()
        )
        db.session.add(sprint)
        db.session.commit()
        return redirect(url_for('listar_sprints_semana'))


    empresas = Empresa.query.all()
    usuarios = Usuario.query.all()
    return render_template('cadastrar_sprint.html', empresas=empresas, usuarios=usuarios)

@app.route('/resultado_sprint')
@login_required
def resultado_sprint():
    if 'empresa_id' not in session:
        return redirect(url_for('montagem_sprint_semana'))  # Se não há empresa, redirecionar

    # Pegar o id da empresa da sessão
    empresa_id = session['empresa_id']

    # Remover o id da empresa da sessão
    session.pop('empresa_id', None)

    # Buscar os sprints do banco de dados
    sprints = Sprint.query.filter_by(empresa_id=empresa_id).all()

    return render_template('resultado_sprint.html', sprints=sprints, empresa_id=empresa_id)



@app.route('/listar_sprints_semana', methods=['GET'])
@login_required
def listar_sprints_semana():
    sprints = Sprint.query.all()
    return render_template('listar_sprints_semana.html', sprints=sprints)


@app.route('/atualizar_sprint/<int:id>', methods=['GET', 'POST'])
@login_required
def atualizar_sprint(id):
    sprint = Sprint.query.get(id)
    if request.method == 'POST':
        tarefa = request.form.get('tarefa')
        sprint.tarefa = tarefa
        db.session.commit()
        return redirect(url_for('listar_sprints_semana'))
    return render_template('atualizar_sprint.html', sprint=sprint)

@app.route('/deletar_sprint/<int:id>', methods=['GET', 'POST'])
@login_required
def deletar_sprint(id):
    sprint = Sprint.query.get(id)
    db.session.delete(sprint)
    db.session.commit()
    return redirect(url_for('listar_sprints_semana'))

@app.route('/revisao_sprint_semana', methods=['GET', 'POST'])
def revisao_sprint_semana():
    if request.method == 'POST':
        empresa_id = request.form.get('empresa_id')
        return redirect(url_for('listar_revisao_sprint_semana', empresa_id=empresa_id))
    empresas = Empresa.query.all()
    return render_template('revisao_sprint_semana.html', empresas=empresas)


@app.route('/listar_revisao_sprint_semana/<int:empresa_id>', methods=['GET'])
def listar_revisao_sprint_semana(empresa_id):
    sprints = Sprint.query.filter_by(empresa_id=empresa_id).all()
    return render_template('listar_revisao_sprint_semana.html', sprints=sprints)

#############################################################################

#################################### WHATSAPP #########################################

@app.route('/api/send_whatsapp/<id>/<user_id>', methods=['POST'])
def send_whatsapp(id, user_id):
    try:
        print(f"Sending whatsapp for analysis ID: {id}")
        # Locate the analysis by id
        analise = AnaliseInstagram.query.get(id)

        if analise is None:
            print(f"Analysis not found for ID: {id}")
            return jsonify({'error': 'Analysis not found'}), 404

        # Locate the user by id
        user = Usuario.query.get(user_id)

        if user is None:
            print(user)
            print(f"User not found for ID: {user_id}")
            return jsonify({'error': 'User not found'}), 404

        whatsapp_to = user.celular
        whatsapp_message = analise.analise

        headers = {
            'Authorization': 'Bearer '+ os.getenv("WHATSAPP_TOKEN"),
            'Content-Type': 'application/json'
        }
        
        body = {
            "messaging_product": "whatsapp",
            "to": "5521964802282",
            "type": "template",
            "template": {
                "name": "envios_analises",
                "language": {
                    "code": "pt_BR"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "text",
                                "text": user.nome + ' ' + user.sobrenome
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": "Análise teste 123"
                            }
                        ]
                    }
                ]
            }
        }
        
       

        response = requests.post('https://graph.facebook.com/v17.0/112868715169108/messages', headers=headers, data=json.dumps(body))

        print("Full response from Facebook API:")
        print(response.text)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to send WhatsApp message'}), 500

        

        return jsonify({'message': 'WhatsApp message sent'}), 200
    except Exception as e:
        print("Exception occurred: ", str(e))
        return jsonify({'error': 'Internal Server Error'}), 500
    
#############################################################################


#################################### EMAIL #########################################

@app.route('/api/send_email/<id>/<user_id>', methods=['POST'])
def send_email(id, user_id):
    try:
        print(f"Sending email for analysis ID: {id}")
        # Localize a análise por id
        analise = AnaliseInstagram.query.get(id)

        if analise is None:
            print(f"Analysis not found for ID: {id}")
            return jsonify({'error': 'Analysis not found'}), 404

        # Localize o usuário por id
        user = Usuario.query.get(user_id)

        if user is None:
            print(user)
            print(f"User not found for ID: {user_id}")
            return jsonify({'error': 'User not found'}), 404

        email_to = user.email
        email_subject = 'Assunto do E-mail'
        email_body = f'Análise: {analise.analise}'
        mail = Mail(app)
        msg = Message(email_subject,
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email_to],
                      body=email_body)

        mail.send(msg)
        print(f"Email sent to: {email_to}")

        return jsonify({'message': 'Email sent'}), 200
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

#############################################################################

#################################### USUÁRIOS #########################################

@app.route('/cadastrar/usuario', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form.get('password'), method='sha256')
        usuario = Usuario(
            nome=request.form.get('nome'),
            sobrenome=request.form.get('sobrenome'),
            email=request.form.get('email'),
            celular=request.form.get('celular'),
            id_empresa=request.form.get('id_empresa'),
            cargo=request.form.get('cargo'),
            status=request.form.get('status'),
            password=hashed_password
        )
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('listar_usuarios'))
    empresas = Empresa.query.all()
    return render_template('cadastrar_usuario.html', empresas=empresas)


@app.route('/usuarios', methods=['GET'])
@login_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('listar_usuarios.html', usuarios=usuarios)

@app.route('/atualizar/usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def atualizar_usuario(id):
    usuario = Usuario.query.get(id)
    if request.method == 'POST':
        usuario.nome = request.form['nome']
        usuario.sobrenome = request.form['sobrenome']
        usuario.email = request.form['email']
        usuario.celular = request.form['celular']
        usuario.id_empresa = request.form['id_empresa']  # Alterado aqui
        usuario.cargo = request.form['cargo']
        usuario.status = request.form['status']
        db.session.commit()
        return redirect(url_for('listar_usuarios'))
    empresas = Empresa.query.all()
    return render_template('atualizar_usuario.html', usuario=usuario, empresas=empresas)

@app.route('/deletar_usuario/<int:id>', methods=['POST'])
@login_required
def deletar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('listar_usuarios'))




@app.route('/get_usuarios/<int:empresa_id>')
@login_required
def get_usuarios(empresa_id):
    usuarios = Usuario.query.filter_by(id_empresa=empresa_id).all()
    return jsonify([{'id': usuario.id, 'nome': usuario.nome} for usuario in usuarios])


#############################################################################

#################################### POSTS #########################################

@app.route('/cadastrar/post', methods=['POST'])
@login_required
def cadastrar_post():
        empresas = Empresa.query.filter(Empresa.vincular_instagram.isnot(None)).all()

        posts = PostsInstagram(
            timestamp=request.form.get('timestamp'),
            caption=request.form.get('caption'),
            like_count=request.form.get('like_count'),
            comments_count=request.form.get('comments_count'),
            reach=request.form.get('reach'),
            percentage=request.form.get('percentage'),
            media_product_type=request.form.get('media_product_type'),
            plays = request.form.get('plays'),
            saved=request.form.get('saved'),
            nome_empresa=request.form.get('nome_empresa')
        )
        db.session.add(posts)
        db.session.commit()
        return jsonify({'message': 'Dados inseridos com sucesso!'} ), 201


@app.route('/api/posts', methods=['GET'])
@login_required
def api_posts():
    empresa_selecionada = request.args.get('empresa')
    if empresa_selecionada:
        posts = PostsInstagram.query.filter(PostsInstagram.nome_empresa == empresa_selecionada).order_by(desc(PostsInstagram.timestamp)).all()
    else:
        posts = PostsInstagram.query.order_by(desc(PostsInstagram.timestamp)).all()

    posts = [post.to_dict() for post in posts]  # Convert each post to a dictionary
    return jsonify(posts)




@app.route('/verificar_post_existente', methods=['POST'])
@login_required
def verificar_post_existente():
    data = request.get_json()
    id = data.get('id')
    if not id:
        return jsonify({'error': 'id não fornecido'}), 400

    post = PostsInstagram.query.filter_by(id=id).first()
    if post is None:
        return jsonify({'exists': False})
    else:
        return jsonify({'exists': True})
    
@app.route('/delete_all_posts', methods=['POST'])
@login_required
def delete_all_posts():
    try:
        num_rows_deleted = db.session.query(PostsInstagram).delete()
        db.session.commit()
        print(f"{num_rows_deleted} rows deleted.")
    except Exception as e:
        db.session.rollback()
        print("Error occurred, rollbacked.")
        print(e)
        
@app.route('/listar/posts', methods=['GET'])
@login_required
def listar_posts():
    empresas = Empresa.query.filter(Empresa.vincular_instagram.isnot(None)).all()
    posts = PostsInstagram.query.filter(PostsInstagram.timestamp.isnot(None)).all()
   
    return render_template('listar_posts.html', posts=posts, empresas=empresas)

@app.route('/analise_posts', methods=['GET', 'POST'])
@login_required
def analise_posts():
    try:
        if request.method == 'POST':
            for field, value in request.form.items():
                if len(value) > 64:
                    print(f"Valor muito longo no campo '{field}': {value}")
            posts = PostsInstagram(
                id=request.form.get('id'),
                id_empresa=request.form.get('id_empresa'),
                timestamp=request.form.get('timestamp'),
                caption=request.form.get('caption'),
                like_count=request.form.get('like_count'),
                comments_count=request.form.get('comments_count'),
                reach=request.form.get('reach'),
                percentage=request.form.get('percentage'),
                media_product_type=request.form.get('media_product_type'),
                plays=request.form.get('plays'),
                saved=request.form.get('saved'),
                nome_empresa=request.form.get('nome_empresa')
            )
            db.session.add(posts)
            db.session.commit()
    except DataError as e:
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 201
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 201
        

    empresas = Empresa.query.filter(Empresa.vincular_instagram.isnot(None)).all()

    return render_template('analise_posts.html', empresas=empresas)

def get_last_15_days_posts(empresa):
    # Substitua esta lógica pelo código necessário para obter os posts dos últimos 15 dias
    posts = PostsInstagram.query.filter(PostsInstagram.nome_empresa == empresa).order_by(PostsInstagram.timestamp.desc()).limit(15).all()

    #print(posts)
    # Converter os objetos Post em dicionários
    posts_dict = [post.to_dict() for post in posts]

    return posts_dict

@app.route('/deletar_posts/<int:id>', methods=['POST'])
def deletar_posts(id):
    post = PostsInstagram.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('listar_posts'))

@app.route('/posts_instagram/<int:empresa_id>', methods=['GET', 'POST'])
def posts_instagram(empresa_id):
    
    data = request.get_json()  # Obter os dados JSON enviados pelo cliente
    df = pd.DataFrame(data)  # Converter os dados em um DataFrame do Pandas
        

    df.columns = ['PostName', 'Date', 'MediaReach', 'LikeCount', 'CommentsCount', 'Engajamento', 'ReelPlays']
   

    df = df.sort_values(by='Date', ascending=False)
    df = df.head(15)
    todos_posts_dict = df.to_dict('records')

    todos_posts_str = ""
    for i, post in enumerate(todos_posts_dict, start=1):
        todos_posts_str += f"\nPost {i}:\n"
        todos_posts_str += f"Nome do Post: {post['PostName']}\n"
        todos_posts_str += f"Data: {post['Date']}\n"
        todos_posts_str += f"Audiência: {post['MediaReach']}\n"
        todos_posts_str += f"Número de likes: {post['LikeCount']}\n"
        todos_posts_str += f"Número de comentários: {post['CommentsCount']}\n"
        todos_posts_str += f"Engajamento: {post['Engajamento']}\n"
        todos_posts_str += f"Número de reproduções (reels): {post['ReelPlays']}\n"

    pergunta = [{"role": "system", "content": "Você está conversando com um assistente de IA. Como posso ajudá-lo?"},
                {"role": "user",
                 "content": f"Aqui estão todos os últimos 15 posts:{todos_posts_str}\nPreciso que você analise de acordo com o engajamento e Audiencia esses posts e me diga: 1 - os 3 posts com melhores resultados, a data e porquê 2 - os 3 posts com piores resultados, a data e porquê. 4 - insights do mês (o que temos que melhorar, o que fizemos bem)"}]

    resposta_gpt = perguntar_gpt(pergunta)

    if request.method == 'POST':
        return redirect(url_for('posts_instagram'))

        # ... restante do seu código para analisar o DataFrame ...

#############################################################################

################################ ANÁLISES ###################################


@app.route('/api/analises', methods=['GET'])
def api_analises():
    empresa_selecionada = request.args.get('empresa')
    if empresa_selecionada:
        analises = AnaliseInstagram.query.filter(AnaliseInstagram.nome_empresa == empresa_selecionada).order_by(desc(AnaliseInstagram.data_criacao)).all()
    else:
        analises = AnaliseInstagram.query.order_by(desc(AnaliseInstagram.data_criacao)).all()

    analises = [analise.to_dict() for analise in analises]  # Convert each analise to a dictionary
    return jsonify(analises)

@app.route('/api/analise_posts')
def api_analise_posts():
    empresa = request.args.get('empresa')
    analise = analise_post_instagram(empresa)
    print(analise)
    return jsonify(analise)

@app.route('/api/salvar_analise', methods=['POST'])
def salvar_analise():
    try:
        if request.method == 'POST':
            analise = AnaliseInstagram(
                id=request.form.get('id'),
                nome_empresa=request.form.get('nome_empresa'),
                data_criacao=request.form.get('data_criacao'),
                analise=request.form.get('analise'),
            )
            db.session.add(analise)
            db.session.commit()
            
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Falha ao salvar análise!'}), 500

@app.route('/visualizar_analises', methods=['GET'])
def visualizar_analises():
    nome_empresa = request.args.get('empresa')
    analise = analise_post_instagram(nome_empresa)
    return render_template('listar_analises.html', analise=analise)


def analise_post_instagram(nome_empresa):
    #print('Análise de Post Instagram')

    # Obter os posts dos últimos 15 dias
    posts = get_last_15_days_posts(nome_empresa)
    if not posts:
        print('Posts não encontrados.')
        return

    #print(f"Posts para a empresa de ID: {nome_empresa}")

    todos_posts_str = ""
    for i, post in enumerate(posts, start=1):
        todos_posts_str += f"Legenda: {post['caption']}\n"
        todos_posts_str += f"Data de criação: {post['timestamp']}\n"
        todos_posts_str += f"Número de likes: {post['like_count']}\n"
        todos_posts_str += f"Número de comentários: {post['comments_count']}\n"
        todos_posts_str += f"Alcance: {post['reach']}\n"
        todos_posts_str += f"Engajamento: {post['percentage']}\n"
        todos_posts_str += f"Tipo de mídia: {post['media_product_type']}\n"
        todos_posts_str += f"Número de reproduções (reels): {post['plays']}\n"
        todos_posts_str += f"Número de salvos: {post['saved']}\n"
        todos_posts_str += f"Nome da empresa: {post['nome_empresa']}\n"

    pergunta = [
        {"role": "system", "content": "Você está conversando com um assistente de IA. Como posso ajudá-lo?"},
        {"role": "user", "content": f"Aqui estão todos os posts dos últimos 15 dias:{todos_posts_str}\nPreciso que você analise de acordo com o engajamento e Audiencia esses posts e me diga: 1 - os 3 posts com melhores resultados, a data e porquê 2 - os 3 posts com piores resultados, a data e porquê. 3 - insights do mês (o que temos que melhorar, o que fizemos bem)"}
    ]  
    #print(pergunta)

    resposta_gpt, _ = perguntar_gpt(pergunta=pergunta, pergunta_id=1, messages=[])
        
    #print(resposta_gpt)

    return resposta_gpt


#############################################################################

#################################### EMPRESA #########################################    

@app.route('/empresas', methods=['GET'])
@login_required
def listar_empresas():
    empresas = Empresa.query.all()
    return render_template('listar_empresas.html', empresas=empresas)



@app.route('/deletar_empresa/<int:id>', methods=['POST'])
@login_required
def deletar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    return redirect(url_for('listar_empresas'))


@app.route('/get_empresa_info/<int:empresa_id>', methods=['GET'])
@login_required
def get_empresa_info(empresa_id):
    empresa = Empresa.query.get(empresa_id)
    okrs = OKR.query.filter_by(id_empresa=empresa_id).all()
    krs = KR.query.filter_by(id_empresa=empresa_id).all()
    macro_acoes = MacroAcao.query.filter_by(empresa_id=empresa_id).all()
    usuarios = Usuario.query.filter_by(id_empresa=empresa_id).all()

    empresa_info = {
        'descricao_empresa': empresa.descricao_empresa,
        'objetivos': [okr.objetivo for okr in okrs],
        'krs': [kr.texto for kr in krs],
        'macro_acoes': [acao.texto for acao in macro_acoes],
        'usuarios': [f"{usuario.nome} {usuario.sobrenome}, {usuario.cargo}" for usuario in usuarios]
    }

    return jsonify(empresa_info)





@app.route('/cadastrar/empresa', methods=['GET', 'POST'])
def cadastrar_empresa():
    if request.method == 'POST':
        empresa = Empresa(
            nome_contato=request.form.get('nome_contato'),
            email_contato=request.form.get('email_contato'),
            telefone_contato=request.form.get('telefone_contato'),
            endereco_empresa=request.form.get('endereco_empresa'),
            setor_atuacao=request.form.get('setor_atuacao'),
            tamanho_empresa=request.form.get('tamanho_empresa'),
            descricao_empresa=request.form.get('descricao_empresa'),
            objetivos_principais=request.form.get('objetivos_principais'),
            historico_interacoes=request.form.get('historico_interacoes'),
            vincular_instagram=request.form.get('vincular_instagram')
        )
        db.session.add(empresa)
        db.session.commit()
        return redirect(url_for('listar_empresas'))
    return render_template('cadastrar_empresa.html')

@app.route('/api/empresa/<int:id>/usuarios', methods=['GET'])
def get_users(id):
    users = Usuario.query.filter_by(id_empresa=id).all()
    return jsonify([user.to_dict() for user in users])


@app.route('/atualizar/empresa/<int:id>', methods=['GET', 'POST'])
def atualizar_empresa(id):
    empresa = Empresa.query.get(id)
    if request.method == 'POST':
        empresa.nome_contato = request.form['nome_contato']
        empresa.email_contato = request.form['email_contato']
        empresa.telefone_contato = request.form['telefone_contato']
        empresa.endereco_empresa = request.form['endereco_empresa']
        empresa.setor_atuacao = request.form['setor_atuacao']
        empresa.tamanho_empresa = request.form['tamanho_empresa']
        empresa.descricao_empresa = request.form['descricao_empresa']
        empresa.objetivos_principais = request.form['objetivos_principais']
        empresa.historico_interacoes = request.form['historico_interacoes']
        empresa.vincular_instagram = request.form['vincular_instagram']
        db.session.commit()
        return redirect(url_for('listar_empresas'))
    return render_template('atualizar_empresa.html', empresa=empresa)

#############################################################################

#################################### GPT #########################################


@app.route('/responder_pergunta/<int:id>', methods=['GET', 'POST'])
@login_required
def responder_pergunta(id):
    # Obter o ID da empresa da sessão
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        # Se o ID da empresa não estiver na sessão, redirecionar para a página de planejamento
        return redirect(url_for('planejamento_redes'))

    if id >= len(session['perguntas']):
        # Todas as perguntas foram respondidas
        return redirect(url_for('visualizar_planejamento_atual', id_empresa=empresa_id))

    pergunta = session['perguntas'][id]

    # Inicializa as mensagens com a mensagem do sistema se for a primeira pergunta
    if id == 0:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
    else:
        # Caso contrário, obter as mensagens da sessão
        messages = session.get('messages')

    if request.method == 'POST':
        if 'aprovado' in request.form:
            # Se o método for POST e o usuário aprovou a resposta
            # Verificar se a lista de respostas está vazia antes de tentar acessar o último elemento
            if session['respostas']:
                resposta = session['respostas'][-1]  # A última resposta é a aprovada
            else:
                resposta = None

            # Mapeamento de classificações
            classificacoes = {
                0: "Apresentação",
                1: "Persona",
                2: "Comportamento da persona das Redes",
                3: "Público-Alvo",
                4: "Objetivos das Redes",
                5: "Redes Socais",
                6: "KPI's de acompanhamento",
            }

            resposta_db = Resposta(id_empresa=empresa_id, pergunta=pergunta, resposta=resposta, classificacao=classificacoes[id])
            db.session.add(resposta_db)
            db.session.commit()

            # Redirecionar para a próxima pergunta
            return redirect(url_for('responder_pergunta', id=id+1))
        elif 'feedback_submit' in request.form:
            # Se o método for POST e o usuário enviou feedback
            feedback = request.form['feedback']
            # Adiciona o feedback à lista de mensagens
            messages.append({"role": "user", "content": feedback})

    resposta, messages = perguntar_gpt(pergunta, id, messages)

    # Salvar a resposta e as mensagens na variável de sessão
    session['respostas'].append(resposta)
    session['messages'] = messages

    return render_template('responder_pergunta.html', pergunta=pergunta, resposta=resposta, id=id)

def perguntar_gpt(pergunta, pergunta_id, messages):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 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"
    }

    # Adiciona a pergunta atual
    messages.append({"role": "user", "content": str(pergunta)})


    data = {
        "model": "gpt-4",
        "messages": messages
    }

    backoff_time = 1  # Começamos com um tempo de espera de 1 segundo
    while True:
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            # Adiciona a resposta do modelo à lista de mensagens
            messages.append({"role": "assistant", "content": response.json()['choices'][0]['message']['content']})
            return response.json()['choices'][0]['message']['content'], messages
        except requests.exceptions.HTTPError as e:
            print(e)
            if e.response.status_code in (429, 520):  # Limite de requisições atingido ou erro de servidor
                print(f"Erro {e.response.status_code} atingido. Aguardando antes de tentar novamente...")
                time.sleep(backoff_time)  # Aguarda antes de tentar novamente
                backoff_time *= 2  # Aumenta o tempo de espera
            else:
                raise

#############################################################################


#################################### PLANEJAMENTO #########################################



@app.route('/visualizar_planejamento_atual/<int:id_empresa>', methods=['GET'])
def visualizar_planejamento_atual(id_empresa):
    # Mapeamento de classificações
    classificacoes = [
        "Apresentação",
        "Persona",
        "Comportamento da persona das Redes",
        "Público-Alvo",
        "Objetivos das Redes",
        "Redes Socais",
        "KPI's de acompanhamento",
    ]

    respostas = []
    for classificacao in classificacoes:
        # Buscar a última resposta de cada classificação
        resposta = Resposta.query.filter_by(id_empresa=id_empresa, classificacao=classificacao).order_by(Resposta.data_criacao.desc()).first()
        if resposta:
            respostas.append(resposta)

    return render_template('visualizar_planejamento.html', respostas=respostas)

@app.route('/planejamento_redes', methods=['GET', 'POST'])
def planejamento_redes():
    empresas = Empresa.query.all()
    if request.method == 'POST':
        empresa_id = request.form.get('empresa')  # Obtenha o ID da empresa a partir do formulário
        empresa = Empresa.query.get(empresa_id)
        empresa.descricao_empresa = request.form.get('descricao_empresa')
        db.session.commit()
        # Armazenar o ID da empresa na sessão
        session['empresa_id'] = empresa_id
        # Inicializar a lista de perguntas
        session['perguntas'] = [
            f"Agora você é um especialista de redes sociais dessa empresa: {empresa.descricao_empresa}",
            "Monte uma persona para esse negocio com a dores, objetivos e interesses?",
            "Passe um entendimento de como esse perfil se comportam nas redes sociais e como eles consomem conteudo?",
            "Crie o publico alvo para as redes sociais desse negocio?",
            "Defina quais são os objetivos desse negocio para as redes sociais?",
            "Quais redes sociais e as estrategias a devem ser usadas para essa empresa?",
            "Crie KPI de acompanhamento para essa rede para os proximos 3 meses para essas redes com os seus objetivos a serem alcançados ?"
        ]
        # Inicializar a lista de respostas
        session['respostas'] = []
        # Inicializar a lista de mensagens
        session['messages'] = [{"role": "system", "content": "You are a helpful assistant."}]
        # Redirecionar para a primeira pergunta
        return redirect(url_for('responder_pergunta', id=0))
    return render_template('planejamento_redes.html', empresas=empresas)

#############################################################################




#################################### OKR #########################################





@app.route('/listar/okrs', methods=['GET'])
@login_required
def listar_okrs():
    okrs = OKR.query.all()  # Substitua OKR pela classe do seu modelo de OKR
    return render_template('listar_okrs.html', okrs=okrs)


@app.route('/atualizar/okr/<int:id>', methods=['GET', 'POST'])
@login_required
def atualizar_okr(id):
    okr = OKR.query.get(id)
    empresas = Empresa.query.all()
    if request.method == 'POST':
        okr.id_empresa = request.form['empresa']
        okr.objetivo = request.form['objetivo']
        okr.data_inicio = datetime.strptime(request.form['data_inicio'], "%Y-%m-%d")
        okr.data_fim = datetime.strptime(request.form['data_fim'], "%Y-%m-%d")
        db.session.commit()
        return redirect(url_for('listar_okrs'))
    return render_template('atualizar_okr.html', okr=okr, empresas=empresas)




@app.route('/deletar/okr/<int:id>', methods=['POST'])
@login_required
def deletar_okr(id):
    okr = OKR.query.get(id)
    for kr in okr.krs:
        db.session.delete(kr)
    db.session.delete(okr)
    db.session.commit()
    return redirect(url_for('listar_okrs'))



@app.route('/get_okrs/<int:empresa_id>', methods=['GET'])
@login_required
def get_okrs(empresa_id):
    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        abort(404)  # Retorna um erro 404 se a empresa não for encontrada
    okrs = OKR.query.filter_by(id_empresa=empresa.id).all()

    # Converte a lista de OKRs em uma lista de dicionários para poder ser serializada em JSON
    okrs_dict = []
    for okr in okrs:
        okrs_dict.append({'id': okr.id, 'objetivo': okr.objetivo})

    return jsonify(okrs_dict)



@app.route('/get_okrs_sprint/<int:empresa_id>')
@login_required
def get_okrs_sprint(empresa_id):
    okrs = OKR.query.filter_by(id_empresa=empresa_id)
    return jsonify([okr.objetivo for okr in okrs])

@app.route('/cadastrar/okr', methods=['GET', 'POST'])
@login_required
def cadastrar_okr():
    if request.method == 'POST':
        try:
            okr = OKR(
                id_empresa=request.form.get('empresa'),
                objetivo=request.form.get('objetivo'),
                data_inicio=convert_string_to_datetime(request.form.get('data_inicio')),
                data_fim=convert_string_to_datetime(request.form.get('data_fim')),
            )
            db.session.add(okr)
            db.session.commit()
            return redirect(url_for('listar_okrs'))  # Redireciona para a página de listagem de OKRs
        except ValueError:
            flash('A data fornecida é inválida. Use o formato YYYY-MM-DD.', 'error')
    empresas = Empresa.query.all()
    return render_template('cadastrar_okr.html', empresas=empresas)



#############################################################################

#################################### KR #########################################

@app.route('/listar/krs', methods=['GET'])
@login_required
def listar_krs():
    krs = KR.query.all()
    return render_template('listar_krs.html', krs=krs)



@app.route('/cadastrar/kr', methods=['GET', 'POST'])
@login_required
def cadastrar_kr():
    if request.method == 'POST':
        id_empresa = int(request.form.get('empresa', '0'))  # Obtenha o valor do campo 'empresa' como uma string e converta-o para um inteiro
        id_okr = int(request.form.get('objetivo', '0'))  # Obtenha o valor do campo 'objetivo' como uma string e converta-o para um inteiro
        texto = request.form['texto']

        # Obtenha a instância OKR e atribua-a ao KR.
        okr = OKR.query.get(id_okr)
        if okr is None:
            return "OKR não encontrado", 404

        kr = KR(id_empresa=id_empresa, id_okr=id_okr, texto=texto, data_inclusao=datetime.utcnow())
        db.session.add(kr)
        db.session.commit()
        return redirect(url_for('listar_krs'))

    empresas = Empresa.query.all()
    return render_template('cadastrar_kr.html', empresas=empresas)




@app.route('/atualizar/kr/<int:id>', methods=['GET', 'POST'])
@login_required
def atualizar_kr(id):
    kr = KR.query.get(id)
    if request.method == 'POST':
        id_empresa = request.form['empresa']
        id_okr = request.form['okr']
        texto = request.form['texto']

        # Obtenha a instância OKR e atribua-a ao KR.
        okr = OKR.query.get(id_okr)
        kr.okr = okr
        kr.id_empresa = id_empresa  # Atualize o id da empresa
        kr.texto = texto
        db.session.commit()
        return redirect(url_for('listar_krs'))

    empresas = Empresa.query.all()
    okrs = OKR.query.filter_by(id_empresa=kr.id_empresa).all()

    return render_template('atualizar_kr.html', empresas=empresas, kr=kr, okrs=okrs)




@app.route('/update_kr/<int:krId>', methods=['POST'])
@login_required
def update_kr(krId):
    okrId = request.form['objetivo']  # assumindo que isso retorna um id de OKR
    kr = KR.query.get(krId)

    # Obtenha a instância OKR e atribua-a ao KR.
    okr = OKR.query.get(okrId)
    if okr is None:
        return "OKR não encontrado", 404
    kr.okr = okr

    db.session.commit()
    return 'OK', 200


@app.route('/get_krs/<int:objetivo_id>')
@login_required
def get_krs(objetivo_id):
    krs = KR.query.filter_by(id_okr=objetivo_id).all()
    return jsonify([{'id': kr.id, 'texto': kr.texto} for kr in krs])





@app.route('/get_krs_sprint/<int:empresa_id>')
@login_required
def get_krs_sprint(empresa_id):
    krs = KR.query.filter_by(id_empresa=empresa_id)
    return jsonify([kr.texto for kr in krs])


@app.route('/deletar/kr/<int:id>', methods=['POST'])
@login_required
def deletar_kr(id):
    kr = KR.query.get(id)
    db.session.delete(kr)
    db.session.commit()
    return redirect(url_for('listar_krs'))

#################################### OBJETIVOS #########################################



@app.route('/get_objectives/<int:empresa_id>', methods=['GET'])
@login_required
def get_objectives(empresa_id):
    okrs = OKR.query.filter_by(id_empresa=empresa_id).all()
    objectives = [{'id': okr.id, 'objetivo': okr.objetivo} for okr in okrs]
    return jsonify(objectives)


@app.route('/get_objetivos/<int:empresa_id>')
@login_required
def get_objetivos(empresa_id):
    objetivos = OKR.query.filter_by(id_empresa=empresa_id).all()
    return jsonify([{'id': objetivo.id, 'objetivo': objetivo.objetivo} for objetivo in objetivos])




#############################################################################


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


