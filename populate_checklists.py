# populate_checklists.py

import random
import json
from datetime import datetime, timedelta
from main import app, db, TipoInspecao, SubitemInspecao, Checklist, User

STATUS_OPTIONS = ['Ok', 'Não Ok', 'Não verificado']
OBS_SAMPLES = [
    'Tudo em ordem', 'Necessita atenção', 'Verificar posteriormente',
    'Substituir componente'
]


def popular_checklists(qtd=5):
    with app.app_context():
        user = User.query.first()
        if not user:
            print(
                "Nenhum usuário encontrado. Crie ao menos um usuário antes de popular checklists."
            )
            return

        tipos = TipoInspecao.query.filter_by(ativo=True).all()
        if not tipos:
            print("Nenhum tipo de inspeção ativo. Popule tipos primeiro.")
            return

        for i in range(qtd):
            tipo = random.choice(tipos)
            subitens_obj = SubitemInspecao.query.filter_by(tipo_id=tipo.id,
                                                           ativo=True).all()
            print(
                f"🔎 Tipo selecionado: {tipo.nome} — {len(subitens_obj)} subitens encontrados"
            )

            if not subitens_obj:
                print(
                    f"⚠️  Nenhum subitem ativo para o tipo '{tipo.nome}', pulando..."
                )
                continue

            itens_raw = []
            for sub in subitens_obj:
                itens_raw.append({
                    'sub_item': sub.descricao,
                    'status': random.choice(STATUS_OPTIONS),
                    'observacao': random.choice(OBS_SAMPLES)
                })

            payload = {'subitens': itens_raw}
            titulo = f"Checklist {tipo.nome} #{i+1}"
            nome_checklist = f"Inspeção {tipo.nome}"
            responsavel = user.username
            data_inspecao = (datetime.utcnow() -
                             timedelta(days=random.randint(0, 10))).date()
            hora_inspecao = f"{random.randint(7, 17):02d}:{random.choice([0, 15, 30, 45]):02d}"
            observacoes = random.choice(OBS_SAMPLES)

            checklist = Checklist(titulo=titulo,
                                  nome_checklist=nome_checklist,
                                  responsavel=responsavel,
                                  data_inspecao=data_inspecao,
                                  hora_inspecao=hora_inspecao,
                                  observacoes=observacoes,
                                  itens_verificados=json.dumps(payload),
                                  user_id=user.id)
            db.session.add(checklist)
            db.session.commit()
            print(f"✔️ Checklist criado: {titulo}")

        print("\n✅ População de checklists concluída.")


if __name__ == '__main__':
    popular_checklists(qtd=3)
