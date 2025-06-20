from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def obter_hash_senha(senha: str) -> str:
    """
    Cria um hash bcrypt de uma senha.

    Args:
        senha (str): A senha em texto puro a ser hasheada.

    Returns:
        str: O hash bcrypt da senha.
    """
    return pwd_context.hash(senha)


senha_do_usuario = "favorito@123"

hash_da_senha_para_db = obter_hash_senha(senha_do_usuario)
print(f"Senha original: '{senha_do_usuario}'")
print(f"Hash gerado (para armazenar no DB): '{hash_da_senha_para_db}'")

clientes_data = [
    {"nome": "Ana Souza", "email": "ana.souza@example.com"},
    {"nome": "Bruno Costa", "email": "bruno.costa@example.com"},
    {"nome": "Carla Lima", "email": "carla.lima@example.com"},
    {"nome": "Daniel Martins", "email": "daniel.martins@example.com"},
    {"nome": "Elisa Rocha", "email": "elisa.rocha@example.com"},
]

inserts_clientes = []
inserts_usuarios = []

for cliente in clientes_data:
    primeiro_nome = cliente["nome"].split(" ")[0].lower()
    senha_clara = f"{primeiro_nome}@123"
    senha_hash = obter_hash_senha(senha_clara)

    inserts_clientes.append(f"INSERT INTO clientes (nome, email) VALUES ('{cliente['nome']}"
                            f"', '{cliente['email']}') ON CONFLICT (email) DO NOTHING;")

    inserts_usuarios.append({
        "email": cliente["email"],
        "hashed_password": senha_hash,
        "nome_cliente": cliente["nome"]
    })

print("\n--- INSERTS PARA TABELA CLIENTES (SQL) ---")
for insert_sql in inserts_clientes:
    print(insert_sql)

print("\n--- DADOS PARA INSERTS DE USUARIOS (Para construir o SQL com JOIN) ---")
for usuario_info in inserts_usuarios:
    print(f"Email: {usuario_info['email']}, Senha Hash: {usuario_info['hashed_password']}")
