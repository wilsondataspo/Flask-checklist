# admin_creator.py

import argparse
from main import app, db, User
#from main import User  # Ajuste a importação conforme a estrutura do seu projeto


def criar_admin(username, senha):
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f'Usuário {username} já existe.')
            return
        admin = User(username=username, role='admin')
        admin.set_password(senha)
        db.session.add(admin)
        db.session.commit()
        print(f'Usuário {username} criado com perfil de admin.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Cria um usuário administrador.")
    parser.add_argument('--username', required=True, help="Nome do usuário")
    parser.add_argument('--password', required=True, help="Senha do usuário")
    args = parser.parse_args()

    criar_admin(args.username, args.password)
