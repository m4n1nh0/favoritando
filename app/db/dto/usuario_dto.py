from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.models.usuario_model import Usuario


class UsuarioDTO:
    def __init__(self, db: Session):
        """
        Inicializa o DTO (Data Transfer Object) responsável pelas operações
        relacionadas à entidade Usuario no banco de dados.

        :param db: Sessão ativa do SQLAlchemy.
        """
        self.db = db
        self.logger = logger

    def pegar_por_email(self, email: str) -> Usuario | None:
        """
        Busca usuário por e-mail.

        :param email: E-mail do usuário.
        :return: Objeto Usuario se encontrado, ou None.
        """
        self.logger.debug(f"Obtendo usuario por e-mail: {email}")
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def usuario_por_id(self, usuario_id: int) -> Usuario | None:
        """
        Busca usuário por ID.

        :param usuario_id: ID do usuário.
        :return: Objeto Usuario se encontrado, ou None.
        """
        self.logger.debug(f"Obtendo usuario por ID: {usuario_id}")
        return self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def pegar_por_cliente_id(self, cliente_id: int) -> Usuario | None:
        """
        Recupera usuário por um cliente específico.

        :param cliente_id: ID do cliente.
        :return: Objeto Usuario vinculado ao cliente, ou None.
        """
        self.logger.debug(f"Obtendo usuario por ID do cliente: {cliente_id}")
        return self.db.query(Usuario).filter(
            Usuario.cliente_id == cliente_id).first()

    def registrar(self, usuario_data: dict) -> Usuario:
        """
        Registra usuário no banco de dados.

        :param usuario_data: Dicionário com os dados do novo usuário.
        :return: Objeto Usuario criado.
        :raises Exception: Em caso de erro durante o registro.
        """
        self.logger.info(f"Criando novo usuario com email: "
                         f"{usuario_data.get('email')}")
        try:
            db_user = Usuario(**usuario_data)
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            self.logger.info(f"Usuario criado com sucesso com ID: "
                             f"{db_user.id}")
            return db_user
        except Exception as e:
            self.logger.error(f"Erro ao criar usuário: {e}", exc_info=True)
            raise

    def deletar(self, usuario: Usuario) -> None:
        """
        Exclui usuário do banco de dados.

        :param usuario: Objeto Usuario a ser removido.
        :return: None.
        :raises Exception: Em caso de falha na exclusão.
        """
        self.logger.info(f"Excluindo usuario com ID: {usuario.id}")
        try:
            self.db.delete(usuario)
            self.db.commit()
            self.logger.info(f"Usuario excluido com sucesso: {usuario.id}")
        except Exception as e:
            self.logger.error(f"Erro ao excluir o ID do usuário "
                              f"{usuario.id}: {e}", exc_info=True)
            raise

    def aualizacao(self, db_usuario: Usuario, update_data: dict) -> Usuario:
        """
        Atualiza os dados de usuário existente.

        :param db_usuario: Objeto Usuario atual.
        :param update_data: Dicionário com os campos e valores a serem atualizados.
        :return: Objeto Usuario atualizado.
        :raises Exception: Em caso de falha na atualização.
        """
        self.logger.info(f"Atualizando usuario com ID: {db_usuario.id}")
        try:
            for key, value in update_data.items():
                setattr(db_usuario, key, value)
            self.db.add(db_usuario)
            self.db.commit()
            self.db.refresh(db_usuario)
            self.logger.info(f"Usuario atualizado com sucesso: "
                             f"{db_usuario.id}")
            return db_usuario
        except Exception as e:
            self.logger.error(f"Erro ao atualizar o ID do usuário "
                              f"{db_usuario.id}: {e}", exc_info=True)
            raise
