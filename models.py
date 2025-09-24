from datetime import datetime
from manage import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Company(db.Model):
    __tablename__ = "company"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    users = db.relationship('User', backref='company', lazy='dynamic')

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, index=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(200))
    role = db.Column(db.String(30), default="cliente", nullable=False)
    # padronizados: "admin", "funcionarios", "cliente_adm", "cliente"

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"

    def is_funcionario(self):
        return self.role == "funcionarios"

    def is_cliente_adm(self):
        return self.role == "cliente_adm"

    def is_cliente(self):
        return self.role == "cliente"

    def company_name(self):
        return self.company.name if self.company else None

class Contato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    empresa = db.Column(db.String(120))
    mensagem = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    resumo = db.Column(db.String(300))
    conteudo = db.Column(db.Text, nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    autor = db.relationship('User', backref='posts')

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Aberto")
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    usuario = db.relationship('User', backref='tickets')

class Mensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    usuario = db.relationship('User', backref='mensagens')
    ticket = db.relationship('Ticket', backref='mensagens')

class Log(db.Model):
    __tablename__ = "log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45))
    status = db.Column(db.String(20), default="ok")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='logs')

class Goal(db.Model):
    __tablename__ = "goal"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # estrategica, taticas, operacionais
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    company = db.relationship('Company', backref='goals')

class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    
    responsavel_id = db.Column(db.Integer, db.ForeignKey('collaborator.id'), nullable=True)
    setor_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=True)
    cor = db.Column(db.String(7), default='#3b82f6')  # Cor do evento em HEX
    tipo = db.Column(db.String(50), default='evento')  # evento, reuniao, tarefa, etc.
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    company = db.relationship('Company', backref='events')
    responsavel = db.relationship('Collaborator', backref='events')
    setor = db.relationship('Sector', backref='events')

class Demand(db.Model):
    __tablename__ = "demand"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # colaborador responsável
    status = db.Column(db.String(30), default='open')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    company = db.relationship('Company', backref='demands')
    owner = db.relationship('User', backref='owned_demands')

class Collaborator(db.Model):
    __tablename__ = "collaborator"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # opcionalmente vinculado a um user
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    role = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    company = db.relationship('Company', backref='collaborators')
    user = db.relationship('User', backref='collab_profile', uselist=False)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=True)

class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    personal_demands = db.relationship("PersonalDemand", backref="organization", lazy=True)

class PersonalDemand(db.Model):
    __tablename__ = "personal_demands"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="Pendente")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)

class Leisure(db.Model):
    __tablename__ = "leisure"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Objective(db.Model):
    __tablename__ = "objective"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # estrategica, taticas, operacionais
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    company = db.relationship('Company', backref='objectives')


class Plan(db.Model):
    __tablename__ = "plan"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # estrategica, taticas, operacionais
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    who = db.Column(db.String(200), nullable=False)
    when = db.Column(db.String(100), nullable=False)  # pode ser DateTime se preferir
    where = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    company = db.relationship('Company', backref='plans')

class Sector(db.Model):
    __tablename__ = "sector"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    company = db.relationship('Company', backref='sectors')
    collaborators = db.relationship('Collaborator', backref='sector', lazy=True)

class DemandKanban(db.Model):
    __tablename__ = "demand_kanban"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Nome do quadro (ex: "Projetos 2024")
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    company = db.relationship('Company', backref='kanban_boards')
    columns = db.relationship('KanbanColumn', backref='kanban', lazy=True, cascade='all, delete-orphan')

class KanbanColumn(db.Model):
    __tablename__ = "kanban_column"
    id = db.Column(db.Integer, primary_key=True)
    kanban_id = db.Column(db.Integer, db.ForeignKey('demand_kanban.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Ex: "To Do", "Doing", "Done"
    position = db.Column(db.Integer, nullable=False)  # Ordem das colunas
    color = db.Column(db.String(7), default="#6b7280")  # Cor em hex
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    cards = db.relationship('KanbanCard', backref='column', lazy=True, cascade='all, delete-orphan')

class KanbanCard(db.Model):
    __tablename__ = "kanban_card"
    id = db.Column(db.Integer, primary_key=True)
    column_id = db.Column(db.Integer, db.ForeignKey('kanban_column.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Critérios GUT
    gravidade = db.Column(db.Integer, default=1)  # 1-5
    urgencia = db.Column(db.Integer, default=1)   # 1-5
    tendencia = db.Column(db.Integer, default=1)  # 1-5
    
    # Informações da demanda
    o_que_fazer = db.Column(db.Text, nullable=False)
    onde_fazer = db.Column(db.String(200))
    quem_fazer_id = db.Column(db.Integer, db.ForeignKey('collaborator.id'), nullable=True)
    setor_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=True)
    prazo = db.Column(db.DateTime, nullable=True)
    
    # Metadados
    position = db.Column(db.Integer, default=0)  # Ordem dentro da coluna
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relacionamentos
    responsavel = db.relationship('Collaborator', backref='cards')
    setor = db.relationship('Sector', backref='cards')
    criador = db.relationship('User', backref='created_cards')
