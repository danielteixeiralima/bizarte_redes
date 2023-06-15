from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


db = SQLAlchemy()

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_contato = db.Column(db.String(80))
    email_contato = db.Column(db.String(120))
    telefone_contato = db.Column(db.String(20))
    endereco_empresa = db.Column(db.String(200))
    setor_atuacao = db.Column(db.String(200))
    tamanho_empresa = db.Column(db.String(200))
    descricao_empresa = db.Column(db.Text)
    objetivos_principais = db.Column(db.Text)
    historico_interacoes = db.Column(db.Text)
    vincular_instagram = db.Column(db.String(200))





class PostInstagram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.String(64), index=True)
    timestamp = db.Column(db.String(64))
    caption = db.Column(db.String(64))
    like_count = db.Column(db.Integer)
    comments_count = db.Column(db.Integer)
    reach = db.Column(db.Integer)
    percentage = db.Column(db.Float)
    media_product_type = db.Column(db.String(64))
    plays = db.Column(db.Integer)
    saved = db.Column(db.Integer)
    nome_empresa = db.Column(db.String(64))

    def to_dicts(self):
        return {
            'id': self.id,  # incluir o id no dicionário
            'id_empresa': self.id_empresa,
            'timestamp': self.timestamp,
            'caption': self.caption,
            'like_count': self.like_count,
            'comments_count': self.comments_count,
            'reach': self.reach,
            'percentage': self.percentage,
            'media_product_type': self.media_product_type,
            'plays': self.plays,
            'saved': self.saved,
            'nome_empresa': self.nome_empresa,
        }
    
class PostsInstagram(db.Model):
    id = db.Column(db.String, primary_key=True)
    id_empresa = db.Column(db.String(64), index=True)
    timestamp = db.Column(db.String(64))
    caption = db.Column(db.String(64))
    like_count = db.Column(db.Integer)
    comments_count = db.Column(db.Integer)  
    reach = db.Column(db.Integer)
    percentage = db.Column(db.Float)
    media_product_type = db.Column(db.String(64))
    plays = db.Column(db.Integer)
    saved = db.Column(db.Integer)
    nome_empresa = db.Column(db.String(64))

    def to_dict(self):
        return {
            'id': self.id,  # incluir o id no dicionário
            'id_empresa': self.id_empresa,
            'timestamp': self.timestamp,
            'caption': self.caption,
            'like_count': self.like_count,
            'comments_count': self.comments_count,
            'reach': self.reach,
            'percentage': self.percentage,
            'media_product_type': self.media_product_type,
            'plays': self.plays,
            'saved': self.saved,
            'nome_empresa': self.nome_empresa,
        }

class AnaliseInstagram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_criacao = db.Column(db.String(64))
    analise = db.Column(db.Text)
    nome_empresa = db.Column(db.String(64))

    def to_dict(self):
        return {
            'id': self.id,
            'data_criacao': self.data_criacao,
            'analise': self.analise,
            'nome_empresa': self.nome_empresa,
        }
    





class Resposta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    pergunta = db.Column(db.Text, nullable=False)
    resposta = db.Column(db.Text)
    classificacao = db.Column(db.String(200))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, onupdate=datetime.utcnow)


class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    sobrenome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    celular = db.Column(db.String(20), nullable=False)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='usuarios')
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    cargo = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    sprint = db.Column(db.String(200))
    dayling_1 = db.Column(db.String(200))
    dayling_2 = db.Column(db.String(200))
    dayling_3 = db.Column(db.String(200))
    dayling_4 = db.Column(db.String(200))
    dayling_5 = db.Column(db.String(200))
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'sobrenome': self.sobrenome,
            'email': self.email,
        }
    @property
    def password(self):
        raise AttributeError('password: campo de leitura apenas')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

class OKR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='okrs')
    objetivo = db.Column(db.String(200))
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)




class KR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    id_okr = db.Column(db.Integer, db.ForeignKey('okr.id'), nullable=False)
    texto = db.Column(db.String(200))
    data_inclusao = db.Column(db.DateTime, default=datetime.utcnow)
    okr = db.relationship('OKR', backref='krs')




class MacroAcao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(500), nullable=False)
    aprovada = db.Column(db.Boolean, default=False)
    data_inclusao = db.Column(db.DateTime, default=datetime.utcnow)
    kr_id = db.Column(db.Integer, db.ForeignKey('kr.id'), nullable=False)
    objetivo = db.Column(db.String(500), nullable=False)
    objetivo_id = db.Column(db.Integer, nullable=False)
    empresa = db.Column(db.String(500), nullable=False)
    empresa_id = db.Column(db.Integer, nullable=False)
    kr = db.relationship('KR', backref='macro_acoes')



class Sprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nome_empresa = db.Column(db.String(120), nullable=False)
    prioridade = db.Column(db.Integer, nullable=False)
    tarefa = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    usuario = db.relationship('Usuario', backref='sprints')
    usuario_grupo = db.Column(db.String(120), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)


class TarefaSemanal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='tarefas_semanais')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('Usuario', backref='tarefas_semanais')
    tarefa_semana = db.Column(db.String(500), nullable=False)
    to_do = db.Column(db.String(10000), nullable=True)
    observacoes = db.Column(db.String(10000), nullable=True)
    data_para_conclusao = db.Column(db.DateTime, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @property
    def to_do_decoded(self):
        return json.loads(self.to_do)

    def observacoes_decoded(self):
        return json.loads(self.observacoes)



