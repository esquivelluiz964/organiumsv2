from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Contato, BlogPost, Ticket, Mensagem, Log, Company, Goal, Event, Demand, Collaborator, PersonalDemand, Organization, Leisure, Plan, Objective, Sector, DemandKanban, KanbanCard, KanbanColumn, Event
from manage import db, login
import os
from werkzeug.utils import secure_filename
from app.utils import register_log
import string
import secrets
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'app/static/uploads/avatars'

bp = Blueprint('app_bp', __name__, template_folder='templates', static_folder='static')

# funções globais
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_random_password(length=12):
    """Gera uma senha aleatória"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for i in range(length))

def create_user_from_collaborator(collaborator):
    """Cria um usuário a partir de um colaborador"""
    # Verifica se já existe um usuário com este email
    existing_user = User.query.filter_by(email=collaborator.email).first()
    if existing_user:
        return existing_user, False  # Já existe, não criou novo
    
    # Gera username a partir do email ou nome
    base_username = collaborator.email.split('@')[0] if collaborator.email else collaborator.name.lower().replace(' ', '')
    username = base_username
    counter = 1
    
    # Garante que o username seja único
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Gera senha aleatória
    password = generate_random_password()
    
    # Cria o usuário
    user = User(
        username=username,
        name=collaborator.name,
        email=collaborator.email,
        role='cliente',  # Role padrão para colaboradores
        company_id=collaborator.company_id
    )
    user.set_password(password)
    
    db.session.add(user)
    return user, True  # Novo usuário criado

def sync_collaborator_to_user(collaborator):
    """Sincroniza os dados do colaborador para o usuário correspondente"""
    user = User.query.filter_by(email=collaborator.email).first()
    
    if user:
        # Atualiza os dados do usuário existente
        user.name = collaborator.name
        user.company_id = collaborator.company_id
        # Mantém o role do usuário, não sobrescreve
        return user, False  # Usuário atualizado, não criado
    else:
        # Cria novo usuário
        return create_user_from_collaborator(collaborator)

# rotas públicas

# home principal
@bp.route('/')
def home():
    register_log("Acesso à página inicial")
    return render_template('public/home.html')

# página de sobre
@bp.route('/sobre')
def about():
    register_log("Acesso à página sobre")
    return render_template('public/sobre.html')

# página institucional para comunicação com empresas
@bp.route('/empresas')
def empresas():
    register_log("Acesso à página empresas")
    return render_template('public/empresas.html')

# página para detalhar os planos
@bp.route('/planos')
def planos():
    register_log("Acesso à página planos")
    return render_template('public/planos.html')

# formulário de contato
@bp.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        nome = request.form.get('name')
        email = request.form.get('email')
        empresa = request.form.get('empresa')
        mensagem = request.form.get('mensagem')

        if not nome or not email or not mensagem:
            flash("Por favor, preencha os campos obrigatórios.", "danger")
            register_log("Envio de mensagem via formulário de contato: falha, detatlhes incompletos", status="fail")
            return redirect(url_for('app_bp.contato'))

        # Salvar no banco de dados
        contato_msg = Contato(nome=nome, email=email, empresa=empresa, mensagem=mensagem)
        db.session.add(contato_msg)
        db.session.commit()

        register_log("Envio de mensagem via formulário de contato: sucesso")

        flash("Mensagem enviada com sucesso! Entraremos em contato em breve.", "success")
        return redirect(url_for('app_bp.contato'))
    else:
        register_log("Acesso à página de contato")

    return render_template('public/contato.html')

# página de perguntas e respostas
@bp.route('/faq')
def faq():
    register_log("Acesso à página FAQ")
    return render_template('public/faq.html')

# página para abertura de chamados
@bp.route('/ajuda', methods=['GET', 'POST'])
def ajuda():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        nome = request.form.get('nome')

        if not titulo or not descricao or not nome:
            register_log("Envio de mensagem via formulário de ajuda: falha, detalhes incompletos", status="fail")
            flash('Por favor, preencha todos os campos.', 'danger')
            return redirect(url_for('app_bp.ajuda'))

        ticket = Ticket(titulo=titulo, descricao=descricao)
        db.session.add(ticket)
        db.session.commit()

        # cria a primeira mensagem usando a descrição
        primeira_msg = Mensagem(
            conteudo=descricao,
            ticket=ticket,
            usuario=current_user if current_user.is_authenticated else None
        )
        # salva nome manualmente em anônimo
        if not primeira_msg.usuario:
            primeira_msg.conteudo = f"[{nome}] {descricao}"

        db.session.add(primeira_msg)
        db.session.commit()
        register_log("Envio de mensagem via formulário de ajuda: sucesso")

        flash('Chamado aberto com sucesso! Agora você pode conversar com o suporte.', 'success')
        return redirect(url_for('app_bp.ajuda_ticket', ticket_id=ticket.id))

    return render_template('public/ajuda.html')

@bp.route('/ajuda/<int:ticket_id>', methods=['GET', 'POST'])
def ajuda_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if request.method == 'POST':
        conteudo = request.form.get('conteudo')
        nome = request.form.get('nome') if not current_user.is_authenticated else None

        if conteudo:
            msg = Mensagem(
                conteudo=f"[{nome}] {conteudo}" if nome else conteudo,
                ticket=ticket,
                usuario=current_user if current_user.is_authenticated else None
            )
            db.session.add(msg)
            db.session.commit()
            flash('Mensagem enviada!', 'success')
        else:
            register_log("Envio de mensagem via ticket de ajuda: falha, detalhes incompletos", status="fail")
        return redirect(url_for('app_bp.ajuda_ticket', ticket_id=ticket.id))
    else:
        register_log("Acesso à página de ticket de ajuda")

    return render_template('public/ajuda_ticket.html', ticket=ticket)

# página do blog público da plataforma
@bp.route('/blog')
def blog():
    register_log("Acesso à página do blog")
    posts = BlogPost.query.order_by(BlogPost.criado_em.desc()).all()
    return render_template('public/blog.html', posts=posts)

@bp.route('/blog/<slug>')
def blog_post(slug):
    register_log(f"Acesso à página do post do blog: {slug}")
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    return render_template('public/blog_post.html', post=post)

# páinel de privacidade
@bp.route('/privacidade')
def privacidade():
    register_log("Acesso à página de privacidade")
    return render_template('public/privacidade.html')

# autenticações
@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login').strip()
        pwd = request.form.get('password')

        # Buscar pelo username ou email
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()

        if user and user.check_password(pwd):
            login_user(user)
            register_log("Login de usuário")
            return redirect(url_for('app_bp.dashboard'))

        flash('Credenciais inválidas', 'danger')
        register_log("Tentativa de login falhou", status="fail")
        return redirect(url_for('app_bp.login'))

    return render_template('auth/login.html')

@bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        name = request.form.get('name').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        company_name = (request.form.get('company') or "").strip()
        avatar_file = request.files.get('avatar')

        if User.query.filter_by(email=email).first():
            register_log("Tentativa de registro falhou: email já cadastrado", status="fail")
            flash('Email já cadastrado', 'warning')
            return redirect(url_for('app_bp.register'))

        if User.query.filter_by(username=username).first():
            register_log("Tentativa de registro falhou: username já existe", status="fail")
            flash('Username já existe', 'warning')
            return redirect(url_for('app_bp.register'))

        avatar_path = None
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(f"{username}_{avatar_file.filename}")
            avatar_file.save(os.path.join(UPLOAD_FOLDER, filename))
            avatar_path = f'/static/uploads/avatars/{filename}'

        # find or create company
        company = None
        if company_name:
            company = Company.query.filter_by(name=company_name).first()
            if not company:
                company = Company(name=company_name)
                db.session.add(company)
                db.session.flush()  # garante company.id sem commit

        user = User(username=username, name=name, email=email, avatar=avatar_path, role="cliente", company=company)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        register_log("Registro de novo usuário")
        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('app_bp.login'))

    return render_template('auth/register.html')

# rotas privadas

# dashboard público principal
@bp.route('/dashboard')
@login_required
def dashboard():
    register_log("Acesso à página do dashboard")
    return render_template('private/home.html')

# verificar e mudar o perfil na plataforma
@bp.route('/perfil')
@login_required
def profile():
    register_log("Acesso à página de perfil")
    return render_template('private/profile.html')

@bp.route('/configuracoes', methods=['GET','POST'])
@login_required
def settings():

    current_app = UPLOAD_FOLDER

    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.name = request.form.get('name')
        current_user.email = request.form.get('email')

        # Avatar upload
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename != '':
            filename = secure_filename(avatar_file.filename)
            avatar_path = f"{filename}"
            avatar_file.save(os.path.join(current_app, avatar_path))
            current_user.avatar = avatar_path

        # Alterar senha se preenchida
        new_password = request.form.get('password')
        if new_password:
            current_user.set_password(new_password)

        db.session.commit()
        flash("Configurações atualizadas com sucesso!", "success")
        register_log("Atualização de configurações de usuário")
        return redirect(url_for('app_bp.profile'))

    register_log("Acesso à página de configurações")

    return render_template('private/settings.html')

# deslogar
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    register_log("Logout de usuário")
    return redirect(url_for('app_bp.home'))

# administrar o blog
@bp.route('/admin/blog')
@login_required
def admin_blog():
    if not current_user.is_admin() and not current_user.is_funcionario():
        abort(403)
    register_log("Acesso à página do blog")
    posts = BlogPost.query.order_by(BlogPost.criado_em.desc()).all()
    return render_template('admin/blog_list.html', posts=posts)

@bp.route('/admin/blog/novo', methods=['GET','POST'])
@login_required
def admin_blog_novo():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        slug = request.form.get('slug')
        resumo = request.form.get('resumo')
        conteudo = request.form.get('conteudo')

        if BlogPost.query.filter_by(slug=slug).first():
            flash('O tema do blog já existe', 'danger')
            register_log("Tentativa de criação de post falhou: slug já existe", status="fail")
            return redirect(url_for('app_bp.admin_blog_novo'))

        post = BlogPost(titulo=titulo, slug=slug, resumo=resumo, conteudo=conteudo, autor=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post criado com sucesso!', 'success')
        register_log("Criação de novo post no blog")
        return redirect(url_for('app_bp.admin_blog'))

    return render_template('admin/blog_form.html')

# administrar os chamados
@bp.route('/admin/ajuda')
@login_required
def admin_ajuda():
    if not current_user.is_admin() and not current_user.is_funcionario():
        abort(403)
    register_log("Acesso à página de ajuda/admin")
    tickets = Ticket.query.order_by(Ticket.criado_em.desc()).all()
    return render_template('admin/ajuda_list.html', tickets=tickets)

@bp.route('/admin/ajuda/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def admin_ajuda_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    register_log(f"Acesso à página de detalhes do ticket: {ticket.id}")

    if request.method == 'POST':
        novo_status = request.form.get('status')
        ticket.status = novo_status
        db.session.commit()
        flash('Status do ticket atualizado.', 'success')
        return redirect(url_for('app_bp.admin_ajuda_ticket', ticket_id=ticket.id))

    register_log(f"Atualização de status do ticket: {ticket.id}")

    return render_template('admin/ajuda_ticket.html', ticket=ticket)

# administrar os contatos recebidos
@bp.route('/admin/contatos')
@login_required
def admin_contatos():
    if not current_user.is_admin():
        abort(403)

    contatos = Contato.query.order_by(Contato.criado_em.desc()).all()
    register_log("Acesso à página de contatos/admin")
    return render_template('admin/contatos.html', contatos=contatos)

# administrar usuários da plataforma
@bp.route('/admin/usuarios')
@login_required
def admin_usuarios():
    if not current_user.is_admin():
        abort(403)

    usuarios = User.query.order_by(User.id.desc()).all()
    register_log("Acesso à gestão de usuários")
    return render_template('admin/usuarios_list.html', usuarios=usuarios)

@bp.route('/admin/usuarios/novo', methods=['GET','POST'])
@login_required
def admin_usuario_novo():
    if not current_user.is_admin():
        abort(403)

    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'cliente')
        company_name = (request.form.get('company') or "").strip()

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'danger')
            return redirect(url_for('app_bp.admin_usuario_novo'))

        company = None
        if company_name:
            company = Company.query.filter_by(name=company_name).first()
            if not company:
                company = Company(name=company_name)
                db.session.add(company)
                db.session.flush()

        user = User(username=username, name=name, email=email, role=role, company=company)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        register_log(f"Usuário criado: {username}")
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('app_bp.admin_usuarios'))

    # para o form, podemos passar lista de empresas existentes
    companies = Company.query.order_by(Company.name).all()
    return render_template('admin/usuario_form.html', companies=companies)

@bp.route('/admin/usuarios/<int:user_id>/editar', methods=['GET','POST'])
@login_required
def admin_usuario_editar(user_id):
    if not current_user.is_admin():
        abort(403)

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.role = request.form.get('role')

        company_name = (request.form.get('company') or "").strip()
        if company_name:
            company = Company.query.filter_by(name=company_name).first()
            if not company:
                company = Company(name=company_name)
                db.session.add(company)
                db.session.flush()
            user.company = company
        else:
            user.company = None

        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        register_log(f"Usuário editado: {user.username}")
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('app_bp.admin_usuarios'))

    companies = Company.query.order_by(Company.name).all()
    return render_template('admin/usuario_form.html', user=user, companies=companies)

@bp.route('/admin/usuarios/<int:user_id>/excluir', methods=['POST'])
@login_required
def admin_usuario_excluir(user_id):
    if not current_user.is_admin():
        abort(403)

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    register_log(f"Usuário excluído: {user.username}")
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('app_bp.admin_usuarios'))

# auditar os log da plataforma
@bp.route('/admin/logs')
@login_required
def admin_logs():
    if not current_user.is_admin():
        abort(403)
    logs = Log.query.order_by(Log.created_at.desc()).limit(500).all()  # últimos 500
    register_log("Acesso à página de auditoria/logs")
    return render_template('admin/logs.html', logs=logs)

# metas institucionais
@bp.route('/client/goals')
@login_required
def client_goals():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)

    goals = Goal.query.filter_by(company_id=current_user.company_id).order_by(Goal.created_at.desc()).all()
    objectives = Objective.query.filter_by(company_id=current_user.company_id).all()
    plans = Plan.query.filter_by(company_id=current_user.company_id).all()

    register_log("Acesso: cliente_adm - metas")
    return render_template('client/goals_crud.html', goals=goals, objectives=objectives, plans=plans)

@bp.route('/client/goals/new', methods=['POST'])
@login_required
def client_goal_new():
    title = request.form.get('title')
    level = request.form.get('level')
    description = request.form.get('description')

    goal = Goal(company_id=current_user.company_id, title=title, level=level, description=description)
    db.session.add(goal)
    db.session.commit()
    return redirect(url_for('app_bp.client_goals'))

@bp.route('/client/goals/<int:id>/edit', methods=['POST'])
@login_required
def client_goal_edit(id):
    goal = Goal.query.get_or_404(id)
    if goal.company_id != current_user.company_id:
        abort(403)

    goal.title = request.form.get('title')
    goal.level = request.form.get('level')
    goal.description = request.form.get('description')
    db.session.commit()
    return redirect(url_for('app_bp.client_goals'))

@bp.route('/client/goals/<int:id>/delete', methods=['POST', 'GET'])
@login_required
def client_goal_delete(id):
    goal = Goal.query.get_or_404(id)
    if goal.company_id != current_user.company_id:
        abort(403)

    db.session.delete(goal)
    db.session.commit()
    return redirect(url_for('app_bp.client_goals'))

# página de colaboradores
@bp.route('/client/sectors')
@login_required
def client_sectors():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    sectors = Sector.query.filter_by(company_id=current_user.company_id).all()
    return render_template('client/sectors_list.html', sectors=sectors)

@bp.route('/client/sectors/new', methods=['POST'])
@login_required
def new_sector():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    name = request.form.get('title')
    description = request.form.get('description')
    sector = Sector(company_id=current_user.company_id, name=name, description=description)
    db.session.add(sector)
    db.session.commit()
    return redirect(url_for('app_bp.client_sectors'))

@bp.route('/client/sectors/<int:sector_id>/edit', methods=['POST'])
@login_required
def edit_sector(sector_id):
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    sector = Sector.query.get_or_404(sector_id)
    if sector.company_id != current_user.company_id:
        abort(403)
    sector.name = request.form.get('title')
    sector.description = request.form.get('description')
    db.session.commit()
    return redirect(url_for('app_bp.client_sectors'))

@bp.route('/client/sectors/<int:sector_id>/delete', methods=['POST'])
@login_required
def delete_sector(sector_id):
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    sector = Sector.query.get_or_404(sector_id)
    if sector.company_id != current_user.company_id:
        abort(403)
    db.session.delete(sector)
    db.session.commit()
    return redirect(url_for('app_bp.client_sectors'))

@bp.route('/client/collaborators')
@login_required
def client_collaborators():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    collaborators = Collaborator.query.filter_by(company_id=current_user.company_id).order_by(Collaborator.created_at.desc()).all()
    sectors = Sector.query.filter_by(company_id=current_user.company_id).order_by(Sector.name).all()
    sectors_data = [{"id": s.id, "name": s.name} for s in sectors]
    register_log("Acesso: cliente_adm - collaborators")
    return render_template('client/collaborators_list.html', collaborators=collaborators, sectors=sectors_data)

@bp.route('/client/collaborators/new', methods=['POST'])
@login_required
def new_collaborator():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    
    collab = Collaborator(
        company_id=current_user.company_id,
        name=request.form.get('title'),
        email=request.form.get('description'),
        role=request.form.get('role'),
        sector_id=request.form.get('sector_id') or None
    )
    
    db.session.add(collab)
    db.session.flush()  # Usa flush para obter o ID sem commit
    
    # Cria o usuário correspondente
    user, is_new_user = sync_collaborator_to_user(collab)
    
    db.session.commit()
    
    if is_new_user:
        flash(f'Colaborador e usuário criados com sucesso!', 'success')
        register_log(f"Colaborador e usuário criados: {collab.name}")
    else:
        flash(f'Colaborador criado e usuário sincronizado com sucesso!', 'success')
        register_log(f"Colaborador criado e usuário sincronizado: {collab.name}")
    
    return redirect(url_for('app_bp.client_collaborators'))

@bp.route('/client/collaborators/<int:collab_id>/edit', methods=['POST'])
@login_required
def edit_collaborator(collab_id):
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    
    collab = Collaborator.query.get_or_404(collab_id)
    if collab.company_id != current_user.company_id:
        abort(403)
    
    # Salva o email antigo para verificar se mudou
    old_email = collab.email
    
    collab.name = request.form.get('title')
    collab.email = request.form.get('description')
    collab.role = request.form.get('role')
    collab.sector_id = request.form.get('sector_id') or None
    
    # Sincroniza com o usuário
    user, is_new_user = sync_collaborator_to_user(collab)
    
    db.session.commit()
    
    if old_email != collab.email:
        flash('Colaborador atualizado e email do usuário modificado!', 'warning')
    else:
        flash('Colaborador atualizado com sucesso!', 'success')
    
    register_log(f"Colaborador editado: {collab.name}")
    return redirect(url_for('app_bp.client_collaborators'))

@bp.route('/client/collaborators/<int:collab_id>/delete', methods=['POST'])
@login_required
def delete_collaborator(collab_id):
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    
    collab = Collaborator.query.get_or_404(collab_id)
    if collab.company_id != current_user.company_id:
        abort(403)
    
    collab_name = collab.name
    collab_email = collab.email
    
    # Encontra o usuário correspondente
    user = User.query.filter_by(email=collab_email, company_id=current_user.company_id).first()
    
    # Remove o colaborador
    db.session.delete(collab)
    
    # Remove o usuário se existir e pertencer à mesma empresa
    if user:
        db.session.delete(user)
        flash('Colaborador e usuário excluídos com sucesso!', 'success')
        register_log(f"Colaborador e usuário excluídos: {collab_name}")
    else:
        flash('Colaborador excluído com sucesso!', 'success')
        register_log(f"Colaborador excluído: {collab_name}")
    
    db.session.commit()
    return redirect(url_for('app_bp.client_collaborators'))

# página de demandas
@bp.route('/client/kanban')
@login_required
def client_demands():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    
    # Buscar quadros kanban da empresa
    kanban_boards = DemandKanban.query.filter_by(company_id=current_user.company_id).all()
    collaborators = Collaborator.query.filter_by(company_id=current_user.company_id).all()
    sectors = Sector.query.filter_by(company_id=current_user.company_id).all()

    # Transformação para front
    collaborators_data = [
        {"id": c.id, "name": c.name} for c in collaborators
    ]
    sectors_data = [
        {"id": s.id, "name": s.name} for s in sectors
    ]

    register_log("Acesso: cliente_adm - kanban")
    return render_template('client/kanban.html', 
                         kanban_boards=kanban_boards,
                         collaborators=collaborators_data,
                         sectors=sectors_data)

@bp.route('/client/kanban/<int:kanban_id>/data')
@login_required
def get_kanban_data(kanban_id):
    kanban = DemandKanban.query.filter_by(id=kanban_id, company_id=current_user.company_id).first_or_404()
    
    data = {
        'id': kanban.id,
        'name': kanban.name,
        'columns': []
    }
    
    for column in sorted(kanban.columns, key=lambda c: c.position):
        column_data = {
            'id': column.id,
            'name': {'Backlog':'Pendências','To Do':'A Fazer','Doing':'Fazendo','Done':'Concluído'}.get(column.name, column.name),
            'color': column.color,
            'position': column.position,
            'cards': []
        }
        
        # Ordena os cards
        for card in sorted(column.cards, key=lambda c: c.position):
            card_data = {
                'id': card.id,
                'title': card.title,
                'description': card.description,
                'o_que_fazer': card.o_que_fazer,
                'onde_fazer': card.onde_fazer,
                'prazo': card.prazo.isoformat() if card.prazo else None,
                'gravidade': card.gravidade,
                'urgencia': card.urgencia,
                'tendencia': card.tendencia,
                'position': card.position,
                'responsavel': {
                    'id': card.quem_fazer_id,
                    'name': card.responsavel.name if card.responsavel else None
                } if card.quem_fazer_id else None,
                'setor': {
                    'id': card.setor_id,
                    'name': card.setor.name if card.setor else None
                } if card.setor_id else None,
                'criador': card.criador.name,
                'created_at': card.created_at.isoformat()
            }
            column_data['cards'].append(card_data)
        
        data['columns'].append(column_data)
    
    return jsonify(data)

@bp.route('/client/kanban/new', methods=['POST'])
@login_required
def create_kanban():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('Nome do quadro é obrigatório', 'danger')
        return redirect(url_for('app_bp.client_demands'))
    
    kanban = DemandKanban(
        name=name,
        description=description,
        company_id=current_user.company_id
    )
    
    # Criar colunas padrão
    default_columns = [
        {'name': 'Backlog', 'position': 0, 'color': '#6b7280'},
        {'name': 'To Do', 'position': 1, 'color': '#3b82f6'},
        {'name': 'Doing', 'position': 2, 'color': '#f59e0b'},
        {'name': 'Done', 'position': 3, 'color': '#10b981'}
    ]
    
    for col_data in default_columns:
        column = KanbanColumn(
            name=col_data['name'],
            position=col_data['position'],
            color=col_data['color']
        )
        kanban.columns.append(column)
    
    db.session.add(kanban)
    db.session.commit()
    
    flash('Quadro criado com sucesso!', 'success')
    register_log(f"Criou quadro kanban: {name}")
    return redirect(url_for('app_bp.client_demands'))

@bp.route('/client/kanban/<int:kanban_id>/delete', methods=['POST'])
@login_required
def delete_kanban(kanban_id):
    kanban = DemandKanban.query.filter_by(id=kanban_id, company_id=current_user.company_id).first_or_404()
    
    db.session.delete(kanban)
    db.session.commit()
    
    flash('Quadro deletado com sucesso!', 'success')
    register_log(f"Deletou quadro kanban: {kanban.name}")
    return redirect(url_for('app_bp.client_demands'))

@bp.route('/client/kanban/card/new', methods=['POST'])
@login_required
def create_kanban_card():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    
    column_id = request.form.get('column_id')
    title = request.form.get('title')
    o_que_fazer = request.form.get('o_que_fazer')
    
    if not all([column_id, title, o_que_fazer]):
        flash('Título e descrição são obrigatórios', 'danger')
        return redirect(url_for('app_bp.client_demands'))
    
    column = KanbanColumn.query.filter_by(id=column_id).first_or_404()
    
    # Verificar se o quadro pertence à empresa do usuário
    if column.kanban.company_id != current_user.company_id:
        abort(403)
    
    card = KanbanCard(
        column_id=column_id,
        title=title,
        description=request.form.get('description'),
        o_que_fazer=o_que_fazer,
        onde_fazer=request.form.get('onde_fazer'),
        quem_fazer_id=request.form.get('quem_fazer_id') or None,
        setor_id=request.form.get('setor_id') or None,
        gravidade=int(request.form.get('gravidade', 1)),
        urgencia=int(request.form.get('urgencia', 1)),
        tendencia=int(request.form.get('tendencia', 1)),
        created_by=current_user.id
    )
    
    # Prazo
    prazo_str = request.form.get('prazo')
    if prazo_str:
        try:
            card.prazo = datetime.fromisoformat(prazo_str)
        except ValueError:
            card.prazo = datetime.strptime(prazo_str, '%Y-%m-%d')
    
    # Posição (última da coluna)
    last_card = KanbanCard.query.filter_by(column_id=column_id).order_by(KanbanCard.position.desc()).first()
    card.position = last_card.position + 1 if last_card else 0
    
    db.session.add(card)
    db.session.commit()
    
    flash('Card criado com sucesso!', 'success')
    register_log(f"Criou card: {title}")
    return redirect(url_for('app_bp.client_demands'))

@bp.route('/client/kanban/card/<int:card_id>/edit', methods=['POST'])
@login_required
def edit_kanban_card(card_id):
    card = KanbanCard.query.get_or_404(card_id)
    
    # Verificar se o card pertence à empresa do usuário
    if card.column.kanban.company_id != current_user.company_id:
        abort(403)
    
    card.title = request.form.get('title', card.title)
    card.description = request.form.get('description', card.description)
    card.o_que_fazer = request.form.get('o_que_fazer', card.o_que_fazer)
    card.onde_fazer = request.form.get('onde_fazer', card.onde_fazer)
    card.quem_fazer_id = request.form.get('quem_fazer_id') or None
    card.setor_id = request.form.get('setor_id') or None
    card.gravidade = int(request.form.get('gravidade', card.gravidade))
    card.urgencia = int(request.form.get('urgencia', card.urgencia))
    card.tendencia = int(request.form.get('tendencia', card.tendencia))
    
    # Prazo
    prazo_str = request.form.get('prazo')
    if prazo_str:
        try:
            card.prazo = datetime.fromisoformat(prazo_str)
        except ValueError:
            card.prazo = datetime.strptime(prazo_str, '%Y-%m-%d')
    else:
        card.prazo = None
    
    db.session.commit()
    
    flash('Card atualizado com sucesso!', 'success')
    register_log(f"Editou card: {card.title}")
    return redirect(url_for('app_bp.client_demands'))

@bp.route('/client/kanban/card/<int:card_id>/delete', methods=['POST'])
@login_required
def delete_kanban_card(card_id):
    card = KanbanCard.query.get_or_404(card_id)
    
    if card.column.kanban.company_id != current_user.company_id:
        abort(403)
    
    db.session.delete(card)
    db.session.commit()
    
    flash('Card deletado com sucesso!', 'success')
    register_log(f"Deletou card: {card.title}")
    return redirect(url_for('app_bp.client_demands'))

@bp.route('/client/kanban/card/<int:card_id>/move', methods=['POST'])
@login_required
def move_kanban_card(card_id):
    card = KanbanCard.query.get_or_404(card_id)
    
    if card.column.kanban.company_id != current_user.company_id:
        abort(403)
    
    new_column_id = request.json.get('column_id')
    new_position = request.json.get('position', 0)
    
    new_column = KanbanColumn.query.get_or_404(new_column_id)
    
    if new_column.kanban.id != card.column.kanban.id:
        abort(400, 'Cannot move card to different kanban board')
    
    # Atualizar posições dos outros cards na coluna original
    if card.column_id != new_column_id:
        cards_in_old_column = KanbanCard.query.filter_by(column_id=card.column_id).filter(KanbanCard.position > card.position).all()
        for c in cards_in_old_column:
            c.position -= 1
    
    # Atualizar posições dos cards na nova coluna
    cards_in_new_column = KanbanCard.query.filter_by(column_id=new_column_id).filter(KanbanCard.position >= new_position).all()
    for c in cards_in_new_column:
        c.position += 1
    
    card.column_id = new_column_id
    card.position = new_position
    
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/client/kanban/columns/<int:column_id>/reorder', methods=['POST'])
@login_required
def reorder_kanban_cards(column_id):
    column = KanbanColumn.query.get_or_404(column_id)
    
    if column.kanban.company_id != current_user.company_id:
        abort(403)
    
    card_order = request.json.get('card_order', [])
    
    for index, card_id in enumerate(card_order):
        card = KanbanCard.query.get(card_id)
        if card and card.column_id == column_id:
            card.position = index
    
    db.session.commit()
    
    return jsonify({'success': True})

# Página para eventos
@bp.route('/client/events')
@login_required
def client_events():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
            abort(403)
    events = Event.query.filter_by(company_id=current_user.company_id).all()
    register_log("Acesso: cliente_adm - events")
    return render_template('client/events_list.html', events=events)

@bp.route('/client/calendar')
@login_required
def client_calendar():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        abort(403)
    
    events = Event.query.filter_by(company_id=current_user.company_id).order_by(Event.start_at.asc()).all()
    collaborators = Collaborator.query.filter_by(company_id=current_user.company_id).all()
    sectors = Sector.query.filter_by(company_id=current_user.company_id).all()
    
    register_log("Acesso: cliente_adm - calendar")
    return render_template('client/calendar.html', 
                         events=events,
                         collaborators=collaborators,
                         sectors=sectors)

# ROTAS API PARA CRUD
@bp.route('/api/events', methods=['POST'])
@login_required
def create_event():
    if not current_user.is_cliente_adm() and not current_user.is_admin():
        return jsonify({'error': 'Não autorizado'}), 403
    
    data = request.get_json()
    
    event = Event(
        company_id=current_user.company_id,
        title=data['title'],
        description=data.get('description'),
        start_at=datetime.fromisoformat(data['start_at']),
        end_at=datetime.fromisoformat(data['end_at']) if data.get('end_at') else None,
        responsavel_id=data.get('responsavel_id'),
        setor_id=data.get('setor_id'),
        cor=data.get('cor', '#3b82f6'),
        tipo=data.get('tipo', 'evento')
    )
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'success': True, 'event': {
        'id': event.id,
        'title': event.title,
        'start': event.start_at.isoformat(),
        'end': event.end_at.isoformat() if event.end_at else None,
        'color': event.cor
    }})

@bp.route('/api/events/<int:event_id>', methods=['PUT'])
@login_required
def update_event(event_id):
    event = Event.query.filter_by(id=event_id, company_id=current_user.company_id).first_or_404()
    
    data = request.get_json()
    event.title = data['title']
    event.description = data.get('description')
    event.start_at = datetime.fromisoformat(data['start_at'])
    event.end_at = datetime.fromisoformat(data['end_at']) if data.get('end_at') else None
    event.responsavel_id = data.get('responsavel_id')
    event.setor_id = data.get('setor_id')
    event.cor = data.get('cor', event.cor)
    
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/api/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    event = Event.query.filter_by(id=event_id, company_id=current_user.company_id).first_or_404()
    
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({'success': True})

# Página para organizar demandas profissionais
@bp.route('/my-demands')
@login_required
def my_demands():
    """Painel individual onde usuário vê apenas demandas relacionadas a ele"""
    
    # Buscar quadros kanban da empresa do usuário
    kanban_boards = DemandKanban.query.filter_by(company_id=current_user.company_id).all()
    
    # Para cada quadro, filtrar apenas cards onde o usuário está envolvido
    filtered_boards = []
    for board in kanban_boards:
        # Criar uma cópia "filtrada" do quadro
        filtered_board = {
            'id': board.id,
            'name': board.name,
            'description': board.description,
            'columns': []
        }
        
        for column in sorted(board.columns, key=lambda c: c.position):
            # Filtrar cards: onde o usuário é responsável OU criador
            filtered_cards = []
            for card in column.cards:
                # Verificar se o usuário está envolvido no card
                is_responsible = (card.quem_fazer_id and 
                                 card.responsavel and 
                                 card.responsavel.user_id == current_user.id)
                is_creator = (card.created_by == current_user.id)
                
                if is_responsible or is_creator:
                    # Converter o card para dicionário serializável
                    card_dict = {
                        'id': card.id,
                        'title': card.title,
                        'description': card.description,
                        'o_que_fazer': card.o_que_fazer,
                        'onde_fazer': card.onde_fazer,
                        'prazo': card.prazo.isoformat() if card.prazo else None,
                        'gravidade': card.gravidade,
                        'urgencia': card.urgencia,
                        'tendencia': card.tendencia,
                        'position': card.position,
                        'created_by': card.created_by,
                        'created_at': card.created_at.isoformat(),
                        'column_id': column.id
                    }
                    
                    # Adicionar informações do responsável se existir
                    if card.responsavel:
                        card_dict['responsavel'] = {
                            'id': card.responsavel.id,
                            'name': card.responsavel.name,
                            'user_id': card.responsavel.user_id
                        }
                    else:
                        card_dict['responsavel'] = None
                    
                    # Adicionar informações do setor se existir
                    if card.setor:
                        card_dict['setor'] = {
                            'id': card.setor.id,
                            'name': card.setor.name
                        }
                    else:
                        card_dict['setor'] = None
                    
                    # Adicionar informações do criador
                    card_dict['criador'] = {
                        'id': card.criador.id,
                        'name': card.criador.name
                    }
                    
                    filtered_cards.append(card_dict)
            
            if filtered_cards:  # Só incluir coluna se tiver cards relevantes
                filtered_column = {
                    'id': column.id,
                    'name': column.name,
                    'color': column.color,
                    'position': column.position,
                    'cards': filtered_cards
                }
                filtered_board['columns'].append(filtered_column)
        
        if filtered_board['columns']:  # Só incluir quadro se tiver colunas com cards
            filtered_boards.append(filtered_board)
    
    collaborators = Collaborator.query.filter_by(company_id=current_user.company_id).all()
    sectors = Sector.query.filter_by(company_id=current_user.company_id).all()

    # Converter collaborators e sectors para dados serializáveis
    collaborators_data = [
        {"id": c.id, "name": c.name, "user_id": c.user_id} 
        for c in collaborators
    ]
    sectors_data = [
        {"id": s.id, "name": s.name} 
        for s in sectors
    ]

    register_log("Acesso: visão individual de demandas")
    return render_template('client/my_demands.html', 
                         kanban_boards=filtered_boards,
                         collaborators=collaborators_data,
                         sectors=sectors_data)

# Página de demandas pessoais
@bp.route("/client/personal-demands")
@login_required
def personal_demands():
    if not current_user.is_cliente_adm() and not current_user.is_admin() and not current_user.is_cliente():
            abort(403)
    demands = PersonalDemand.query.filter_by(owner_id=current_user.id).all()
    register_log("Acesso: demandas pessoais")
    return render_template("client/personal_demands.html", demands=demands)

@bp.route("/client/personal-demands/new", methods=["GET", "POST"])
@login_required
def personal_demands_new():
    orgs = Organization.query.filter_by(owner_id=current_user.id).all()

    if request.method == "POST":
        title = request.form["title"]
        desc = request.form.get("description")
        status = request.form.get("status") or "Pendente"
        org_id = request.form.get("organization_id")

        demand = PersonalDemand(
            title=title,
            description=desc,
            status=status,
            owner_id=current_user.id,
            organization_id=int(org_id) if org_id else None
        )
        db.session.add(demand)
        db.session.commit()
        flash("Demanda criada com sucesso!", "success")
        register_log("Demanda nova criada pelo usuário em ambito pessoal")
        return redirect(url_for("app_bp.personal_demands"))

    return render_template(
        "client/personal_demands_form.html",
        organizations=orgs,
        demand=None
    )

@bp.route("/client/personal-demands/<int:id>/delete", methods=["GET", "POST"])
@login_required
def personal_demands_delete(id):
    demand = PersonalDemand.query.get_or_404(id)
    if demand.owner_id != current_user.id:
        abort(403)
    db.session.delete(demand)
    db.session.commit()
    flash("Demanda removida!", "success")
    register_log("Demanda pessoal removida")
    return redirect(url_for("app_bp.personal_demands"))

@bp.route("/client/leisure")
@login_required
def leisure_list():
    leisures = Leisure.query.filter_by(owner_id=current_user.id).all()
    register_log("Lazer na parte de demanda pessoal acessada")
    return render_template("client/leisure.html", leisures=leisures)

@bp.route("/client/leisure/new", methods=["GET", "POST"])
@login_required
def leisure_new():
    orgs = Organization.query.filter_by(owner_id=current_user.id).all()

    if request.method == "POST":
        title = request.form["title"]
        desc = request.form.get("description")

        leisure = Leisure(
            name=title,
            description=desc,
            owner_id=current_user.id
        )
        db.session.add(leisure)
        db.session.commit()
        flash("Atividade de lazer criada!", "success")
        register_log("Nova atividade de lazer criada")
        return redirect(url_for("app_bp.leisure_list"))

    return render_template("client/leisure_form.html", organizations=orgs)

@bp.route("/client/organizations")
@login_required
def organizations_list():
    orgs = Organization.query.filter_by(owner_id=current_user.id).all()
    register_log("Parte de organizações da demanda pessoal acessada")
    return render_template("client/organizations.html", organizations=orgs)

@bp.route("/client/organizations/new", methods=["GET", "POST"])
@login_required
def organizations_new():
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form.get("description")

        org = Organization(
            name=title,
            description=desc,
            owner_id=current_user.id
        )
        db.session.add(org)
        db.session.commit()
        flash("Organização criada com sucesso!", "success")
        register_log("Organização de demanda pessoal criada com sucesso")
        return redirect(url_for("app_bp.organizations_list"))

    return render_template("client/organizations_form.html")


@bp.route("/client/organizations/<int:id>/delete", methods=["POST"])
@login_required
def organizations_delete(id):
    org = Organization.query.get_or_404(id)
    if org.owner_id != current_user.id:
        abort(403)
    db.session.delete(org)
    db.session.commit()
    flash("Organização removida!", "success")
    register_log("Organização removida")
    return redirect(url_for("app_bp.organizations_list"))
