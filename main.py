import json
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///checklist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Modelo de usuário
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Modelo de checklist atualizado
class Checklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    nome_checklist = db.Column(db.String(200), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    responsavel = db.Column(db.String(150), nullable=False)
    data_inspecao = db.Column(db.Date, nullable=True)
    hora_inspecao = db.Column(db.String(10), nullable=True)
    observacoes = db.Column(db.Text)
    itens_verificados = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='checklists')


class TipoInspecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
    ativo = db.Column(db.Boolean, default=True)


class SubitemInspecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo_inspecao.id'))
    descricao = db.Column(db.String(200), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    tipo = db.relationship('TipoInspecao',
                           backref=db.backref('subitens', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user')
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe!')
            return redirect(url_for('register'))
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login realizado com sucesso!')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas.')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout efetuado com sucesso!')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        checklists = Checklist.query.all()
    else:
        checklists = Checklist.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', checklists=checklists)


@app.route('/novo_checklist', methods=['GET', 'POST'])
@login_required
def novo_checklist():
    # 1) Busca tipos de inspeção ativos
    tipos = TipoInspecao.query.filter_by(ativo=True).all()
    tipos_subitens = {
        str(tipo.id): [sub.descricao for sub in tipo.subitens if sub.ativo]
        for tipo in tipos
    }

    if request.method == 'POST':
        # 2) Lê campos principais
        titulo = request.form.get('titulo', '').strip()
        nome_checklist = request.form.get('nome_checklist', '').strip()
        responsavel = request.form.get('responsavel', '').strip()
        data_inspecao = request.form.get('data_inspecao')
        hora_inspecao = request.form.get('hora_inspecao', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        tipo_id = request.form.get('tipo_inspecao')

        # 3) Monta a lista de subitens com status e observação
        raw_list = tipos_subitens.get(tipo_id, [])
        itens = []
        for idx, descricao in enumerate(raw_list):
            status = request.form.get(f'status_{idx}', 'Não verificado')
            obs = request.form.get(f'obs_{idx}', '').strip()
            itens.append({
                'sub_item': descricao,
                'status': status,
                'observacao': obs
            })

        # 4) Envolve itens em um dicionário para manter compatibilidade
        payload = {'subitens': itens}

        # 5) Cria e persiste o Checklist
        checklist = Checklist(
            titulo=titulo,
            nome_checklist=nome_checklist,
            responsavel=responsavel,
            data_inspecao=(datetime.strptime(data_inspecao, '%Y-%m-%d')
                           if data_inspecao else None),
            hora_inspecao=hora_inspecao,
            observacoes=observacoes,
            itens_verificados=json.dumps(payload),
            user_id=current_user.id)
        db.session.add(checklist)
        db.session.commit()
        flash('Checklist criado com sucesso!')
        return redirect(url_for('dashboard'))

    # 6) GET: renderiza o formulário
    return render_template('novo_checklist.html',
                           tipos=tipos,
                           tipos_subitens=tipos_subitens)


@app.route('/checklist/<int:checklist_id>')
@login_required
def visualizar_checklist(checklist_id):
    checklist = Checklist.query.get_or_404(checklist_id)
    if current_user.role != 'admin' and checklist.user_id != current_user.id:
        flash('Você não tem permissão para visualizar este checklist.')
        return redirect(url_for('dashboard'))
    try:
        dados = json.loads(checklist.itens_verificados)
    except Exception:
        dados = {}
    return render_template('visualizar_checklist.html',
                           checklist=checklist,
                           dados=dados)


@app.route('/admin/tipos', methods=['GET', 'POST'])
@login_required
def gerenciar_tipos():
    if current_user.role != 'admin':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        nome = request.form['nome']
        novo_tipo = TipoInspecao(nome=nome)
        db.session.add(novo_tipo)
        db.session.commit()
        flash('Tipo de inspeção adicionado!')
        return redirect(url_for('gerenciar_tipos'))
    tipos = TipoInspecao.query.all()
    return render_template('admin_tipos.html', tipos=tipos)


@app.route('/admin/subitens', methods=['GET', 'POST'])
@login_required
def gerenciar_subitens():
    if current_user.role != 'admin':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))
    tipos = TipoInspecao.query.all()
    if request.method == 'POST':
        descricao = request.form['descricao']
        tipo_id = request.form['tipo_id']
        novo_subitem = SubitemInspecao(descricao=descricao, tipo_id=tipo_id)
        db.session.add(novo_subitem)
        db.session.commit()
        flash('Subitem adicionado!')
        return redirect(url_for('gerenciar_subitens'))
    subitens = SubitemInspecao.query.all()
    return render_template('admin_subitens.html',
                           subitens=subitens,
                           tipos=tipos)


@app.route('/admin/tipos/delete/<int:id>')
@login_required
def deletar_tipo(id):
    if current_user.role != 'admin':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))
    tipo = TipoInspecao.query.get_or_404(id)
    db.session.delete(tipo)
    db.session.commit()
    flash('Tipo de inspeção removido.')
    return redirect(url_for('gerenciar_tipos'))


@app.route('/admin/subitens/delete/<int:id>')
@login_required
def deletar_subitem(id):
    if current_user.role != 'admin':
        flash('Acesso negado.')
        return redirect(url_for('dashboard'))
    subitem = SubitemInspecao.query.get_or_404(id)
    db.session.delete(subitem)
    db.session.commit()
    flash('Subitem removido.')
    return redirect(url_for('gerenciar_subitens'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
