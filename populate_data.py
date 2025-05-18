# populate_data.py

import random
from main import app, db
from main import TipoInspecao, SubitemInspecao


def popular_dados(qtd_tipos=5, qtd_subitens=5):
    nomes_tipos = [
        "Elétrica Geral", "Manutenção de Elevadores", "Geradores de Energia",
        "Infraestrutura de Rede", "Segurança Contra Incêndio"
    ]
    # Se tiver menos de qtd_tipos pré-definidos, completa com nomes genéricos
    while len(nomes_tipos) < qtd_tipos:
        idx = len(nomes_tipos) + 1
        nomes_tipos.append(f"Tipo Aleatório {idx}")

    with app.app_context():
        for i in range(qtd_tipos):
            nome_tipo = nomes_tipos[i]
            # Verifica se já existe para não duplicar
            tipo = TipoInspecao.query.filter_by(nome=nome_tipo).first()
            if not tipo:
                tipo = TipoInspecao(nome=nome_tipo, ativo=True)
                db.session.add(tipo)
                db.session.commit()
                print(f"✔️ Criado TipoInspecao: {nome_tipo}")
            else:
                print(f"🔄 TipoInspecao já existe: {nome_tipo}")

            # Cria subitens para este tipo
            existentes = {s.descricao for s in tipo.subitens}
            for j in range(1, qtd_subitens + 1):
                desc = f"{nome_tipo} – Subitem {j}"
                if desc not in existentes:
                    sub = SubitemInspecao(tipo_id=tipo.id,
                                          descricao=desc,
                                          ativo=True)
                    db.session.add(sub)
                    print(f"   • Adicionado Subitem: {desc}")
                else:
                    print(f"   • Subitem já existe: {desc}")
            db.session.commit()

        print("\n✅ População concluída.")


if __name__ == "__main__":
    # Você pode ajustar os números abaixo, se quiser mais ou menos registros
    popular_dados(qtd_tipos=3, qtd_subitens=2)
