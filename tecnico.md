from app import db
from app.models import User  # ajuste o caminho se necessário

# Cria o usuário root
admin = User(
    username="suporte_organiums",
    name="Administrador Suporte",
    email="suporte@organiums.com",
    role="admin"
)

# Define a senha
admin.set_password("MinhaSenhaForte123")  # 🔑 troque por uma senha que você saiba

# Salva no banco
db.session.add(admin)
db.session.commit()
