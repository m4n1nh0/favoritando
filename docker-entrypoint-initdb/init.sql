-- docker-entrypoint-initdb/init.sql

-- Criação da tabela clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Criação da tabela usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    perfil VARCHAR(50) NOT NULL DEFAULT 'cliente',
    cliente_id INTEGER UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT fk_cliente
        FOREIGN KEY(cliente_id)
        REFERENCES clientes(id)
        ON DELETE CASCADE
);

-- Criação da tabela favoritos
CREATE TABLE IF NOT EXISTS favoritos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    imagem VARCHAR(255) NOT NULL,
    preco NUMERIC(10, 2) NOT NULL,
    review TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT fk_cliente_favoritos
        FOREIGN KEY(cliente_id)
        REFERENCES clientes(id)
        ON DELETE CASCADE,
    CONSTRAINT unique_cliente_produto UNIQUE (cliente_id, produto_id)
);

-- Inserção de um usuário admin padrão (senha 'favorito@123')
INSERT INTO usuarios (email, hashed_password, perfil)
VALUES ('admin@aiqfome.com', '$2b$12$Wekol57XnnS2B1zCqwydx.geHdFBLvuBQTzg0KfIcFg53napGs10S', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Inserção de clientes e seus usuários associados
INSERT INTO clientes (nome, email) VALUES ('Ana Souza', 'ana.souza@example.com') ON CONFLICT (email) DO NOTHING;
INSERT INTO clientes (nome, email) VALUES ('Bruno Costa', 'bruno.costa@example.com') ON CONFLICT (email) DO NOTHING;
INSERT INTO clientes (nome, email) VALUES ('Carla Lima', 'carla.lima@example.com') ON CONFLICT (email) DO NOTHING;
INSERT INTO clientes (nome, email) VALUES ('Daniel Martins', 'daniel.martins@example.com') ON CONFLICT (email) DO NOTHING;
INSERT INTO clientes (nome, email) VALUES ('Elisa Rocha', 'elisa.rocha@example.com') ON CONFLICT (email) DO NOTHING;

-- Inserção de usuários normais associados aos clientes criados
-- O ID do cliente é recuperado via subquery
-- A senha é o primeiro nome @123 ex: ana@123
INSERT INTO usuarios (email, hashed_password, perfil, cliente_id)
SELECT
    'ana.souza@example.com',
    '$2b$12$9s2RquqMOAXaLdEyegWzD.4XzUDkJEqQPjK.ou2/MUFhUNMCHC0C6',
    'cliente',
    (SELECT id FROM clientes WHERE email = 'ana.souza@example.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, hashed_password, perfil, cliente_id)
SELECT
    'bruno.costa@example.com',
    '$2b$12$rfdE4F1jbr8Kzs5J..qt8uA6yS/DUwLkgZ6Y.ElpL53Hu.dyYAeZ.',
    'cliente',
    (SELECT id FROM clientes WHERE email = 'bruno.costa@example.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, hashed_password, perfil, cliente_id)
SELECT
    'carla.lima@example.com',
    '$2b$12$FXdKmPPEmyO8idHHYIcjmuerQzpgev3NC50BWxMguC7hGcqlHn.b2',
    'cliente',
    (SELECT id FROM clientes WHERE email = 'carla.lima@example.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, hashed_password, perfil, cliente_id)
SELECT
    'daniel.martins@example.com',
    '$2b$12$Q5VDSD000WCfEkwtxk.LKOxmscCk7/08yLE41evI74Zt8mhqMxlMe',
    'cliente',
    (SELECT id FROM clientes WHERE email = 'daniel.martins@example.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, hashed_password, perfil, cliente_id)
SELECT
    'elisa.rocha@example.com',
    '$2b$12$WOgAKBCcjvVJsufNE1aaE.t5Q.8a43QLZl7ct5vcCrTXAKsFDUj5C',
    'cliente',
    (SELECT id FROM clientes WHERE email = 'elisa.rocha@example.com')
ON CONFLICT (email) DO NOTHING;
