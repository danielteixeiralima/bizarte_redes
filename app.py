from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Empresa, Resposta, Usuario, OKR, KR, PostsInstagram, AnaliseInstagram, analise_anuncios
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
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))


load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

url = os.getenv("DATABASE_URL")  # obtém a URL do banco de dados do ambiente
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)  # substitui o primeiro 'postgres://' por 'postgresql://'

app = Flask(__name__)
app.secret_key = 'Omega801'
app.config['SQLALCHEMY_DATABASE_URI'] = url or 'sqlite:///C:\\Users\\USER\\PycharmProjects\\bizarte\\test.db'
migrate = Migrate(app, db)
db.init_app(app)
app.jinja_env.globals.update(zip=zip)
app.jinja_env.globals.update(len=len)

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'danieltl@poli.ufrj.br'  # Substitua pelo seu email
app.config['MAIL_PASSWORD'] = '118167419'  # Substitua pela sua senha


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/empresas', methods=['GET'])
def listar_empresas():
    empresas = Empresa.query.all()
    return render_template('listar_empresas.html', empresas=empresas)

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
            vincular_instagram=request.form.get('vincular_instagram'),
            vincular_anuncio=request.form.get('vincular_anuncio')
        )
        db.session.add(empresa)
        db.session.commit()
        return redirect(url_for('listar_empresas'))
    return render_template('cadastrar_empresa.html')

@app.route('/cadastrar/post', methods=['POST'])
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
def api_posts():
    empresa_selecionada = request.args.get('empresa')
    if empresa_selecionada:
        posts = PostsInstagram.query.filter(PostsInstagram.nome_empresa == empresa_selecionada).order_by(desc(PostsInstagram.timestamp)).all()
    else:
        posts = PostsInstagram.query.order_by(desc(PostsInstagram.timestamp)).all()

    posts = [post.to_dict() for post in posts]  # Convert each post to a dictionary
    return jsonify(posts)

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

@app.route('/api/empresa/<int:id>/usuarios', methods=['GET'])
def get_users(id):
    users = Usuario.query.filter_by(id_empresa=id).all()
    return jsonify([user.to_dict() for user in users])

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
            'Authorization': 'Bearer EAAEKuYkpbtsBAD4zieqbSSw3JeyeFULHWlvHTzHuGoKAZBd0l120H0PAZAXF0rzXoGpyTXcrgwwLHsAzwr6qHtWypJ2lBI8zNqGbvVSVF0IcnpLS7cuCLFRwKGpgCDHZCQZAk6rjawKc5U4ZCaYYSebGBMe4j6JjtpPOjnikQ9oep9VhlMzhieXCjOKOzf2S2ddSEtiHEEAZDZD',
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

@app.route('/verificar_post_existente', methods=['POST'])
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
def listar_posts():
    empresas = Empresa.query.filter(Empresa.vincular_instagram.isnot(None)).all()
    posts = PostsInstagram.query.filter(PostsInstagram.timestamp.isnot(None)).all()
    return render_template('listar_posts.html', posts=posts, empresas=empresas)

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
        empresa.vincular_anuncio = request.form['vincular_anuncio']
        db.session.commit()
        return redirect(url_for('listar_empresas'))
    return render_template('atualizar_empresa.html', empresa=empresa)



@app.route('/deletar_empresa/<int:id>', methods=['POST'])
def deletar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    return redirect(url_for('listar_empresas'))

@app.route('/cadastrar/usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        usuario = Usuario(
            nome=request.form.get('nome'),
            sobrenome=request.form.get('sobrenome'),
            email=request.form.get('email'),
            celular=request.form.get('celular'),
            id_empresa=request.form.get('id_empresa'),
            cargo=request.form.get('cargo'),
            status=request.form.get('status')
        )
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('listar_usuarios'))
    empresas = Empresa.query.all()
    return render_template('cadastrar_usuario.html', empresas=empresas)


@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('listar_usuarios.html', usuarios=usuarios)

@app.route('/atualizar/usuario/<int:id>', methods=['GET', 'POST'])
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
def deletar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('listar_usuarios'))





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


@app.route('/analise_posts', methods=['GET', 'POST'])
def analise_posts():
    try:
        if request.method == 'POST':
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
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 201
        

    empresas = Empresa.query.filter(Empresa.vincular_instagram.isnot(None)).all()

    return render_template('analise_posts.html', empresas=empresas)

@app.route('/anuncios', methods=['GET', 'POST'])
def analise_anuncios():
    try:
        if request.method == 'POST':
            anuncios = analise_anuncios(
                id=request.form.get('id'),
                id_empresa=request.form.get('id_empresa'),
                valor=request.form.get('valor'),
                impressoes=request.form.get('impressoes'),
                landing=request.form.get('landing'),
                cpm=request.form.get('cpm'),
                ctr=request.form.get('ctr'),
                cpc=request.form.get('cpc')
            )
            db.session.add(anuncios)
            db.session.commit()
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 201
        

    empresaNomes = Empresa.query.filter(Empresa.vincular_anuncio.isnot(None)).all()

    return render_template('anuncios.html', empresas=empresaNomes)

@app.route('/googleAds', methods=['GET', 'POST'])
def analise_googleAds():
    try:
        if request.method == 'POST':
            anuncios = analise_anuncios(
                id=request.form.get('id'),
                id_empresa=request.form.get('id_empresa'),
                valor=request.form.get('valor'),
                impressoes=request.form.get('impressoes'),
                landing=request.form.get('landing'),
                cpm=request.form.get('cpm'),
                ctr=request.form.get('ctr'),
                cpc=request.form.get('cpc')
            )
            db.session.add(anuncios)
            db.session.commit()
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 201
        

    empresaNomes = Empresa.query.filter(Empresa.vincular_anuncio.isnot(None)).all()

    return render_template('anuncios.html', empresas=empresaNomes)


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
            return jsonify({'message': 'Análise salva com sucesso!'}), 200  # Adicione essa linha
            
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Falha ao salvar análise!'}), 500

   

def get_last_15_days_posts(empresa):
    # Substitua esta lógica pelo código necessário para obter os posts dos últimos 15 dias
    posts = PostsInstagram.query.filter(PostsInstagram.nome_empresa == empresa).order_by(PostsInstagram.timestamp.desc()).limit(12).all()

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

@app.route('/responder_pergunta/<int:id>', methods=['GET', 'POST'])
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
        "Authorization": "Bearer " + os.getenv("OPENAI_API_KEY")
    }

    # Adiciona a pergunta atual
    messages.append({"role": "user", "content": pergunta})

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
            if e.response.status_code in (429, 520, 502, 503):  # Limite de requisições atingido ou erro de servidor
                print(f"Erro {e.response.status_code} atingido. Aguardando antes de tentar novamente...")
                time.sleep(backoff_time)  # Aguarda antes de tentar novamente
                backoff_time *= 2  # Aumenta o tempo de espera
            else:
                raise



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


@app.route('/anuncios', methods=['GET', 'POST'])
def anuncios():
    return render_template('anuncios.html')  # Redireciona para a página de listagem de OKRs

@app.route('/visualizar_analises', methods=['GET'])
def visualizar_analises():
    nome_empresa = request.args.get('empresa')
    analise = analise_post_instagram(nome_empresa)
    return render_template('listar_analises.html', analise=analise)

@app.route('/cadastrar/okr', methods=['GET', 'POST'])
def cadastrar_okr():
    if request.method == 'POST':
        okr = OKR(
            id_empresa=request.form.get('empresa'),
            objetivo_1=request.form.get('objetivo_1'),
            objetivo_2=request.form.get('objetivo_2'),
            objetivo_3=request.form.get('objetivo_3'),
            objetivo_4=request.form.get('objetivo_4'),
            objetivo_5=request.form.get('objetivo_5'),
        )
        db.session.add(okr)
        db.session.commit()
        return redirect(url_for('listar_okrs'))  # Redireciona para a página de listagem de OKRs
    empresas = Empresa.query.all()
    return render_template('cadastrar_okr.html', empresas=empresas)

@app.route('/listar/okrs', methods=['GET'])
def listar_okrs():
    okrs = OKR.query.all()  # Substitua OKR pela classe do seu modelo de OKR
    return render_template('listar_okrs.html', okrs=okrs)


@app.route('/atualizar/okr/<int:id>', methods=['GET', 'POST'])
def atualizar_okr(id):
    okr = OKR.query.get(id)
    empresas = Empresa.query.all()
    if request.method == 'POST':
        okr.objetivo_1 = request.form['objetivo_1']
        okr.objetivo_2 = request.form['objetivo_2']
        okr.objetivo_3 = request.form['objetivo_3']
        okr.objetivo_4 = request.form['objetivo_4']
        okr.objetivo_5 = request.form['objetivo_5']
        db.session.commit()
        return redirect(url_for('listar_okrs'))
    return render_template('atualizar_okr.html', okr=okr, empresas=empresas)




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

    pergunta = f"Aqui estão todos os posts dos últimos 15 dias:{todos_posts_str}\nPreciso que você analise de acordo com o engajamento e Audiencia esses posts e me diga: 1 - os 3 posts com melhores resultados, a data e porquê 2 - os 3 posts com piores resultados, a data e porquê. 3 - insights do mês (o que temos que melhorar, o que fizemos bem)"
      
    #print(pergunta)

    resposta_gpt = perguntar_gpt(pergunta=pergunta, pergunta_id=1, messages=[])
        
    #print(resposta_gpt)

    return resposta_gpt

@app.route('/deletar/okr/<int:id>', methods=['POST'])
def deletar_okr(id):
    okr = OKR.query.get(id)
    db.session.delete(okr)
    db.session.commit()
    return redirect(url_for('listar_okrs'))



@app.route('/listar/krs', methods=['GET'])
def listar_krs():
    krs = KR.query.all()
    return render_template('listar_krs.html', krs=krs)

@app.route('/cadastrar/kr', methods=['GET', 'POST'])
def cadastrar_kr():
    if request.method == 'POST':
        id_empresa = request.form['empresa']
        id_objetivo = request.form['objetivo']  # Altere 'okr' para 'objetivo'
        texto = request.form['texto']
        kr = KR(id_empresa=id_empresa, id_objetivo=id_objetivo, texto=texto)
        db.session.add(kr)
        db.session.commit()
        return redirect(url_for('listar_krs'))
    empresas = Empresa.query.all()
    return render_template('cadastrar_kr.html', empresas=empresas)



@app.route('/atualizar/kr/<int:id>', methods=['GET', 'POST'])
def atualizar_kr(id):
    kr = KR.query.get(id)
    if request.method == 'POST':
        kr.id_okr = request.form['okr']
        kr.texto = request.form['texto']
        db.session.commit()
        return redirect(url_for('listar_krs'))
        pass
    else:
        empresas = Empresa.query.all()
        return render_template('cadastrar_kr.html', empresas=empresas)
@app.route('/deletar/kr/<int:id>', methods=['POST'])
def deletar_kr(id):
    kr = KR.query.get(id)
    db.session.delete(kr)
    db.session.commit()
    return redirect(url_for('listar_krs'))

@app.route('/get_objectives/<int:empresa_id>', methods=['GET'])
def get_objectives(empresa_id):
    okrs = OKR.query.filter_by(id_empresa=empresa_id).all()
    objectives = []
    for okr in okrs:
        for i in range(1, 6):
            objetivo = getattr(okr, f'objetivo_{i}')
            if objetivo:
                objectives.append({'id': okr.id, 'objetivo': objetivo})
    return jsonify(objectives)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

