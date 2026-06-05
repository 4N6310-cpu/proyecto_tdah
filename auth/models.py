class Terapeuta:
    def __init__(self, id, username, nombre, especialidad, email, password_hash):
        self.id = id
        self.username = username
        self.nombre = nombre
        self.especialidad = especialidad
        self.email = email
        self.password_hash = password_hash

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return Terapeuta(
            id=data["id"],
            username=data["username"],
            nombre=data["nombre"],
            especialidad=data["especialidad"],
            email=data["email"],
            password_hash=data["password_hash"]
        )
